"""
AI Job Hunter v2 — Marc Planas
Rebuilt from scratch. Scans working job APIs daily, scores with Claude AI,
generates tailored PDF CVs + cover letters, researches companies, logs to tracker.
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
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from marc_profile import PROFILE

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    )
    from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
    REPORTLAB = True
except ImportError:
    REPORTLAB = False
    print("⚠ reportlab not installed — PDF generation disabled")

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
    {"name": "Tractable",              "client": "tractable"},
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
    {"name": "Tractable",          "client": "tractable"},
    {"name": "Guidewire",          "client": "guidewire"},
    {"name": "Duck Creek",         "client": "duckcreek"},
    {"name": "FINEOS",             "client": "fineos"},
    {"name": "CoverGo",            "client": "covergo"},
    {"name": "Hokodo",             "client": "hokodo"},
    {"name": "Concirrus",          "client": "concirrus"},
    # Additional EU InsurTech/FinTech (Greenhouse)
    {"name": "Coalition",          "client": "coalitioninc"},
    {"name": "Branch Insurance",   "client": "branchinsurance"},
    {"name": "Hippo Insurance",    "client": "hippoinsurance"},
    {"name": "Openly",             "client": "openly"},
    {"name": "Kin Insurance",      "client": "kininsurance"},
]

# Lever ATS companies
LEVER_COMPANIES = [
    {"name": "Wakam",        "client": "wakam"},
    {"name": "Prima",        "client": "prima"},
    {"name": "Superscript",  "client": "superscript"},
    {"name": "Laka",         "client": "laka"},
    {"name": "Flock",        "client": "flock"},
    # Additional EU InsurTech/FinTech (Lever)
    {"name": "Pie Insurance", "client": "pieinsurance"},
    {"name": "At-Bay",        "client": "atbay"},
    {"name": "Embroker",      "client": "embroker"},
    {"name": "Corvus Insurance", "client": "corvusinsurance"},
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
    # New: AI/Automation InsurTech platforms and solutions
    {"name": "Embat", "url": "https://www.embat.com/careers"},
    {"name": "Tractable (AI Claims)", "url": "https://www.tractable.ai/careers"},
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
    {"country": "gb", "keywords": "insurance operations manager remote"},
    {"country": "gb", "keywords": "underwriting operations remote"},
    {"country": "gb", "keywords": "insurtech operations remote"},
    {"country": "gb", "keywords": "business analyst insurtech remote"},
    {"country": "gb", "keywords": "AI product engineer insurance remote"},
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
    strong_insurance = ["insurance", "insurtech", "reinsurance", "underwriting", "mga ",
                       "managing general", "coverholder", "lloyd's", "actuar", "claims",
                       "broker", "solvency", "dua", "delegated underwriting",
                       "fintech", "financial services", "insuretechdaily"]

    # Business analysis at insurance/fintech
    ba_insurance = ["business analyst", "process analyst", "operational analyst",
                    "digital transformation", "business analysis"]

    # AI/automation keywords (tool-specific)
    ai_automation = ["claude api", "langchain", "langgraph", "crewai",
                     "prompt engineer", "llm", "generative ai",
                     "ai agent", "ai implementation", "ai automation", "rag", "mcp",
                     "ai-powered", "ai-enabled"]

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
    """Check if role is remote EU or Barcelona-based."""
    loc = location_text.lower()
    desc = description_text.lower()
    combined = f"{loc} {desc}"

    # Fully remote
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
    """Score job fit using Claude AI. Returns dict with score + tailored content.
    Evaluates both traditional insurance operations AND new AI Product Engineer roles."""
    if not ANTHROPIC_API_KEY:
        return {"score": 0, "reason": "No API key"}

    # Build skills list from both traditional ops and AI stack
    skills_list = ", ".join(
        PROFILE["core_competencies"]["operations_process"][:3] +
        PROFILE["core_competencies"]["compliance_governance"][:2] +
        PROFILE["core_competencies"]["data_technology"][:3] +
        PROFILE["core_competencies"]["ai_automation_stack"][:3]
    )
    roles_list = ", ".join(PROFILE["target_roles"][:10])
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
- OR AI Product Engineer: Claude/LLM APIs + (Finance/Insurance domain knowledge), remote EU
- OR Business Analyst: InsurTech/FinTech/MGA, process ownership focus, remote EU, €60K+
- Explicitly values domain expertise translation into automation or process improvement

### TIER 2: STRONG MATCH (80-89) ⭐⭐⭐⭐
- Operations or BA role at insurer/insurtech/MGA, EU eligible
- OR AI/automation role mentioning LangChain/LangGraph/Claude with finance/insurance context
- BA roles where process documentation + stakeholder management = clear requirements match
- Clear path to own end-to-end processes (manual → improved/automated)

### TIER 3: GOOD MATCH (70-79) ⭐⭐⭐
- Adjacent role: data ops, programme mgmt, BA, process automation at insurance/fintech company
- OR: AI role with transferable skills (Python, SQL, API integration) in ANY domain, remote EU
- Business Analyst at fintech/scale-up where insurance experience is transferable advantage

### TIER 4: WEAK MATCH (50-69) ⭐⭐
- Insurance-related but wrong function (pure sales, claims adjuster) OR location unclear
- BA role at generic company with no insurance/fintech domain — learning curve on domain
- Would need convincing about domain expertise relevance

### TIER 5: POOR MATCH (0-49) ⚠️
- Wrong domain entirely (pure FAANG SWE, pure ML research, public sector BA)
- Wrong location (on-site Asia, hard-reject timezones)
- Junior/intern/graduate unless exceptional AI + domain combo
- Explicitly requires experience candidate lacks (actuary, PhD ML, 5+ years pure AI)

### HARD REJECT (score 0):
- On-site outside Barcelona
- Hybrid outside Barcelona
- Salary explicitly below €50,000
- Junior/graduate/intern roles without compelling domain + AI angle
- Pure actuarial or pure software engineering (no domain bridge)
- Requires 5+ years AI/ML experience (candidate has 1yr practical + certs)
- AI Research Scientist (not AI Product Engineer or BA)

### AI PRODUCT ENGINEER REFRAME RULES:
If role asks for "AI/ML experience" at different level than candidate has:
- "1-3 years AI experience needed" → ACCEPT: has 1 year practical + Anthropic certs + 10 years domain
- "LangChain/LangGraph required" → ACCEPT: has CrewAI + LangGraph portfolio projects
- "Background in Physics/ML" → ACCEPT: 3 years science + autodidact demonstrated, 10 years domain
- "Product mindset" → ACCEPT: 10 years translating business needs to tech specs
- Missing 5+ years pure AI → REJECT (too junior for senior AI Product Engineer)

### BUSINESS ANALYST SCORING NOTES:
- BA at InsurTech/MGA/Reinsurer with 10yr domain experience → score 80-90
- BA at FinTech/scale-up where insurance knowledge is advantage → score 70-80
- BA at generic company with process improvement focus → score 50-65
- "Requirements gathering", "stakeholder management", "SOP", "process mapping" = strong signals
- Key BA signal: does the JD mention financial services, insurance, or regulatory compliance?

If score >= 75, also provide:
- A 3-sentence tailored CV summary in English (emphasize: domain expert building AI systems)
- A 3-sentence tailored CV summary in Spanish
- A 3-sentence cover letter opening in English
- A 3-sentence cover letter opening in Spanish

Respond ONLY in valid JSON:
{{"score":<int>,"reason":"<1 sentence>","location_type":"<remote_eu|hybrid_barcelona|onsite|unclear>","salary_info":"<salary or 'not specified'>","cv_summary_en":"<or empty>","cv_summary_es":"<or empty>","cover_letter_en":"<or empty>","cover_letter_es":"<or empty>"}}"""

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
                "max_tokens": 800,
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
# PDF GENERATION — career-ops Playwright renderer (primary)
#                  ReportLab (fallback)
# ═════════════════════════════════════════════════════════════

NAVY   = HexColor("#1a2744") if REPORTLAB else None
ACCENT = HexColor("#2563eb") if REPORTLAB else None
DARK   = HexColor("#1f2937") if REPORTLAB else None
GRAY   = HexColor("#6b7280") if REPORTLAB else None

_CAREER_OPS_SCRIPT = os.path.join(os.path.dirname(__file__), "career-ops", "generate-pdf.mjs")


def _build_pdf_via_playwright(job, ai_result, lang, doc_type):
    """Call career-ops/generate-pdf.mjs --stdin-json and return PDF bytes.

    Returns None if career-ops is not available or the subprocess fails.
    """
    import subprocess, json as _json
    if not os.path.exists(_CAREER_OPS_SCRIPT):
        return None
    summary_key = f"cv_summary_{lang}"
    payload = {
        "type":          doc_type,
        "lang":          lang,
        "job": {
            "title":    job.get("title", ""),
            "company":  job.get("company", ""),
            "location": job.get("location", ""),
            "link":     job.get("link", ""),
        },
        "ai_summary":    ai_result.get(summary_key) or ai_result.get("cv_summary_en", ""),
        "cover_opening": ai_result.get(f"cover_letter_{lang}", ""),
    }
    try:
        result = subprocess.run(
            ["node", _CAREER_OPS_SCRIPT, "--stdin-json", "--format=a4"],
            input=_json.dumps(payload).encode(),
            capture_output=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            return bytes(result.stdout)
        if result.stderr:
            print(f"    Playwright PDF warn: {result.stderr.decode()[:120]}")
    except Exception as e:
        print(f"    Playwright PDF error: {e}")
    return None


def build_pdf_cv(job, ai_result, lang="en"):
    # Try career-ops Playwright renderer first
    pdf = _build_pdf_via_playwright(job, ai_result, lang, doc_type="cv")
    if pdf:
        return pdf

    if not REPORTLAB:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    def s(name, **kw):
        d = dict(fontName="Helvetica", fontSize=10, textColor=DARK, leading=14)
        d.update(kw)
        return ParagraphStyle(name, **d)

    s_name    = s("N", fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, leading=26)
    s_sub     = s("Su", fontSize=10, textColor=ACCENT)
    s_contact = s("C", fontSize=9, textColor=GRAY, leading=12)
    s_sec     = s("Sec", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
                  spaceBefore=12, spaceAfter=3)
    s_body    = s("B", fontSize=9.5, leading=13, alignment=TA_JUSTIFY)
    s_bullet  = s("Bu", fontSize=9.5, leading=13, leftIndent=12)
    s_role_t  = s("RT", fontName="Helvetica-Bold", fontSize=10)
    s_role_c  = s("RC", fontName="Helvetica-Oblique", fontSize=9.5, textColor=ACCENT)
    s_role_d  = s("RD", fontSize=9, textColor=GRAY, alignment=TA_RIGHT)

    line = lambda: HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=4, spaceBefore=2)

    summary_key = "cv_summary_en" if lang == "en" else "cv_summary_es"
    summary = ai_result.get(summary_key, "") or PROFILE[summary_key]

    elems = []
    elems.append(Paragraph(PROFILE["name"], s_name))
    elems.append(Paragraph(f"{job['title']} · Insurance Operations · Process Excellence", s_sub))
    elems.append(Spacer(1, 3))
    elems.append(Paragraph(
        f"{PROFILE['location']}  ·  {PROFILE['phone']}  ·  {PROFILE['email']}  ·  {PROFILE['linkedin']}",
        s_contact))
    elems.append(Spacer(1, 4))
    elems.append(line())

    # Profile
    sec_profile = "Professional Profile" if lang == "en" else "Perfil Profesional"
    elems.append(Paragraph(sec_profile, s_sec))
    elems.append(Paragraph(summary, s_body))

    # Core competencies
    sec_skills = "Core Competencies" if lang == "en" else "Competencias Clave"
    elems.append(Paragraph(sec_skills, s_sec))
    elems.append(line())
    for area, skills in PROFILE["core_competencies"].items():
        label = area.replace("_", " ").title()
        elems.append(Paragraph(f"<b>{label}:</b> {' · '.join(skills)}", s_bullet))

    # Languages
    langs = " · ".join(f"{l['lang']} {l['level']}" for l in PROFILE["languages"])
    elems.append(Paragraph(f"<b>Languages:</b> {langs}", s_bullet))

    # Experience
    sec_exp = "Professional Experience" if lang == "en" else "Experiencia Profesional"
    elems.append(Paragraph(sec_exp, s_sec))
    elems.append(line())
    for exp in PROFILE["career_history"]:
        header = Table(
            [[Paragraph(f"<b>{exp['title']}</b>", s_role_t),
              Paragraph(exp['period'], s_role_d)]],
            colWidths=[10*cm, 5.7*cm]
        )
        header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        elems.append(header)
        elems.append(Paragraph(f"{exp['company']} ({exp['type']})", s_role_c))
        for h in exp["highlights"]:
            elems.append(Paragraph(f"• {h}", s_bullet))
        elems.append(Spacer(1, 4))

    # Education
    sec_edu = "Education & Certifications" if lang == "en" else "Formación y Certificaciones"
    elems.append(Paragraph(sec_edu, s_sec))
    elems.append(line())
    for ed in PROFILE["education"]:
        elems.append(Paragraph(f"• <b>{ed['title']}</b> · {ed['institution']} · {ed['year']}", s_bullet))

    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()


def build_pdf_cover_letter(job, ai_result, lang="en"):
    # Try career-ops Playwright renderer first
    pdf = _build_pdf_via_playwright(job, ai_result, lang, doc_type="cover_letter")
    if pdf:
        return pdf

    if not REPORTLAB:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    def s(name, **kw):
        d = dict(fontName="Helvetica", fontSize=10, textColor=DARK, leading=14)
        d.update(kw)
        return ParagraphStyle(name, **d)

    s_name    = s("N", fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, leading=26)
    s_contact = s("C", fontSize=9, textColor=GRAY, leading=12)
    s_body    = s("B", fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=4)
    s_bold    = s("Bd", fontName="Helvetica-Bold", fontSize=10.5, spaceBefore=10)
    line = lambda: HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=8, spaceBefore=2)

    opening = ai_result.get(f"cover_letter_{lang}", "")
    company = job.get("company", "your company")
    title = job.get("title", "the role")

    elems = []
    elems.append(Paragraph(PROFILE["name"], s_name))
    elems.append(Paragraph(
        f"{PROFILE['location']}  ·  {PROFILE['phone']}  ·  {PROFILE['email']}  ·  {PROFILE['linkedin']}",
        s_contact))
    elems.append(Spacer(1, 8))
    elems.append(line())
    elems.append(Paragraph(TODAY, s_body))
    elems.append(Paragraph(f"Re: {title} — {company}", s_bold))
    elems.append(Spacer(1, 8))

    if lang == "en":
        salutation = "Dear Hiring Team,"
        body = [
            opening or f"I am writing to express my strong interest in the {title} position at {company}.",
            f"With over ten years of experience in insurance and reinsurance operations — spanning MGA platforms, "
            f"international programmes and broker environments — I bring a proven track record in end-to-end "
            f"process ownership, BPO management, SOP standardisation, and regulatory compliance including "
            f"Solvency II and sanctions screening.",
            f"In my current role at Accelerant, I own operational processes for a reinsurance MGA platform "
            f"serving 20+ managing agent partners, manage BPO supplier performance, and drive continuous "
            f"improvement using SQL, Power BI and AI tools. This experience aligns directly with the "
            f"requirements at {company}.",
            "I would welcome the opportunity to discuss how my background can contribute to your team.",
        ]
        closing = "Yours sincerely,"
    else:
        salutation = "Estimado equipo de selección,"
        body = [
            opening or f"Me dirijo a ustedes para expresar mi interés en el puesto de {title} en {company}.",
            f"Con más de diez años de experiencia en operaciones de seguros y reaseguros — en entornos MGA, "
            f"programas internacionales y corredores — aporto una trayectoria demostrada en gestión integral "
            f"de procesos, gestión de BPO, estandarización de SOPs y cumplimiento normativo incluyendo "
            f"Solvencia II y screening de sanciones.",
            f"En mi puesto actual en Accelerant, gestiono los procesos operativos de una plataforma MGA de "
            f"reaseguro con 20+ managing agents, superviso el rendimiento del proveedor BPO y lidero la "
            f"mejora continua con SQL, Power BI y herramientas de IA.",
            "Quedo a su disposición para comentar cómo mi perfil puede contribuir a su equipo.",
        ]
        closing = "Atentamente,"

    elems.append(Paragraph(salutation, s_bold))
    for p in body:
        if p.strip():
            elems.append(Paragraph(p, s_body))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(closing, s_body))
    elems.append(Spacer(1, 16))
    elems.append(Paragraph(f"<b>{PROFILE['name']}</b>", s_body))

    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════
# EMAIL
# ═════════════════════════════════════════════════════════════

def attach_pdf(msg, pdf_bytes, filename):
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)


def send_email(matched_jobs):
    if not matched_jobs or not GMAIL_USER:
        return

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"🎯 {len(matched_jobs)} Job Match(es) — Ops/BA/AI — {TODAY}"
    msg["From"] = f"Job Hunter <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER

    html = [f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;">
<div style="background:linear-gradient(135deg,#1a2744,#2563eb);padding:20px;border-radius:8px;">
  <h2 style="color:#fff;margin:0;">🎯 {len(matched_jobs)} Insurance Operations Match(es)</h2>
  <p style="color:#ddd;margin:6px 0 0;">{TODAY} · Score {PROFILE['min_match_score']}%+ · Remote EU / Barcelona</p>
</div>"""]

    pdf_count = 0
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

        safe = "".join(c for c in job['company'] if c.isalnum() or c in " _-")[:20].strip()
        for lang in ["en", "es"]:
            cv = build_pdf_cv(job, ai, lang)
            if cv:
                attach_pdf(msg, cv, f"CV_{lang.upper()}_{safe}_{TODAY}.pdf")
                pdf_count += 1
            cl = build_pdf_cover_letter(job, ai, lang)
            if cl:
                attach_pdf(msg, cl, f"CoverLetter_{lang.upper()}_{safe}_{TODAY}.pdf")
                pdf_count += 1

    html.append(f"""
<p style="color:#999;font-size:11px;border-top:1px solid #eee;padding-top:12px;margin-top:20px;">
  AI Job Hunter v2 · {len(matched_jobs)} match(es) · {pdf_count} PDFs attached · {TODAY}
</p></body></html>""")

    plain = "\n".join([f"#{i} {j['title']} @ {j['company']} ({j.get('ai_result',{}).get('score','?')}%)"
                       for i, j in enumerate(matched_jobs, 1)])

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain, "plain"))
    alt.attach(MIMEText("".join(html), "html"))
    msg.attach(alt)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Email sent: {len(matched_jobs)} match(es), {pdf_count} PDFs")
    except Exception as e:
        print(f"❌ Email error: {e}")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*60}")
    print(f"  AI Job Hunter v2 — {TODAY}")
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
    print("  → Career pages")
    all_jobs += scrape_career_pages()
    print("  → Adzuna (EU-wide keyword search)")
    all_jobs += scrape_adzuna()

    print(f"\n📊 Total EU-eligible listings: {len(all_jobs)}")

    # Deduplicate against seen
    new_jobs = []
    for j in all_jobs:
        jid = job_id(j["title"], j["company"])
        if jid not in seen:
            seen.add(jid)
            new_jobs.append(j)

    print(f"🆕 New (not seen before): {len(new_jobs)}")

    if not new_jobs:
        print("✅ No new jobs today.")
        save_seen(seen)
        return

    # Score with AI
    matched = []
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

    if matched:
        send_email(matched)

    save_seen(seen)
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
