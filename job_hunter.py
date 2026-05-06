"""
AI Job Hunter v3 — Marc Planas
Scans working job APIs daily, scores with Claude AI, researches companies, logs to tracker.
"""

import os
import json
import csv
import hashlib
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from marc_profile import PROFILE

# ── Environment ──────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

SEEN_FILE    = "seen_jobs.json"
TRACKER_FILE = "job_tracker.csv"
TODAY        = datetime.now().strftime("%Y-%m-%d")
HEADERS      = {"User-Agent": "Mozilla/5.0 (compatible; InsurtechJobHunter/2.0)"}

# ── EU cities for location matching ──────────────────────────
EU_CITIES = [
    "barcelona", "madrid", "paris", "london", "dublin", "amsterdam",
    "berlin", "munich", "frankfurt", "zurich", "vienna", "milan",
    "brussels", "lisbon", "stockholm", "copenhagen", "warsaw", "prague",
]

EU_REMOTE_KEYWORDS = [
    "remote", "fully remote", "remote eu", "remote europe", "remote emea",
    "work from anywhere", "wfa", "distributed",
]

# Hard-reject patterns for US-only roles
US_ONLY_PATTERNS = [
    "united states only", "us only", "usa only", "us-only",
    "remote (us)", "remote - us", "remote, us", "remote us only",
    "must be authorized to work in the us",
    "must be legally authorized to work in the united states",
    "authorized to work in the us",
    "right to work in the us",
]

# ═════════════════════════════════════════════════════════════
# COMPANY WATCHLIST — Sorted by relevance to Marc's profile
# ═════════════════════════════════════════════════════════════

# Ashby ATS companies
ASHBY_COMPANIES = [
    # Traditional InsurTech (domain-focused)
    {"name": "Descartes Underwriting", "client": "descartesunderwriting"},
    {"name": "Cytora",                 "client": "cytora"},
    {"name": "Artificial Labs",        "client": "artificial"},
    {"name": "wefox",                  "client": "wefox"},
    {"name": "Alan",                   "client": "alan"},
    {"name": "Kota",                   "client": "kota"},
    {"name": "Inaza",                  "client": "inaza"},
    {"name": "Marshmallow",            "client": "marshmallow"},
    {"name": "Zego",                   "client": "zego"},
    {"name": "Lassie",                 "client": "lassie"},
    {"name": "YuLife",                 "client": "yulife"},
    # AI-focused InsurTech and automation platforms
    {"name": "Embat",                  "client": "embat"},
    {"name": "Shift Technology",       "client": "shifttechnology"},
    # Additional EU InsurTech/FinTech (Ashby)
    {"name": "Hiscox",                 "client": "hiscox"},
    {"name": "Bought By Many",         "client": "boughtbymany"},
    {"name": "Cuvva",                  "client": "cuvva"},
    {"name": "Nimbla",                 "client": "nimbla"},
    {"name": "Optalitix",              "client": "optalitix"},
    {"name": "Drivit",                 "client": "drivit"},
    {"name": "Qover",                  "client": "qover"},
    {"name": "InMyBag",                "client": "inmybag"},
]

# Greenhouse ATS companies
GREENHOUSE_COMPANIES = [
    {"name": "Shift Technology",   "client": "shifttechnology"},
    {"name": "Guidewire",          "client": "guidewire"},
    {"name": "Duck Creek",         "client": "duckcreek"},
    {"name": "FINEOS",             "client": "fineos"},
    {"name": "CoverGo",            "client": "covergo"},
    {"name": "Hokodo",             "client": "hokodo"},
    {"name": "Concirrus",          "client": "concirrus"},
    {"name": "Coalition",          "client": "coalitioninc"},
    {"name": "At-Bay",             "client": "atbay"},
]

# Lever ATS companies
LEVER_COMPANIES = [
    {"name": "Wakam",        "client": "wakam"},
    {"name": "Prima",        "client": "prima"},
    {"name": "Superscript",  "client": "superscript"},
    {"name": "Laka",         "client": "laka"},
    {"name": "Flock",        "client": "flock"},
    {"name": "Embroker",     "client": "embroker"},
]

# Direct career page checks (companies without standard ATS APIs)
CAREER_PAGES = [
    {"name": "Accelerant",         "url": "https://accelerant.ai/careers/"},
    {"name": "Ledgebrook",         "url": "https://www.ledgebrook.com/careers"},
    {"name": "Swiss Re",           "url": "https://careers.swissre.com/search/?q=operations&locationsearch="},
    {"name": "Munich Re",          "url": "https://careers.munichre.com/en/munichre/search"},
    {"name": "Gen Re",             "url": "https://www.genre.com/us/careers"},
    {"name": "SCOR",               "url": "https://www.scor.com/en/careers"},
    {"name": "Hannover Re",        "url": "https://www.hannover-re.com/careers"},
    {"name": "Novidea",            "url": "https://www.novidea.com/careers"},
    {"name": "EIS Group",          "url": "https://eisgroup.com/careers"},
    {"name": "ELEMENT Insurance",  "url": "https://www.element.in/en/careers"},
    {"name": "Pie Insurance",      "url": "https://jobs.lever.co/pieinsurance"},
    {"name": "Embroker",           "url": "https://www.embroker.com/careers/"},
    {"name": "Coalition",          "url": "https://www.coalitioninc.com/careers"},
    {"name": "Counterpart",        "url": "https://www.counterpart.com/careers"},
]
# Add to CAREER_PAGES — consultancies and EU insurance-consulting firms
CAREER_PAGES += [
    {"name": "zeb", "url": "https://zeb-career.com/"},
    {"name": "Milliman (EMEA)", "url": "https://www.milliman.com/careers"},
    {"name": "Aon", "url": "https://www.aon.com/careers"},
    {"name": "Mazars", "url": "https://www.mazars.com/careers"},
    {"name": "Oliver Wyman", "url": "https://www.oliverwyman.com/careers"},
    {"name": "EY (Insurance Transformation)", "url": "https://www.ey.com/en_gl/careers"},
    {"name": "Roland Berger", "url": "https://www.rolandberger.com/en/Careers"},
    {"name": "Capgemini Invent", "url": "https://www.capgemini.com/careers"},
    {"name": "WTW", "url": "https://careers.wtwco.com/"},
    {"name": "KPMG (Insurance Advisory)", "url": "https://home.kpmg/careers"},
    {"name": "FTI Consulting (EMEA)", "url": "https://www.fticonsulting.com/careers"},
    {"name": "Synpulse", "url": "https://www.synpulse.com/careers/"},
    # AI/Automation InsurTech platforms
    {"name": "Embat", "url": "https://www.embat.com/careers"},
    {"name": "Shift Technology", "url": "https://www.shift-technology.com/careers"},
    {"name": "Concirrus (InsurTech AI)", "url": "https://www.concirrus.com/careers"},
]
# Remotive API — working JSON API for remote jobs
REMOTIVE_CATEGORIES = [
    "finance",
    "business",
    "all-others",
    "software-dev",  # For AI/automation engineer roles in finance/insurance
]

# RSS feeds that actually work
WORKING_RSS = [
    {"name": "Remotive Finance",     "url": "https://remotive.com/remote-jobs/finance/feed"},
    {"name": "Remotive Business",    "url": "https://remotive.com/remote-jobs/business/feed"},
    {"name": "We Work Remotely",     "url": "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss"},
    {"name": "Jobicy Finance",       "url": "https://jobicy.com/?feed=job_feed&job_category=finance&job_region=europe"},
    {"name": "Jobicy Operations",    "url": "https://jobicy.com/?feed=job_feed&job_category=business&job_region=europe"},
]

# Adzuna API — covers EU countries, keyword-based search, free public API
# Requires app_id + app_key (free at developer.adzuna.com — add as GitHub secrets)
ADZUNA_APP_ID  = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

ADZUNA_SEARCHES = [
    # Operations roles
    {"country": "gb", "keywords": "insurance operations manager remote"},
    {"country": "gb", "keywords": "underwriting operations remote"},
    {"country": "gb", "keywords": "insurtech operations remote"},
    # Business Analysis
    {"country": "gb", "keywords": "business analyst insurtech remote"},
    {"country": "gb", "keywords": "business analyst fintech remote"},
    # AI Product / Engineering
    {"country": "gb", "keywords": "AI product engineer insurance remote"},
    {"country": "gb", "keywords": "AI engineer finance insurance remote"},
    {"country": "gb", "keywords": "machine learning engineer insurance remote"},
    {"country": "gb", "keywords": "AI implementation specialist insurance"},
    {"country": "de", "keywords": "AI engineer insurance remote"},
    # EU country searches
    {"country": "de", "keywords": "insurance operations remote"},
    {"country": "fr", "keywords": "insurance operations remote"},
    {"country": "es", "keywords": "insurance operations remote"},
    {"country": "nl", "keywords": "insurance operations remote"},
]

# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════

def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r if r.status_code == 200 else None
    except Exception as e:
        print(f"    fetch error: {str(e)[:60]}")
        return None

def job_id(title, company):
    return hashlib.md5(f"{title}|{company}".lower().encode()).hexdigest()[:12]

def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()

def save_seen(seen):
    try:
        json.dump(list(seen), open(SEEN_FILE, "w"))
    except Exception as e:
        print(f"    save_seen error: {e}")

def is_insurance_relevant(text):
    """Check if job contains insurance/fintech domain OR AI + finance/insurance domain."""
    t = text.lower()

    # Traditional insurance/fintech keywords
    strong_insurance = ["insurance", "insurtech", "reinsurance", "underwriting", "mga",
                       "managing general", "coverholder", "lloyd's", "actuar", "claims",
                       "broker", "solvency", "dua", "delegated underwriting",
                       "fintech", "financial services", "insuretechdaily"]

    # Business analysis at insurance/fintech
    ba_insurance = ["business analyst", "process analyst", "operational analyst",
                    "digital transformation", "business analysis"]

    # AI/automation keywords (tool-specific + engineering roles)
    ai_automation = ["claude api", "langchain", "langgraph", "crewai",
                     "prompt engineer", "llm", "generative ai",
                     "ai agent", "ai implementation", "ai automation", "rag", "mcp",
                     "ai-powered", "ai-enabled", "ai engineer", "ai software engineer",
                     "machine learning engineer", "llm engineer", "ai solutions engineer",
                     "conversational ai", "ai platform", "ai developer"]

    # Domain context for AI roles (STRICT: insurance/finance specific)
    finance_insurance_domain = [
        "claims automation", "underwriting automation", "claims processing",
        "insurance automation", "operations ai", "fintech",
        "treasury operations", "finance operations", "financial automation",
        "insurance operations", "reinsurance", "policy management", "bordereaux",
        "financial services"
    ]

    has_insurance = any(kw in t for kw in strong_insurance)
    has_ba = any(kw in t for kw in ba_insurance)
    has_ai = any(kw in t for kw in ai_automation)
    has_finance_insurance = any(kw in t for kw in finance_insurance_domain)

    # Accept: traditional insurance/fintech (includes BA at those companies)
    # OR: BA keyword + insurance/fintech domain
    # OR: AI tools + finance/insurance domain
    return has_insurance or (has_ba and has_finance_insurance) or (has_ai and has_finance_insurance)

def is_eu_eligible(location_text, description_text=""):
    """Check if role is remote EU or Barcelona-based. Hard-rejects US-only roles."""
    loc = location_text.lower()
    desc = description_text.lower()
    combined = f"{loc} {desc}"

    # Hard-reject explicit US-only indicators
    if any(pat in combined for pat in US_ONLY_PATTERNS):
        return False, "us_only"

    # Fully remote (no US-only restriction detected above)
    if any(kw in combined for kw in EU_REMOTE_KEYWORDS):
        return True, "remote"
    # EU city
    if any(city in loc for city in EU_CITIES):
        return True, f"eu_city_{loc.strip()}"
    return False, "not_eu"

def log_to_tracker(job, ai_result):
    try:
        exists = os.path.exists(TRACKER_FILE)
        with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(["Date", "Title", "Company", "Source", "Score",
                            "Location", "Salary", "Reason", "Link", "Status"])
            w.writerow([
                TODAY, job.get("title", ""), job.get("company", ""),
                job.get("source", ""), ai_result.get("score", ""),
                ai_result.get("location_type", ""), ai_result.get("salary_info", ""),
                ai_result.get("reason", ""), job.get("link", ""), "New"
            ])
    except Exception as e:
        print(f"    log_to_tracker error: {e}")

# ═════════════════════════════════════════════════════════════
# SCRAPERS — Only working, tested APIs
# ═════════════════════════════════════════════════════════════

def scrape_ashby():
    """Ashby ATS public JSON API — reliable, no auth needed."""
    jobs = []
    for co in ASHBY_COMPANIES:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{co['client']}?includeCompensation=true"
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json().get("jobs", []):
                if not job.get("isListed", True):
                    continue
                location = job.get("location", "")
                workplace = (job.get("workplaceType") or "").lower()
                desc = job.get("descriptionPlain", "")[:600]
                eligible, loc_type = is_eu_eligible(location, f"{workplace} {desc}")

                if not eligible:
                    continue

                salary = ""
                comp = job.get("compensation", {})
                if comp:
                    salary = (comp.get("compensationTierSummary", "") or
                              comp.get("scrapeableCompensationSalarySummary", ""))

                jobs.append({
                    "title": job.get("title", ""),
                    "company": co["name"],
                    "link": job.get("jobUrl", ""),
                    "description": desc,
                    "location": location,
                    "location_type": loc_type,
                    "salary": salary,
                    "source": "Ashby",
                })
        except Exception as e:
            print(f"  Ashby {co['name']} error: {e}")
    print(f"  Ashby: {len(jobs)} EU-eligible jobs")
    return jobs


def scrape_greenhouse():
    """Greenhouse ATS public JSON API."""
    jobs = []
    for co in GREENHOUSE_COMPANIES:
        url = f"https://api.greenhouse.io/v1/boards/{co['client']}/jobs?content=true"
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json().get("jobs", []):
                location = job.get("location", {}).get("name", "")
                desc = job.get("content", "")[:600]
                eligible, loc_type = is_eu_eligible(location, desc)
                if not eligible:
                    continue
                jobs.append({
                    "title": job.get("title", ""),
                    "company": co["name"],
                    "link": job.get("absolute_url", ""),
                    "description": desc,
                    "location": location,
                    "location_type": loc_type,
                    "salary": "",
                    "source": "Greenhouse",
                })
        except Exception as e:
            print(f"  Greenhouse {co['name']} error: {e}")
    print(f"  Greenhouse: {len(jobs)} EU-eligible jobs")
    return jobs


def scrape_lever():
    """Lever ATS public JSON API."""
    jobs = []
    for co in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{co['client']}?mode=json"
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json():
                cats = job.get("categories", {})
                location = cats.get("location", "")
                desc = job.get("descriptionPlain", "")[:600]
                eligible, loc_type = is_eu_eligible(location, desc)
                if not eligible:
                    continue
                jobs.append({
                    "title": job.get("text", ""),
                    "company": co["name"],
                    "link": job.get("hostedUrl", ""),
                    "description": desc,
                    "location": location,
                    "location_type": loc_type,
                    "salary": "",
                    "source": "Lever",
                })
        except Exception as e:
            print(f"  Lever {co['name']} error: {e}")
    print(f"  Lever: {len(jobs)} EU-eligible jobs")
    return jobs


def scrape_remotive():
    """Remotive JSON API — curated remote jobs."""
    jobs = []
    for cat in REMOTIVE_CATEGORIES:
        url = f"https://remotive.com/api/remote-jobs?category={cat}&limit=50"
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json().get("jobs", []):
                desc = job.get("description", "")[:600]
                if not is_insurance_relevant(f"{job.get('title','')} {job.get('company_name','')} {desc}"):
                    continue
                # Check candidate_required_location for EU
                req_loc = job.get("candidate_required_location", "").lower()
                if req_loc and "usa" in req_loc and "europe" not in req_loc:
                    continue
                jobs.append({
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "link": job.get("url", ""),
                    "description": desc,
                    "location": job.get("candidate_required_location", "Anywhere"),
                    "location_type": "remote",
                    "salary": job.get("salary", ""),
                    "source": "Remotive",
                })
        except Exception as e:
            print(f"  Remotive {cat} error: {e}")
    print(f"  Remotive: {len(jobs)} insurance-related jobs")
    return jobs


def scrape_rss():
    """RSS feeds — only tested, working ones."""
    jobs = []
    for feed in WORKING_RSS:
        r = fetch(feed["url"])
        if not r:
            continue
        try:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                desc = (item.findtext("description") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not is_insurance_relevant(f"{title} {desc}"):
                    continue
                jobs.append({
                    "title": title,
                    "company": feed["name"],
                    "link": link,
                    "description": desc[:600],
                    "location": "Remote",
                    "location_type": "remote",
                    "salary": "",
                    "source": feed["name"],
                })
        except Exception as e:
            print(f"  RSS {feed['name']} error: {e}")
    print(f"  RSS feeds: {len(jobs)} insurance-related jobs")
    return jobs


def scrape_career_pages():
    """Check career pages for operations OR AI/automation keywords. Lightweight check."""
    jobs = []
    ops_keywords = ["operations", "ops manager", "underwriting ops", "process",
                    "bpo", "programme manager", "program manager"]
    ai_keywords = ["ai", "automation", "claude", "llm", "langchain", "agent",
                   "machine learning", "workflow", "automation engineer", "ai engineer"]
    for co in CAREER_PAGES:
        r = fetch(co["url"])
        if not r:
            continue
        text = r.text.lower()
        found_ops = [kw for kw in ops_keywords if kw in text]
        found_ai = [kw for kw in ai_keywords if kw in text]
        found = found_ops + found_ai
        if found and ("remote" in text or "barcelona" in text or "spain" in text or "europe" in text):
            jobs.append({
                "title": f"Operations/AI roles detected at {co['name']}",
                "company": co["name"],
                "link": co["url"],
                "description": f"Keywords found: {', '.join(found)}. Check career page for specific roles.",
                "location": "Check page",
                "location_type": "check",
                "salary": "",
                "source": "Career Page",
            })
    print(f"  Career pages: {len(jobs)} with ops/AI keywords")
    return jobs


def scrape_adzuna():
    """Adzuna API — broad EU job search by keyword. Requires free API key at developer.adzuna.com."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("  Adzuna: skipped (ADZUNA_APP_ID / ADZUNA_APP_KEY not set — add as GitHub secrets)")
        return []

    jobs = []
    seen_titles = set()

    for search in ADZUNA_SEARCHES:
        country = search["country"]
        keywords = search["keywords"]
        url = (
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
            f"&results_per_page=20&what={requests.utils.quote(keywords)}&content-type=application/json"
        )
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json().get("results", []):
                title = job.get("title", "")
                company = job.get("company", {}).get("display_name", "")
                loc = job.get("location", {}).get("display_name", "")
                desc = job.get("description", "")[:600]
                link = job.get("redirect_url", "")

                dedup_key = f"{title}|{company}".lower()
                if dedup_key in seen_titles:
                    continue
                seen_titles.add(dedup_key)

                eligible, loc_type = is_eu_eligible(loc, desc)
                if not eligible:
                    continue
                if not is_insurance_relevant(f"{title} {company} {desc}"):
                    continue

                salary = ""
                sal_min = job.get("salary_min")
                sal_max = job.get("salary_max")
                if sal_min or sal_max:
                    salary = f"£/€{int(sal_min or 0):,}–{int(sal_max or 0):,}"

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": desc,
                    "location": loc,
                    "location_type": loc_type,
                    "salary": salary,
                    "source": f"Adzuna-{country.upper()}",
                })
        except Exception as e:
            print(f"  Adzuna {country}/{keywords[:30]} error: {e}")

    print(f"  Adzuna: {len(jobs)} EU-eligible matches across {len(ADZUNA_SEARCHES)} searches")
    return jobs


# ═════════════════════════════════════════════════════════════
# AI SCORING — Claude API
# ═════════════════════════════════════════════════════════════

def score_job(job):
    """Score job fit using Claude AI. Evaluates traditional ops, BA, and AI engineering roles."""
    if not ANTHROPIC_API_KEY:
        return {"score": 0, "reason": "No API key"}

    skills_list = ", ".join(
        PROFILE["core_competencies"]["operations_process"][:3] +
        PROFILE["core_competencies"]["compliance_governance"][:2] +
        PROFILE["core_competencies"]["data_technology"][:3] +
        PROFILE["core_competencies"]["ai_automation_stack"][:3]
    )
    roles_list = ", ".join(PROFILE["target_roles"][:12])
    companies_list = ", ".join(PROFILE["target_company_types"][:8])

    prompt = f"""You are a career advisor for insurance operations + AI automation professionals.

CANDIDATE: {PROFILE['name']}, {PROFILE['location']}
EXPERIENCE: {PROFILE['experience_summary']}
TARGET ROLES (traditional + AI): {roles_list}
TARGET COMPANIES: {companies_list}
KEY SKILLS: {skills_list}
LANGUAGES: English C2, French C1, Spanish native, Italian B2
MIN SALARY: €{PROFILE['min_salary_eur']:,}/year
LOCATION: Remote EU ✅ | Hybrid Barcelona ✅ | Everything else ❌

JOB:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Source: {job['source']}
Description: {job['description'][:800]}

SCORING RUBRIC:

### TIER 1: PERFECT MATCH (90-100) ⭐⭐⭐⭐⭐
- Traditional operations: Insurance/reinsurance ops, remote EU, senior level, €60K+
- OR AI Product/Engineer: Claude/LLM APIs + Finance/Insurance domain knowledge, remote EU
- OR AI Engineer: builds AI agents/automation for finance/insurance workflows, remote EU
- OR Business Analyst: InsurTech/FinTech/MGA, process ownership focus, remote EU, €60K+
- Explicitly values domain expertise translation into automation or process improvement

### TIER 2: STRONG MATCH (80-89) ⭐⭐⭐⭐
- Operations or BA role at insurer/insurtech/MGA, EU eligible
- OR AI/automation engineer role mentioning LangChain/LangGraph/Claude with finance/insurance context
- OR AI Software Engineer at fintech/insurtech where 10yr domain expertise is a clear advantage
- BA roles where process documentation + stakeholder management = clear requirements match

### TIER 3: GOOD MATCH (70-79) ⭐⭐⭐
- Adjacent role: data ops, programme mgmt, BA, process automation at insurance/fintech company
- OR AI Engineer / ML Engineer with Python + API skills in any domain, remote EU (domain bridge possible)
- Business Analyst at fintech/scale-up where insurance experience is transferable advantage

### TIER 4: WEAK MATCH (50-69) ⭐⭐
- Insurance-related but wrong function (pure sales, claims adjuster) OR location unclear
- AI Engineer role at generic tech company with no finance/insurance domain context
- BA role at generic company with no insurance/fintech domain

### HARD REJECT (score 0):
- On-site outside Barcelona or hybrid outside Barcelona
- Salary explicitly below €50,000
- Junior/graduate/intern roles
- Pure actuarial, pure ML research scientist, pure data scientist (no ops bridge)
- Requires 5+ years pure AI/ML research experience
- US-only or non-EU location

### AI ENGINEER / PRODUCT ENGINEER REFRAME RULES:
- "1-3 years AI experience" → ACCEPT: 1yr practical + Anthropic certs + 10yrs domain ops
- "LangChain/LangGraph required" → ACCEPT: has LangGraph + CrewAI portfolio
- "Python scripting for automation" → ACCEPT: intermediate Python confirmed
- "Product mindset" → ACCEPT: 10 years translating business needs to tech requirements
- Missing 5+ years pure AI/ML → REJECT (too senior a gap for AI Engineer)

### BUSINESS ANALYST SCORING NOTES:
- BA at InsurTech/MGA/Reinsurer with 10yr domain experience → score 80-90
- BA at FinTech/scale-up where insurance knowledge is advantage → score 70-80
- "Requirements gathering", "stakeholder management", "SOP", "process mapping" = strong signals

Respond ONLY in valid JSON:
{{"score":<int>,"reason":"<1 sentence>","location_type":"<remote_eu|hybrid_barcelona|onsite|unclear>","salary_info":"<salary or 'not specified'>"}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        text = r.json()["content"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"    AI scoring error: {e}")
        return None


def research_company(company_name, job_title):
    """Brief company research using Claude."""
    if not ANTHROPIC_API_KEY:
        return ""
    prompt = f"""Write a 5-bullet 'Know Before You Apply' brief about "{company_name}" for a candidate applying for "{job_title}" in insurance operations.

Cover: what they do (insurance/insurtech focus), size/funding, culture & remote policy, recent news, one interview tip. Be factual and concise."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"    Research error: {e}")
        return ""


# ═════════════════════════════════════════════════════════════
# EMAIL
# ═════════════════════════════════════════════════════════════


def send_email(matched_jobs, career_hints=None):
    if not matched_jobs and not career_hints:
        return
    if not GMAIL_USER:
        return

    career_hints = career_hints or []
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(matched_jobs)} Job Match(es) — Ops/BA/AI — {TODAY}"
    msg["From"] = f"Job Hunter <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER

    html = [f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;">
<div style="background:linear-gradient(135deg,#1a2744,#2563eb);padding:20px;border-radius:8px;">
  <h2 style="color:#fff;margin:0;">🎯 {len(matched_jobs)} Match(es) — Ops / BA / AI Engineering</h2>
  <p style="color:#ddd;margin:6px 0 0;">{TODAY} · Score {PROFILE['min_match_score']}%+ · Remote EU / Barcelona</p>
</div>"""]

    for i, job in enumerate(matched_jobs, 1):
        ai = job.get("ai_result", {})
        research = job.get("company_research", "")
        score = ai.get("score", "?")
        color = "#16a34a" if score >= 85 else "#2563eb" if score >= 75 else "#d97706"

        html.append(f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0;">
  <h3 style="margin:0;">#{i} <a href="{job['link']}" style="color:#1a2744;">{job['title']}</a></h3>
  <p style="color:#6b7280;margin:4px 0;">{job['company']} · {job['source']} · {job['location']}</p>
  <div style="display:inline-block;background:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;margin:8px 0;">{score}%</div>
  <p><em>{ai.get('reason', '')}</em></p>
  <p><b>Location:</b> {ai.get('location_type', '')} · <b>Salary:</b> {ai.get('salary_info', 'not specified')}</p>
  {"<h4>Company Research</h4><pre style='background:#f8f8ff;padding:10px;border-radius:4px;font-size:12px;white-space:pre-wrap;'>" + research + "</pre>" if research else ""}
  <p><a href="{job['link']}" style="background:#1a2744;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;">Apply →</a></p>
</div>""")

    if career_hints:
        html.append("""
<div style="background:#f0f4ff;border-radius:8px;padding:16px;margin:16px 0;">
  <h3 style="color:#1a2744;margin:0 0 8px;">📋 Companies With Active Hiring (Check Manually)</h3>
  <p style="color:#6b7280;font-size:13px;margin:0 0 12px;">These career pages had ops/AI keywords — no specific listing confirmed. Worth checking directly.</p>
  <ul style="margin:0;padding-left:20px;">""")
        for hint in career_hints:
            kws = hint.get("description", "")
            html.append(f'<li style="margin:6px 0;"><a href="{hint["link"]}" style="color:#2563eb;font-weight:bold;">{hint["company"]}</a> <span style="color:#6b7280;font-size:12px;">— {kws}</span></li>')
        html.append("</ul></div>")

    html.append(f"""
<p style="color:#999;font-size:11px;border-top:1px solid #eee;padding-top:12px;margin-top:20px;">
  AI Job Hunter v3 · {len(matched_jobs)} scored match(es) · {len(career_hints)} company hint(s) · {TODAY}
</p></body></html>""")

    plain_lines = [f"#{i} {j['title']} @ {j['company']} ({j.get('ai_result',{}).get('score','?')}%)"
                   for i, j in enumerate(matched_jobs, 1)]
    if career_hints:
        plain_lines.append("\nCompanies to check:")
        plain_lines += [f"  - {h['company']}: {h['link']}" for h in career_hints]

    msg.attach(MIMEText("\n".join(plain_lines), "plain"))
    msg.attach(MIMEText("".join(html), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Email sent: {len(matched_jobs)} match(es), {len(career_hints)} hints")
    except Exception as e:
        print(f"❌ Email error: {e}")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*60}")
    print(f"  AI Job Hunter v3 — {TODAY}")
    print(f"{'='*60}\n")

    seen = load_seen()

    print("📡 Scanning job sources...")
    print("  → Ashby ATS API")
    all_jobs  = scrape_ashby()
    print("  → Greenhouse ATS API")
    all_jobs += scrape_greenhouse()
    print("  → Lever ATS API")
    all_jobs += scrape_lever()
    print("  → Remotive API")
    all_jobs += scrape_remotive()
    print("  → RSS feeds")
    all_jobs += scrape_rss()
    print("  → Adzuna (EU-wide keyword search)")
    all_jobs += scrape_adzuna()
    # Career pages produce hints only — not scored as job listings
    print("  → Career pages (hints only)")
    career_page_hits = scrape_career_pages()

    print(f"\n📊 Total EU-eligible listings: {len(all_jobs)}")
    print(f"📋 Career page hints: {len(career_page_hits)}")

    # Deduplicate against seen
    new_jobs = []
    for j in all_jobs:
        jid = job_id(j["title"], j["company"])
        if jid not in seen:
            seen.add(jid)
            new_jobs.append(j)

    print(f"🆕 New (not seen before): {len(new_jobs)}")

    # Career page hints: include all (they're manual check signals, not scored jobs)
    new_hints = career_page_hits

    if not new_jobs and not new_hints:
        print("✅ No new jobs or hints today.")
        save_seen(seen)
        return

    # Score with AI
    matched = []
    if new_jobs:
        print(f"\n🤖 Scoring {len(new_jobs)} jobs with Claude AI...")
        for job in new_jobs:
            result = score_job(job)
            if not result:
                continue

            score = result.get("score", 0)
            emoji = "🎯" if score >= 85 else "✅" if score >= 75 else "➖" if score >= 50 else "❌"
            print(f"  {emoji} {score:3d}% — {job['title']} @ {job['company']}")

            if score >= PROFILE["min_match_score"]:
                job["ai_result"] = result
                print(f"       Researching {job['company']}...")
                job["company_research"] = research_company(job["company"], job["title"])
                log_to_tracker(job, result)
                matched.append(job)

    print(f"\n🏆 Matches at {PROFILE['min_match_score']}%+: {len(matched)}")

    if matched or new_hints:
        send_email(matched, career_hints=new_hints)

    save_seen(seen)
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
