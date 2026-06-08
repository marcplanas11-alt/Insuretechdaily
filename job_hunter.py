"""
EU Insurance Remote Job Monitor v5.1 — Marc Planas

Search scope:
- Track A: Insurance operations / claims / underwriting / reinsurance / Guidewire / MGA / coverholder roles
- Track B: Business Analyst / Digital Transformation / Process Analyst / Implementation Consultant roles
- Track C: AI Consultant / AI Automation / AI Implementation roles where insurance, finance, operations or governance context is useful

v5.1 tuning:
- Keeps Madrid presencial as a hard blocker.
- Keeps US-only as a hard blocker.
- Accepts 100% remote EU / EMEA / Europe roles.
- Accepts European relocation / hybrid for strong BA, transformation and consulting roles.
- Gives extra weight to BA, transformation consultant, insurance consultant and AI automation consultant roles.
- Penalizes pure AI Engineer / LLM Engineer roles when they lack consulting, operations, insurance, finance or governance context.
- Uses €45K as the explicit salary floor, while keeping roles with undisclosed salary.

The script is intentionally resilient in GitHub Actions:
- Missing email secrets do not crash the scan; email is skipped.
- Missing Anthropic key does not crash the scan; deterministic scoring is used.
- Missing Adzuna keys do not crash the scan; Adzuna is skipped.
"""

import csv
import hashlib
import html
import json
import os
import re
import smtplib
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Iterable, List, Tuple

import requests

try:
    from marc_profile import PROFILE
except Exception:
    PROFILE = {
        "name": "Marc Planas",
        "location": "Barcelona, Spain",
        "min_match_score": 50,
        "min_salary_eur": 45000,
        "target_roles": [],
        "target_company_types": [],
        "experience_summary": "Senior insurance operations, BA/digital transformation and AI-enabled transformation profile.",
    }

TODAY = datetime.now().strftime("%Y-%m-%d")
SEEN_FILE = "seen_jobs.json"
TRACKER_FILE = "job_tracker.csv"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

MIN_SALARY_EUR = int(PROFILE.get("min_salary_eur", 45000))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EUInsuranceJobMonitor/5.1)"}

EU_CITIES = [
    "barcelona", "valencia", "lisbon", "porto", "paris", "london", "dublin",
    "amsterdam", "brussels", "berlin", "munich", "frankfurt", "hamburg",
    "zurich", "geneva", "vienna", "milan", "rome", "stockholm", "copenhagen",
    "oslo", "helsinki", "warsaw", "prague", "luxembourg", "rotterdam", "utrecht",
]

EU_REGION_KEYWORDS = [
    "europe", "european union", "eu", "emea", "eea", "remote europe", "remote eu",
    "remote emea", "europe remote", "emea remote", "eu remote", "within europe",
]

EU_REMOTE_KEYWORDS = [
    "remote", "fully remote", "100% remote", "remote-first", "distributed",
    "work from anywhere", "work from home", "home based", "home-based",
] + EU_REGION_KEYWORDS

RELOCATION_KEYWORDS = [
    "relocation", "relocate", "visa sponsorship", "sponsorship available",
    "hybrid", "on-site", "onsite", "office-based", "office based",
]

MADRID_HARD_BLOCKERS = [
    "madrid presencial", "presencial madrid", "onsite madrid", "on-site madrid",
    "madrid onsite", "madrid office", "oficina madrid", "híbrido madrid", "hybrid madrid",
]

US_ONLY_PATTERNS = [
    "united states only", "us only", "usa only", "us-only", "u.s. only",
    "remote (us)", "remote - us", "remote, us", "remote us only",
    "authorized to work in the us", "authorized to work in the united states",
    "must be legally authorized to work in the united states",
]

TARGET_KEYWORD_GROUPS = {
    "insurance_ops": [
        "insurance operations", "insurance ops", "underwriting operations", "underwriting ops",
        "claims operations", "claims manager", "claims specialist", "claims analyst",
        "claims transformation", "claims automation", "policy operations", "broker operations",
        "delegated authority", "dua", "bordereaux", "mga", "coverholder", "lloyd's",
        "reinsurance operations", "reinsurance analyst", "technical accounting", "premium bordereaux",
        "programme manager", "program manager", "operations manager", "process owner",
    ],
    "platforms": [
        "guidewire", "policycenter", "claimcenter", "billingcenter", "duck creek", "fineos",
        "sapiens", "insurance platform", "core insurance system", "policy administration",
    ],
    "ba_transformation": [
        "business analyst", "senior business analyst", "it business analyst", "technical business analyst",
        "digital transformation", "transformation consultant", "business transformation",
        "process analyst", "business process analyst", "requirements analyst", "product owner",
        "change analyst", "implementation consultant", "solution consultant", "functional consultant",
        "insurance consultant", "financial services consultant", "business consultant", "process consultant",
    ],
    "ai_consulting": [
        "ai consultant", "ai automation consultant", "automation consultant", "intelligent automation",
        "ai implementation", "ai implementation consultant", "ai solutions consultant", "ai product consultant",
        "agentic process automation", "digital workforce", "ai agent", "workflow automation",
        "process automation", "operations automation", "ai governance", "responsible ai", "eu ai act",
        "dora", "ai risk", "ai compliance",
    ],
    "domain": [
        "insurance", "insurtech", "reinsurance", "underwriting", "claims", "broker", "fintech",
        "financial services", "mga", "coverholder", "lloyd's", "risk", "compliance",
    ],
}

BONUS_KEYWORDS = {
    "business analyst": 14,
    "senior business analyst": 16,
    "technical business analyst": 14,
    "it business analyst": 12,
    "transformation consultant": 14,
    "digital transformation consultant": 16,
    "insurance consultant": 14,
    "financial services consultant": 10,
    "implementation consultant": 10,
    "ai automation consultant": 16,
    "ai implementation consultant": 14,
    "intelligent automation consultant": 14,
    "guidewire business analyst": 18,
    "guidewire consultant": 16,
}

PURE_AI_ENGINEERING_KEYWORDS = [
    "ai engineer", "ai software engineer", "machine learning engineer", "ml engineer",
    "llm engineer", "generative ai engineer", "ai platform engineer", "research scientist",
    "deep learning engineer", "computer vision engineer", "nlp engineer",
]

CONSULTING_OR_DOMAIN_CONTEXT = [
    "consultant", "consulting", "implementation", "business analyst", "transformation",
    "operations", "workflow", "process", "insurance", "reinsurance", "claims", "underwriting",
    "financial services", "fintech", "governance", "compliance", "risk", "client-facing",
]

NEGATIVE_ROLE_KEYWORDS = [
    "intern", "internship", "graduate", "junior", "student", "sales development representative",
    "sdr", "account executive", "pure sales", "actuarial intern", "field adjuster",
]

ASHBY_COMPANIES = [
    {"name": "Descartes Underwriting", "client": "descartesunderwriting"},
    {"name": "Cytora", "client": "cytora"},
    {"name": "Artificial Labs", "client": "artificial"},
    {"name": "wefox", "client": "wefox"},
    {"name": "Alan", "client": "alan"},
    {"name": "Kota", "client": "kota"},
    {"name": "Inaza", "client": "inaza"},
    {"name": "Marshmallow", "client": "marshmallow"},
    {"name": "Zego", "client": "zego"},
    {"name": "Qover", "client": "qover"},
    {"name": "Embat", "client": "embat"},
    {"name": "Hugging Face", "client": "huggingface"},
]

GREENHOUSE_COMPANIES = [
    {"name": "Shift Technology", "client": "shifttechnology"},
    {"name": "Guidewire", "client": "guidewire"},
    {"name": "Duck Creek", "client": "duckcreek"},
    {"name": "FINEOS", "client": "fineos"},
    {"name": "CoverGo", "client": "covergo"},
    {"name": "Hokodo", "client": "hokodo"},
    {"name": "Concirrus", "client": "concirrus"},
    {"name": "Coalition", "client": "coalitioninc"},
    {"name": "At-Bay", "client": "atbay"},
]

LEVER_COMPANIES = [
    {"name": "Wakam", "client": "wakam"},
    {"name": "Prima", "client": "prima"},
    {"name": "Superscript", "client": "superscript"},
    {"name": "Laka", "client": "laka"},
    {"name": "Flock", "client": "flock"},
    {"name": "Embroker", "client": "embroker"},
    {"name": "Mistral AI", "client": "mistral"},
]

CAREER_PAGES = [
    {"name": "Accelerant", "url": "https://accelerant.ai/careers/"},
    {"name": "Swiss Re", "url": "https://careers.swissre.com/search/?q=operations&locationsearch="},
    {"name": "Munich Re", "url": "https://careers.munichre.com/en/munichre/search"},
    {"name": "SCOR", "url": "https://www.scor.com/en/careers"},
    {"name": "Hannover Re", "url": "https://www.hannover-re.com/careers"},
    {"name": "Novidea", "url": "https://www.novidea.com/careers"},
    {"name": "EIS Group", "url": "https://eisgroup.com/careers"},
    {"name": "Synpulse", "url": "https://www.synpulse.com/careers/"},
    {"name": "Capco", "url": "https://www.capco.com/Careers"},
    {"name": "Capgemini Invent", "url": "https://www.capgemini.com/careers"},
    {"name": "EY Financial Services", "url": "https://www.ey.com/en_gl/careers"},
    {"name": "Deloitte Financial Services", "url": "https://www.deloitte.com/global/en/careers.html"},
    {"name": "KPMG Insurance Advisory", "url": "https://kpmg.com/xx/en/home/careers.html"},
    {"name": "WTW", "url": "https://careers.wtwco.com/"},
    {"name": "Aon", "url": "https://www.aon.com/careers"},
    {"name": "Milliman", "url": "https://www.milliman.com/careers"},
    {"name": "Oliver Wyman", "url": "https://www.oliverwyman.com/careers"},
    {"name": "Maisa", "url": "https://www.maisa.ai/careers"},
]

REMOTIVE_CATEGORIES = ["finance", "business", "all-others", "software-dev"]

WORKING_RSS = [
    {"name": "Remotive Finance", "url": "https://remotive.com/remote-jobs/finance/feed"},
    {"name": "Remotive Business", "url": "https://remotive.com/remote-jobs/business/feed"},
    {"name": "We Work Remotely Finance", "url": "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss"},
    {"name": "Jobicy Finance", "url": "https://jobicy.com/?feed=job_feed&job_category=finance&job_region=europe"},
    {"name": "Jobicy Operations", "url": "https://jobicy.com/?feed=job_feed&job_category=business&job_region=europe"},
]

ADZUNA_SEARCHES = [
    {"country": "gb", "keywords": "insurance operations manager remote"},
    {"country": "gb", "keywords": "underwriting operations remote"},
    {"country": "gb", "keywords": "claims operations remote"},
    {"country": "gb", "keywords": "reinsurance operations remote"},
    {"country": "gb", "keywords": "Guidewire business analyst remote"},
    {"country": "gb", "keywords": "Guidewire consultant remote"},
    {"country": "gb", "keywords": "insurance programme manager remote"},
    {"country": "gb", "keywords": "bordereaux insurance remote"},
    {"country": "gb", "keywords": "delegated authority insurance remote"},
    {"country": "gb", "keywords": "business analyst insurance remote"},
    {"country": "gb", "keywords": "senior business analyst insurance remote"},
    {"country": "gb", "keywords": "technical business analyst insurance remote"},
    {"country": "gb", "keywords": "business analyst insurtech remote"},
    {"country": "gb", "keywords": "business analyst fintech remote"},
    {"country": "gb", "keywords": "digital transformation insurance remote"},
    {"country": "gb", "keywords": "transformation consultant insurance remote"},
    {"country": "gb", "keywords": "insurance consultant business analyst remote"},
    {"country": "gb", "keywords": "implementation consultant insurance remote"},
    {"country": "gb", "keywords": "process analyst insurance remote"},
    {"country": "gb", "keywords": "AI automation consultant remote"},
    {"country": "gb", "keywords": "AI automation consultant insurance"},
    {"country": "gb", "keywords": "AI consultant insurance remote"},
    {"country": "gb", "keywords": "AI implementation consultant remote"},
    {"country": "gb", "keywords": "intelligent automation consultant insurance"},
    {"country": "gb", "keywords": "AI governance financial services remote"},
    {"country": "es", "keywords": "business analyst insurance remote"},
    {"country": "es", "keywords": "consultor inteligencia artificial seguros"},
    {"country": "es", "keywords": "consultor transformacion digital seguros"},
    {"country": "es", "keywords": "Guidewire insurance consultant"},
    {"country": "de", "keywords": "insurance business analyst remote"},
    {"country": "de", "keywords": "transformation consultant insurance"},
    {"country": "de", "keywords": "insurance operations remote"},
    {"country": "fr", "keywords": "business analyst assurance remote"},
    {"country": "fr", "keywords": "consultant transformation assurance"},
    {"country": "nl", "keywords": "insurance business analyst remote"},
]


def fetch(url: str, timeout: int = 20):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code == 200:
            return response
        print(f"    fetch skipped {response.status_code}: {url[:90]}")
    except Exception as exc:
        print(f"    fetch error: {str(exc)[:90]}")
    return None


def load_seen() -> set:
    try:
        with open(SEEN_FILE, encoding="utf-8") as file:
            return set(json.load(file))
    except Exception:
        return set()


def save_seen(seen: Iterable[str]) -> None:
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as file:
            json.dump(sorted(seen), file, indent=2)
    except Exception as exc:
        print(f"  save_seen error: {exc}")


def job_id(title: str, company: str, link: str = "") -> str:
    raw = f"{title}|{company}|{link}".lower().encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:16]


def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw in lower]


def has_any(text: str, keywords: Iterable[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def is_ba_or_consulting_context(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in TARGET_KEYWORD_GROUPS["ba_transformation"] + [
        "consultant", "consulting", "transformation", "implementation", "business analyst",
    ])


def is_pure_ai_engineering(text: str) -> bool:
    lower = text.lower()
    has_pure_ai_title = any(kw in lower for kw in PURE_AI_ENGINEERING_KEYWORDS)
    has_context = any(kw in lower for kw in CONSULTING_OR_DOMAIN_CONTEXT)
    return has_pure_ai_title and not has_context


def explicit_salary_below_floor(text: str) -> bool:
    """Best-effort salary floor check. Only rejects explicit annual salary below MIN_SALARY_EUR."""
    lower = text.lower().replace(",", "")
    patterns = [
        r"€\s?(\d{2,3})\s?k",
        r"eur\s?(\d{2,3})\s?k",
        r"(\d{2,3})\s?k\s?€",
        r"(\d{5,6})\s?eur",
        r"€\s?(\d{5,6})",
    ]
    values = []
    for pattern in patterns:
        for match in re.findall(pattern, lower):
            value = int(match)
            if value < 1000:
                value *= 1000
            values.append(value)
    return bool(values) and max(values) < MIN_SALARY_EUR


def is_eu_eligible(location_text: str, description_text: str = "") -> Tuple[bool, str]:
    loc = (location_text or "").lower()
    desc = (description_text or "").lower()
    combined = f"{loc} {desc}"

    if any(pattern in combined for pattern in US_ONLY_PATTERNS):
        return False, "us_only"
    if any(pattern in combined for pattern in MADRID_HARD_BLOCKERS):
        return False, "madrid_presencial_blocked"
    if "madrid" in loc and not any(remote in combined for remote in EU_REMOTE_KEYWORDS):
        return False, "madrid_presencial_blocked"

    if any(region in combined for region in EU_REGION_KEYWORDS) and any(remote in combined for remote in EU_REMOTE_KEYWORDS):
        return True, "remote_eu_or_emea"
    if any(remote in combined for remote in EU_REMOTE_KEYWORDS) and not any(pattern in combined for pattern in US_ONLY_PATTERNS):
        return True, "remote_unspecified_or_global"
    if "barcelona" in loc:
        return True, "barcelona_hybrid_or_local"
    if any(city in loc for city in EU_CITIES):
        if is_ba_or_consulting_context(combined) and any(word in combined for word in RELOCATION_KEYWORDS + ["consultant", "business analyst", "transformation"]):
            return True, f"eu_relocation_or_hybrid_ba:{location_text}"
        return True, f"eu_location:{location_text}"
    if not loc or loc in {"anywhere", "worldwide", "global", "remote"}:
        return True, "remote_unspecified_or_global"
    return False, "not_eu"


def is_relevant(text: str) -> Tuple[bool, List[str]]:
    lower = text.lower()
    if any(negative in lower for negative in NEGATIVE_ROLE_KEYWORDS):
        return False, ["negative_role_keyword"]
    if is_pure_ai_engineering(lower):
        return False, ["pure_ai_engineering_without_domain_or_consulting_context"]

    hits = []
    groups_hit = set()
    for group, keywords in TARGET_KEYWORD_GROUPS.items():
        group_hits = keyword_hits(lower, keywords)
        if group_hits:
            groups_hit.add(group)
            hits.extend(group_hits[:5])

    if groups_hit & {"insurance_ops", "platforms"}:
        return True, hits
    if "ba_transformation" in groups_hit:
        return True, hits
    if "ai_consulting" in groups_hit and (groups_hit & {"domain", "insurance_ops", "platforms", "ba_transformation"}):
        return True, hits
    if any(term in lower for term in ["ai governance", "responsible ai", "eu ai act", "ai compliance", "dora"]):
        return True, hits

    return False, hits


def normalize_job(title: str, company: str, link: str, description: str, location: str, source: str, salary: str = "") -> Dict:
    return {
        "title": title or "Untitled role",
        "company": company or "Unknown company",
        "link": link or "",
        "description": (description or "")[:1200],
        "location": location or "Unspecified",
        "source": source,
        "salary": salary or "",
    }


def scrape_ashby() -> List[Dict]:
    jobs = []
    for company in ASHBY_COMPANIES:
        response = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{company['client']}?includeCompensation=true")
        if not response:
            continue
        try:
            for item in response.json().get("jobs", []):
                if not item.get("isListed", True):
                    continue
                title = item.get("title", "")
                location = item.get("location", "")
                description = item.get("descriptionPlain", "")
                combined_desc = f"{item.get('workplaceType', '')} {description}"
                eligible, _ = is_eu_eligible(location, combined_desc)
                relevant, _ = is_relevant(f"{title} {company['name']} {combined_desc}")
                if eligible and relevant:
                    compensation = item.get("compensation") or {}
                    salary = compensation.get("compensationTierSummary") or compensation.get("scrapeableCompensationSalarySummary") or ""
                    jobs.append(normalize_job(title, company["name"], item.get("jobUrl", ""), description, location, "Ashby", salary))
        except Exception as exc:
            print(f"  Ashby {company['name']} error: {exc}")
    print(f"  Ashby: {len(jobs)} relevant EU-eligible jobs")
    return jobs


def scrape_greenhouse() -> List[Dict]:
    jobs = []
    for company in GREENHOUSE_COMPANIES:
        response = fetch(f"https://api.greenhouse.io/v1/boards/{company['client']}/jobs?content=true")
        if not response:
            continue
        try:
            for item in response.json().get("jobs", []):
                title = item.get("title", "")
                location = (item.get("location") or {}).get("name", "")
                description = re.sub("<[^>]+>", " ", item.get("content", ""))
                eligible, _ = is_eu_eligible(location, description)
                relevant, _ = is_relevant(f"{title} {company['name']} {description}")
                if eligible and relevant:
                    jobs.append(normalize_job(title, company["name"], item.get("absolute_url", ""), description, location, "Greenhouse"))
        except Exception as exc:
            print(f"  Greenhouse {company['name']} error: {exc}")
    print(f"  Greenhouse: {len(jobs)} relevant EU-eligible jobs")
    return jobs


def scrape_lever() -> List[Dict]:
    jobs = []
    for company in LEVER_COMPANIES:
        response = fetch(f"https://api.lever.co/v0/postings/{company['client']}?mode=json")
        if not response:
            continue
        try:
            for item in response.json():
                title = item.get("text", "")
                categories = item.get("categories") or {}
                location = categories.get("location", "")
                description = item.get("descriptionPlain", "")
                eligible, _ = is_eu_eligible(location, description)
                relevant, _ = is_relevant(f"{title} {company['name']} {description}")
                if eligible and relevant:
                    jobs.append(normalize_job(title, company["name"], item.get("hostedUrl", ""), description, location, "Lever"))
        except Exception as exc:
            print(f"  Lever {company['name']} error: {exc}")
    print(f"  Lever: {len(jobs)} relevant EU-eligible jobs")
    return jobs


def scrape_remotive() -> List[Dict]:
    jobs = []
    for category in REMOTIVE_CATEGORIES:
        response = fetch(f"https://remotive.com/api/remote-jobs?category={category}&limit=80")
        if not response:
            continue
        try:
            for item in response.json().get("jobs", []):
                title = item.get("title", "")
                company = item.get("company_name", "")
                description = re.sub("<[^>]+>", " ", item.get("description", ""))
                location = item.get("candidate_required_location", "Remote")
                eligible, _ = is_eu_eligible(location, description)
                relevant, _ = is_relevant(f"{title} {company} {description}")
                if eligible and relevant:
                    jobs.append(normalize_job(title, company, item.get("url", ""), description, location, "Remotive", item.get("salary", "")))
        except Exception as exc:
            print(f"  Remotive {category} error: {exc}")
    print(f"  Remotive: {len(jobs)} relevant jobs")
    return jobs


def scrape_rss() -> List[Dict]:
    jobs = []
    for feed in WORKING_RSS:
        response = fetch(feed["url"])
        if not response:
            continue
        try:
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                description = re.sub("<[^>]+>", " ", item.findtext("description") or "")
                link = (item.findtext("link") or "").strip()
                relevant, _ = is_relevant(f"{title} {description}")
                if relevant:
                    jobs.append(normalize_job(title, feed["name"], link, description, "Remote", feed["name"]))
        except Exception as exc:
            print(f"  RSS {feed['name']} error: {exc}")
    print(f"  RSS: {len(jobs)} relevant jobs")
    return jobs


def scrape_adzuna() -> List[Dict]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("  Adzuna: skipped because ADZUNA_APP_ID / ADZUNA_APP_KEY are not set")
        return []
    jobs = []
    seen = set()
    for search in ADZUNA_SEARCHES:
        country = search["country"]
        keywords = requests.utils.quote(search["keywords"])
        url = (
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
            f"&results_per_page=30&what={keywords}&content-type=application/json"
        )
        response = fetch(url)
        if not response:
            continue
        try:
            for item in response.json().get("results", []):
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "")
                location = (item.get("location") or {}).get("display_name", "")
                description = item.get("description", "")
                link = item.get("redirect_url", "")
                dedup = job_id(title, company, link)
                if dedup in seen:
                    continue
                seen.add(dedup)
                eligible, _ = is_eu_eligible(location, description)
                relevant, _ = is_relevant(f"{title} {company} {description}")
                if eligible and relevant:
                    salary = ""
                    if item.get("salary_min") or item.get("salary_max"):
                        salary = f"£/€{int(item.get('salary_min') or 0):,}-{int(item.get('salary_max') or 0):,}"
                    jobs.append(normalize_job(title, company, link, description, location, f"Adzuna-{country.upper()}", salary))
        except Exception as exc:
            print(f"  Adzuna {country}/{search['keywords']} error: {exc}")
    print(f"  Adzuna: {len(jobs)} relevant EU-eligible jobs across {len(ADZUNA_SEARCHES)} searches")
    return jobs


def scrape_career_pages() -> List[Dict]:
    hints = []
    all_keywords = sorted({kw for kws in TARGET_KEYWORD_GROUPS.values() for kw in kws})
    for company in CAREER_PAGES:
        response = fetch(company["url"], timeout=15)
        if not response:
            continue
        text = response.text.lower()
        hits = [kw for kw in all_keywords if kw in text]
        geo_hit = any(word in text for word in ["remote", "spain", "barcelona", "europe", "emea", "hybrid", "relocation"])
        if hits and geo_hit:
            hints.append(normalize_job(
                f"Relevant hiring signals at {company['name']}",
                company["name"],
                company["url"],
                f"Keywords found: {', '.join(hits[:12])}. Manual check recommended.",
                "Check page",
                "Career Page",
            ))
    print(f"  Career pages: {len(hints)} companies with relevant signals")
    return hints


def deterministic_score(job: Dict) -> Dict:
    text = f"{job['title']} {job['company']} {job['location']} {job['salary']} {job['description']}".lower()
    score = 30
    reasons = []

    for group, bonus in [
        ("insurance_ops", 24),
        ("platforms", 22),
        ("ba_transformation", 26),
        ("ai_consulting", 18),
        ("domain", 12),
    ]:
        hits = keyword_hits(text, TARGET_KEYWORD_GROUPS[group])
        if hits:
            score += bonus
            reasons.append(f"{group}: {', '.join(hits[:3])}")

    bonus_hits = []
    for keyword, bonus in BONUS_KEYWORDS.items():
        if keyword in text:
            score += bonus
            bonus_hits.append(keyword)
    if bonus_hits:
        reasons.append(f"priority bonus: {', '.join(bonus_hits[:3])}")

    eligible, loc_type = is_eu_eligible(job.get("location", ""), job.get("description", ""))
    if not eligible:
        score = 0
        reasons.append(f"location rejected: {loc_type}")
    elif loc_type in {"remote_eu_or_emea", "barcelona_hybrid_or_local"}:
        score += 8
        reasons.append(f"location: {loc_type}")
    elif loc_type.startswith("eu_relocation_or_hybrid_ba"):
        score += 5
        reasons.append("location: EU relocation/hybrid acceptable for BA/consulting")

    if is_pure_ai_engineering(text):
        score -= 35
        reasons.append("penalty: pure AI/LLM engineering without domain or consulting context")
    elif has_any(text, PURE_AI_ENGINEERING_KEYWORDS) and has_any(text, CONSULTING_OR_DOMAIN_CONTEXT):
        score -= 10
        reasons.append("minor penalty: AI engineering title, but has domain/consulting context")

    if any(negative in text for negative in NEGATIVE_ROLE_KEYWORDS):
        score = 0
        reasons.append("junior/sales/research negative keyword")

    if explicit_salary_below_floor(text):
        score = 0
        reasons.append(f"explicit salary below €{MIN_SALARY_EUR:,} floor")

    score = max(0, min(score, 98))
    return {
        "score": score,
        "reason": "; ".join(reasons[:4]) or "Relevant keywords detected.",
        "location_type": loc_type,
        "salary_info": job.get("salary") or "not specified",
    }


def score_job(job: Dict) -> Dict:
    fallback = deterministic_score(job)
    if not ANTHROPIC_API_KEY:
        return fallback

    prompt = f"""Score this job for Marc Planas from 0-100.

Marc target:
- EU-wide insurance operations, Business Analyst, digital transformation, implementation consultant and AI automation consultant roles.
- Accept: 100% remote EU/Europe/EMEA, remote global if EU-eligible, Barcelona hybrid, and European relocation/hybrid for strong BA/consulting roles.
- Hard reject: Madrid presencial, US-only, junior/graduate/intern, pure sales, pure ML research.
- Salary floor: explicit salary below EUR {MIN_SALARY_EUR} is a reject; missing salary is acceptable.
- Strong bonus: Business Analyst, Transformation Consultant, Insurance Consultant, AI Automation Consultant, Guidewire Business Analyst/Consultant.
- Penalize: pure AI Engineer / LLM Engineer roles unless they clearly involve consulting, operations, insurance, financial services, governance, implementation or workflow automation.

Job title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Salary: {job.get('salary', '') or 'not specified'}
Description: {job['description'][:1100]}

Return only JSON: {{"score": int, "reason": "one sentence", "location_type": "remote_eu|remote_emea|barcelona_hybrid|eu_relocation_ba_consulting|us_only|madrid_presencial|onsite_rejected|unclear", "salary_info": "salary or not specified"}}
"""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 350,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if response.status_code != 200:
            print(f"    Claude scoring skipped: HTTP {response.status_code}")
            return fallback
        content = response.json().get("content") or []
        text = (content[0].get("text", "") if content else "").replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        return {**fallback, **parsed}
    except Exception as exc:
        print(f"    Claude scoring fallback used: {exc}")
        return fallback


def log_to_tracker(job: Dict, result: Dict) -> None:
    try:
        exists = os.path.exists(TRACKER_FILE)
        with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not exists:
                writer.writerow(["Date", "Title", "Company", "Source", "Score", "Location", "Salary", "Reason", "Link", "Status"])
            writer.writerow([
                TODAY,
                job.get("title", ""),
                job.get("company", ""),
                job.get("source", ""),
                result.get("score", ""),
                result.get("location_type", ""),
                result.get("salary_info", ""),
                result.get("reason", ""),
                job.get("link", ""),
                "New",
            ])
    except Exception as exc:
        print(f"  tracker write error: {exc}")


def send_email(matches: List[Dict], hints: List[Dict]) -> None:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("⚠️ Email skipped because SMTP_USER / SMTP_PASS are not configured.")
        return
    if not matches and not hints:
        print("No matches or hints to email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(matches)} Job Match(es) — EU BA / Ops / AI Consulting — {TODAY}"
    msg["From"] = f"EU Job Monitor <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER

    rows = []
    for job in matches:
        result = job.get("ai_result", {})
        rows.append(
            f"<li><b><a href='{html.escape(job['link'])}'>{html.escape(job['title'])}</a></b> "
            f"@ {html.escape(job['company'])} — {result.get('score', '?')}%<br>"
            f"<small>{html.escape(job.get('source', ''))} · {html.escape(job.get('location', ''))} · "
            f"{html.escape(result.get('location_type', ''))} · {html.escape(result.get('reason', ''))}</small></li>"
        )
    hint_rows = [f"<li><a href='{html.escape(h['link'])}'>{html.escape(h['company'])}</a> — {html.escape(h['description'])}</li>" for h in hints]

    body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 760px;">
      <h2>EU Insurance / BA / AI Consulting Job Monitor</h2>
      <p><b>Scope:</b> insurance ops / Guidewire / claims / underwriting / reinsurance + BA / transformation + AI automation consulting.</p>
      <p><b>Location policy:</b> remote EU/EMEA, Barcelona hybrid, and EU relocation/hybrid for strong BA/consulting roles. Madrid presencial and US-only are blocked.</p>
      <p><b>Salary floor:</b> explicit salaries below €{MIN_SALARY_EUR:,} are rejected; missing salary is still considered.</p>
      <h3>Scored matches</h3>
      <ol>{''.join(rows) or '<li>No scored matches above threshold.</li>'}</ol>
      <h3>Career pages worth manual checking</h3>
      <ul>{''.join(hint_rows) or '<li>No manual-check signals.</li>'}</ul>
      <p style="font-size:12px;color:#777;">{TODAY} · Minimum score {PROFILE.get('min_match_score', 50)}%</p>
    </body></html>
    """
    plain = "\n".join([f"{j['title']} @ {j['company']} — {j.get('link', '')}" for j in matches])
    msg.attach(MIMEText(plain or "No scored matches above threshold.", "plain"))
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Email sent: {len(matches)} matches, {len(hints)} hints")
    except Exception as exc:
        print(f"❌ Email error: {exc}")


def main() -> None:
    print(f"\n{'=' * 78}")
    print(f"  EU Insurance Remote Job Monitor v5.1 — {TODAY}")
    print("  Scope: Ops/Guidewire + BA/Transformation/Consulting + AI Automation Consultant")
    print("  Location: Remote EU/EMEA + Barcelona hybrid + EU relocation for strong BA/consulting")
    print(f"  Salary floor: €{MIN_SALARY_EUR:,} explicit minimum")
    print(f"{'=' * 78}\n")

    seen = load_seen()
    all_jobs: List[Dict] = []
    for scraper in [scrape_ashby, scrape_greenhouse, scrape_lever, scrape_remotive, scrape_rss, scrape_adzuna]:
        all_jobs.extend(scraper())
    hints = scrape_career_pages()

    deduped = []
    current_run_seen = set()
    for job in all_jobs:
        identifier = job_id(job["title"], job["company"], job.get("link", ""))
        if identifier in current_run_seen:
            continue
        current_run_seen.add(identifier)
        if identifier not in seen:
            seen.add(identifier)
            deduped.append(job)

    print(f"\n📊 Relevant listings found: {len(all_jobs)}")
    print(f"🆕 New listings not seen before: {len(deduped)}")
    print(f"📋 Career page hints: {len(hints)}")

    matches = []
    threshold = int(PROFILE.get("min_match_score", 50))
    for job in deduped:
        result = score_job(job)
        job["ai_result"] = result
        score = int(result.get("score", 0))
        emoji = "🎯" if score >= 85 else "✅" if score >= 70 else "👀" if score >= threshold else "➖"
        print(f"  {emoji} {score:3d}% — {job['title']} @ {job['company']} [{job['source']}] — {result.get('location_type', '')}")
        if score >= threshold:
            log_to_tracker(job, result)
            matches.append(job)

    print(f"\n🏆 Matches above {threshold}%: {len(matches)}")
    if matches or hints:
        send_email(matches, hints)
    save_seen(seen)
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
