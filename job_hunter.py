"""
AI Job Hunter v3 — Marc Planas Callico
Triple-Track job scanner: Insurance Ops/AI (A) · BA/Digital Transformation (B) · AI Product Engineer (C)
Implements Prompt Maestro v5.0: Phase 1 blockers → Phase 2 track ID → Phase 3 weighted scoring → Phase 4 output.
Scans ATS APIs + RSS + Adzuna daily, scores with Claude AI, generates PDFs, logs to tracker.
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
    # Track B/C — AI + consulting + transformation (Greenhouse)
    {"name": "Palantir",           "client": "palantir"},
    {"name": "Weights & Biases",   "client": "wandb"},
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
# Add to CAREER_PAGES — consultancies, EU insurance-consulting, and AI platforms
CAREER_PAGES += [
    # Track A/B — Consulting & insurance advisory
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
    # AI/Automation InsurTech platforms — Track A/C
    {"name": "Embat", "url": "https://www.embat.com/careers"},
    {"name": "Tractable (AI Claims)", "url": "https://www.tractable.ai/careers"},
    {"name": "Shift Technology", "url": "https://www.shift-technology.com/careers"},
    {"name": "Concirrus (InsurTech AI)", "url": "https://www.concirrus.com/careers"},
    # Track C — AI Product / Digital Workforce platforms (EU-remote)
    {"name": "Aisera", "url": "https://aisera.com/careers/"},
    {"name": "Inari (InsurTech AI)", "url": "https://inari.com/careers"},
    {"name": "Akur8", "url": "https://www.akur8.com/careers"},
    {"name": "Dacadoo", "url": "https://www.dacadoo.com/careers/"},
    {"name": "Bdeo", "url": "https://bdeo.io/en/careers/"},
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
    # Track A — Insurance Ops / AI Transformation
    {"country": "gb", "keywords": "insurance operations manager remote"},
    {"country": "gb", "keywords": "underwriting operations MGA remote"},
    {"country": "gb", "keywords": "insurtech operations manager remote"},
    {"country": "gb", "keywords": "reinsurance operations specialist remote"},
    {"country": "gb", "keywords": "MGA operations manager remote"},
    {"country": "de", "keywords": "insurance operations remote Europe"},
    {"country": "fr", "keywords": "insurance operations manager remote"},
    {"country": "es", "keywords": "insurance operations remote"},
    {"country": "nl", "keywords": "insurance operations remote"},
    # Track B — BA / Digital Transformation
    {"country": "gb", "keywords": "business analyst insurtech remote"},
    {"country": "gb", "keywords": "digital transformation analyst financial services remote"},
    {"country": "gb", "keywords": "business analyst AI insurance remote"},
    {"country": "gb", "keywords": "process analyst fintech remote"},
    {"country": "de", "keywords": "business analyst digital transformation insurance remote"},
    {"country": "nl", "keywords": "business analyst insurtech remote"},
    # Track C — AI Product Engineer / Digital Workforce
    {"country": "gb", "keywords": "AI product engineer insurance fintech remote"},
    {"country": "gb", "keywords": "AI implementation specialist financial services remote"},
    {"country": "gb", "keywords": "LangGraph LangChain engineer insurance remote"},
    {"country": "gb", "keywords": "digital workforce specialist AI agent remote"},
    {"country": "de", "keywords": "AI product engineer fintech remote"},
    {"country": "nl", "keywords": "AI automation engineer financial services remote"},
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
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(seen):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen), f)
    except Exception as e:
        print(f"    save_seen error: {e}")

def is_insurance_relevant(text):
    """Check if job is relevant for any of the three tracks.

    Track A: Insurance/reinsurance/MGA domain roles.
    Track B: BA/digital transformation at insurance/fintech.
    Track C: AI Product Engineer / agent orchestration with finance-insurance domain context.
    """
    t = text.lower()

    # Track A — core insurance/reinsurance domain
    strong_insurance = [
        "insurance", "insurtech", "reinsurance", "underwriting", "mga ",
        "managing general", "coverholder", "lloyd's", "actuar", "claims",
        "broker", "solvency", "dua", "delegated underwriting",
        "fintech", "financial services", "insuretechdaily", "bordereaux",
    ]

    # Track B — BA / digital transformation signals
    ba_keywords = [
        "business analyst", "process analyst", "operational analyst",
        "digital transformation", "business analysis",
        "requirements elicitation", "bpmn", "gap analysis", "user stories",
        "stakeholder management", "process mapping",
    ]

    # Track C — AI Product Engineer / agent orchestration (tool-specific)
    ai_automation = [
        "claude api", "langchain", "langgraph", "crewai",
        "prompt engineer", "llm", "generative ai",
        "ai agent", "ai implementation", "ai automation", "rag", "mcp",
        "ai-powered", "ai-enabled", "digital workforce", "ai product engineer",
        "agentic", "agent orchestration", "workflow automation",
    ]

    # Finance/insurance domain context (required for Track C to be accepted)
    finance_insurance_domain = [
        "claims automation", "underwriting automation", "claims processing",
        "insurance automation", "operations ai", "fintech",
        "treasury operations", "finance operations", "financial automation",
        "insurance operations", "reinsurance", "policy management", "bordereaux",
        "financial services", "insurance platform", "mga", "insurtech",
    ]

    # Track B also accepted at any regulated/financial services context
    regulated_domain = finance_insurance_domain + [
        "regulatory", "compliance", "financial", "banking", "payments",
        "asset management", "wealth management",
    ]

    has_insurance = any(kw in t for kw in strong_insurance)
    has_ba = any(kw in t for kw in ba_keywords)
    has_ai = any(kw in t for kw in ai_automation)
    has_finance_domain = any(kw in t for kw in finance_insurance_domain)
    has_regulated = any(kw in t for kw in regulated_domain)

    # Track A: traditional insurance/fintech domain
    if has_insurance:
        return True
    # Track B: BA/transformation + regulated/financial context
    if has_ba and has_regulated:
        return True
    # Track C: AI orchestration tools + finance-insurance domain
    if has_ai and has_finance_domain:
        return True
    return False

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
                w.writerow([
                    "Date", "Title", "Company", "Source", "Track", "Score",
                    "Recommendation", "Location", "Salary", "Blockers",
                    "Reason", "CV_To_Use", "Link", "Status",
                ])
            w.writerow([
                TODAY,
                job.get("title", ""),
                job.get("company", ""),
                job.get("source", ""),
                ai_result.get("track", ""),
                ai_result.get("score", ""),
                ai_result.get("recommendation", ""),
                ai_result.get("location_type", ""),
                ai_result.get("salary_info", ""),
                ai_result.get("blockers", ""),
                ai_result.get("reason", ""),
                ai_result.get("cv_to_use", ""),
                job.get("link", ""),
                "New",
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
    """Score job fit using Claude AI with the full triple-track Prompt Maestro v5.0 protocol.

    Phase 1: Hard blockers (auto-discard).
    Phase 2: Track identification (A / B / C / Mixed).
    Phase 3: Track-specific weighted scoring matrix.
    Phase 4: Structured output with CV adaptation hints.
    """
    if not ANTHROPIC_API_KEY:
        return {"score": 0, "reason": "No API key"}

    ops_skills = ", ".join(PROFILE["core_competencies"]["operations_process"][:4])
    ai_skills  = ", ".join(PROFILE["core_competencies"]["ai_automation_stack"][:6])
    ba_skills  = ", ".join(PROFILE["core_competencies"]["ba_transformation"][:4])
    compliance = ", ".join(PROFILE["core_competencies"]["compliance_governance"][:4])

    prompt = f"""You are a precision career advisor implementing the Prompt Maestro v5.0 for Marc Planas Callico.

═══════════════════════════════════════════════════════════
CANDIDATE PROFILE — MARC PLANAS CALLICO
═══════════════════════════════════════════════════════════
Location: Barcelona · CET · Remote-ready EMEA
Current role: Operations Data Manager · Accelerant (MGA Reinsurance, UK & Europe) · Apr 2025–Present
Experience: 10+ years insurance/reinsurance operations (MGA, Lloyd's, delegated authority, bordereaux)
Languages: Spanish/Catalan native · English C2 · French C1 · Italian B2
Salary floor: €60K (absolute) | Target: €75K+ Track A/B · €65K+ Track C

VERIFIED TECH STACK (production):
- Python intermediate · SQL intermediate · Claude API (Anthropic certified) · CrewAI · LangGraph
- MCP · n8n · Streamlit · Pytest · GitHub Actions · Power BI · Snowflake · Guidewire · Salesforce

VERIFIED COMPETENCIES:
- Operations/Process: {ops_skills}
- AI/Automation: {ai_skills}
- BA/Transformation: {ba_skills}
- Compliance: {compliance}

GITHUB PORTFOLIO (public, verified): github.com/intlinsure
- reinsurance-contract-crew (CrewAI · 3-agent contract review · DORA-aligned)
- claims-triage-langgraph (LangGraph · RAG · ChromaDB · HITL · Streamlit · Pytest)
- insurance-ai-governance-pack (EU AI Act Arts 6-13 · DORA Art.28 · gap analysis)
- bordereaux-intake-n8n-mcp (n8n · MCP · Claude API · bordereaux validation)
- sql-insurance-data-quality · agent-evaluation-dashboard · ba-process-models

═══════════════════════════════════════════════════════════
JOB TO EVALUATE
═══════════════════════════════════════════════════════════
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Source: {job['source']}
Description: {job['description'][:900]}

═══════════════════════════════════════════════════════════
EVALUATION PROTOCOL — EXECUTE IN ORDER
═══════════════════════════════════════════════════════════

## PHASE 1 — HARD BLOCKERS (auto-score 0 if any present)
Check for these in the JD. If found → score=0, state which blocker:
- Madrid presencial / on-site Madrid
- Salary explicitly below €55,000
- PhD in AI/ML required
- Open-source contributions to AI core frameworks required
- AI Research Scientist (not AI Product Engineer)
- Stack 100% model training / fine-tuning with no orchestration
- Junior / graduate / intern role (unless exceptional AI + domain combo)
- NTT Data or similar IT vendors without insurance practice
- Sector completely unrelated (gaming, aerospace, unrelated manufacturing)

## PHASE 2 — TRACK IDENTIFICATION
Identify which track(s) this role covers:

TRACK A — Insurance Ops / AI Transformation: JD mentions any of:
MGA · Lloyd's · Delegated Authority · Bordereaux · Coverholder · Reinsurance Operations
Insurance Platform · Binding Authority · Solvency II / DORA / IFRS 17 as requirements

TRACK B — Digital Transformation BA / Consultant: JD mentions any of:
Business Analyst · Digital Transformation · Requirements · Stakeholder
Process Improvement · BPMN · Agile BA · Gap Analysis · Consulting · Change Management
Financial Services without specific insurance spec

TRACK C — AI Product Engineer / Digital Workforce: JD mentions any of:
AI Product Engineer · AI Implementation · LLM · Agent · Workflow Automation
Claude / GPT / LangChain / LangGraph / MCP · Hacker mindset · Ship fast
Digital Workforce · Friction removal · Internal tooling

## PHASE 3 — SCORE WITH TRACK-SPECIFIC MATRIX

### IF TRACK A (or Mixed with A dominant):
Score each axis 0-10, multiply by weight, sum for final:
- Insurance domain match (MGA/Lloyd's/DA/Reinsurance): weight 0.30
- AI/Automation stack match (CrewAI/LangGraph/Claude/n8n): weight 0.25
- Seniority & scope fit (senior/lead, not junior/admin): weight 0.20
- Compliance match (DORA/SolvII/IFRS17/OFAC): weight 0.15
- Location/salary fit (EMEA remote, ≥€60K): weight 0.10
Threshold to recommend application: ≥6.0/10 (i.e. 60/100 when scaled)

### IF TRACK B (or Mixed with B dominant):
Score each axis 0-10, multiply by weight, sum for final:
- BA/process skills match (requirements, BPMN, gap analysis): weight 0.25
- Digital/AI component (not pure BA without tech): weight 0.25
- Domain transferability (insurance/finance/fintech): weight 0.20
- Consulting/client-facing component: weight 0.15
- Seniority + location/salary fit: weight 0.15
Threshold: ≥6.0/10

### IF TRACK C (or Mixed with C dominant):
Score each axis 0-10, multiply by weight, sum for final:
- AI Stack match (LLM orchestration, agents, MCP, RAG): weight 0.25
- Domain expertise required (finance/insurance/ops context): weight 0.25
- Builder/ownership profile (ship fast, end-to-end ownership): weight 0.20
- Business impact focus (KPIs business, not just tech metrics): weight 0.15
- Seniority fit + location/salary: weight 0.15
Threshold: ≥5.5/10 (lower — emergent profile, JDs over-spec)

### MIXED TRACKS: score from the most favorable track.

## TRACK C GAP REFRAME RULES (apply automatically):
- "1-3 years AI experience" → ACCEPT: 1yr practical + Anthropic certs + 10yr domain
- "LangChain/LangGraph required" → ACCEPT: LangGraph + CrewAI portfolio verified
- "Background in Physics/Math/ML" → ACCEPT: 3yr science + autodidact + 10yr domain
- "Product mindset" → ACCEPT: 10yr translating business needs → tech specs
- "5+ years pure AI experience" → REJECT (real gap, do not reframe)
- "MLOps/Docker/K8s/cloud ML" → real gap, note honestly

## OUTPUT FORMAT
Return ONLY valid JSON — no markdown, no extra text:
{{
  "track": "<A|B|C|Mixed A+B|Mixed A+C|Mixed B+C>",
  "score": <int 0-100>,
  "score_breakdown": {{
    "axis1": {{"name": "<axis name>", "raw": <0-10>, "weight": <float>, "points": <float>}},
    "axis2": {{"name": "<axis name>", "raw": <0-10>, "weight": <float>, "points": <float>}},
    "axis3": {{"name": "<axis name>", "raw": <0-10>, "weight": <float>, "points": <float>}},
    "axis4": {{"name": "<axis name>", "raw": <0-10>, "weight": <float>, "points": <float>}},
    "axis5": {{"name": "<axis name>", "raw": <0-10>, "weight": <float>, "points": <float>}}
  }},
  "blockers": "<blocker found, or 'None'>",
  "gaps_and_reframe": "<key gaps and how to reframe, or 'None'>",
  "recommendation": "<APPLY|DISCARD|CONDITIONAL — with condition>",
  "reason": "<1-2 sentence summary>",
  "location_type": "<remote_eu|hybrid_barcelona|onsite|unclear>",
  "salary_info": "<salary range or 'not specified'>",
  "cv_to_use": "<exact CV file: MarcPlanas_CV_English_Final_Updated.docx | MarcPlanas_TrackB_BA_Transformation_EN.docx | MarcPlanas_CV_AIProductEngineer_EN.docx>",
  "keywords_to_mirror": "<top 5 ATS keywords from JD to mirror in CV>",
  "github_projects_to_mention": "<1-3 most relevant from portfolio>",
  "cv_summary_en": "<3-sentence tailored summary if score>=65, else empty>",
  "cv_summary_es": "<3-sentence tailored summary if score>=65, else empty>",
  "cover_letter_en": "<3-sentence opening if score>=65, else empty>",
  "cover_letter_es": "<3-sentence opening if score>=65, else empty>"
}}"""

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
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=40,
        )
        if r.status_code != 200:
            print(f"    AI scoring API error: {r.status_code}")
            return None
        data = r.json()
        content = data.get("content")
        if not content:
            print("    AI scoring error: empty content in response")
            return None
        text = content[0].get("text", "")
        if not text:
            print("    AI scoring error: empty text in response")
            return None
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
        if r.status_code != 200:
            print(f"    Research API error: {r.status_code}")
            return ""
        data = r.json()
        content = data.get("content")
        if not content:
            return ""
        text = content[0].get("text", "")
        return text.strip()
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
    msg["Subject"] = f"🎯 {len(matched_jobs)} Job Match(es) — Track A/B/C — {TODAY}"
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

        track     = ai.get("track", "?")
        rec       = ai.get("recommendation", "")
        blockers  = ai.get("blockers", "")
        gaps      = ai.get("gaps_and_reframe", "")
        cv_file   = ai.get("cv_to_use", "")
        kw_mirror = ai.get("keywords_to_mirror", "")
        gh_proj   = ai.get("github_projects_to_mention", "")

        html.append(f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0;">
  <h3 style="margin:0;">#{i} <a href="{job['link']}" style="color:#1a2744;">{job['title']}</a></h3>
  <p style="color:#6b7280;margin:4px 0;">{job['company']} · {job['source']} · {job['location']}</p>
  <div style="margin:8px 0;">
    <span style="display:inline-block;background:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;">{score}%</span>
    <span style="display:inline-block;background:#7c3aed;color:white;padding:4px 12px;border-radius:12px;font-weight:bold;margin-left:6px;">Track {track}</span>
    <span style="display:inline-block;background:#065f46;color:white;padding:4px 12px;border-radius:12px;font-size:11px;margin-left:6px;">{rec}</span>
  </div>
  <p><em>{ai.get('reason', '')}</em></p>
  <p><b>Location:</b> {ai.get('location_type', '')} · <b>Salary:</b> {ai.get('salary_info', 'not specified')}</p>
  {"<p><b>⚠️ Blockers:</b> " + blockers + "</p>" if blockers and blockers != "None" else ""}
  {"<p><b>🔄 Gaps/Reframe:</b> " + gaps + "</p>" if gaps and gaps != "None" else ""}
  {"<p><b>📄 CV:</b> " + cv_file + "</p>" if cv_file else ""}
  {"<p><b>🔑 Mirror keywords:</b> " + kw_mirror + "</p>" if kw_mirror else ""}
  {"<p><b>💻 GitHub projects:</b> " + gh_proj + "</p>" if gh_proj else ""}
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
    print(f"  AI Job Hunter v3 — Triple Track — {TODAY}")
    print(f"  Track A: Insurance Ops/AI · B: BA/Digital Transformation · C: AI Product Engineer")
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
        track = result.get("track", "?")
        rec   = result.get("recommendation", "")
        emoji = "🎯" if score >= 85 else "✅" if score >= 75 else "➖" if score >= 50 else "❌"
        print(f"  {emoji} {score:3d}% [Track {track}] {rec} — {job['title']} @ {job['company']}")

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
