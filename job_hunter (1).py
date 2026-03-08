import requests
from bs4 import BeautifulSoup
import json
import os
import re
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from marc_profile import PROFILE

# ── Config ───────────────────────────────────────────────────────────────────
RECIPIENT_EMAIL   = "marcplanas11@gmail.com"
SENDER_EMAIL      = os.environ["GMAIL_USER"]
SENDER_PASSWORD   = os.environ["GMAIL_APP_PASSWORD"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEEN_JOBS_FILE    = "seen_hunted_jobs.json"
MATCH_THRESHOLD   = 80   # Only jobs scoring 80%+ get through

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Job Sources ───────────────────────────────────────────────────────────────

def fetch(url, delay=1):
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠️  Could not fetch {url}: {e}")
        return ""

def scrape_indeed():
    """Indeed RSS feed for insurtech jobs in Europe"""
    jobs = []
    queries = [
        "https://www.indeed.com/rss?q=insurtech+operations&l=Remote&sort=date",
        "https://www.indeed.com/rss?q=insurance+operations+manager&l=Europe&sort=date",
        "https://www.indeed.com/rss?q=MGA+operations&l=Remote&sort=date",
        "https://www.indeed.com/rss?q=insurtech+product+manager&l=Remote&sort=date",
        "https://es.indeed.com/rss?q=insurtech+operaciones&sort=date",
    ]
    for url in queries:
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "xml")
        for item in soup.find_all("item")[:10]:
            title   = item.find("title").get_text(strip=True) if item.find("title") else ""
            link    = item.find("link").get_text(strip=True) if item.find("link") else ""
            desc    = item.find("description").get_text(strip=True) if item.find("description") else ""
            company = item.find("source").get_text(strip=True) if item.find("source") else "Unknown"
            if title:
                jobs.append({
                    "title": title, "company": company,
                    "url": link, "description": desc[:1000],
                    "source": "Indeed"
                })
    return jobs

def scrape_linkedin():
    """LinkedIn public job search"""
    jobs = []
    searches = [
        "https://www.linkedin.com/jobs/search/?keywords=insurtech%20operations&location=Europe&f_WT=2&sortBy=DD",
        "https://www.linkedin.com/jobs/search/?keywords=insurance%20operations%20manager&location=Remote&f_WT=2&sortBy=DD",
        "https://www.linkedin.com/jobs/search/?keywords=MGA%20operations%20insurance&location=Europe&sortBy=DD",
        "https://www.linkedin.com/jobs/search/?keywords=insurtech%20consultant&location=Europe&sortBy=DD",
        "https://www.linkedin.com/jobs/search/?keywords=insurance%20product%20operations&location=Barcelona&sortBy=DD",
    ]
    for url in searches:
        html = fetch(url, delay=2)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".base-card, .job-search-card, [class*='job-card']"):
            title_el   = card.select_one(".base-card__full-link, .job-card-list__title, h3")
            company_el = card.select_one(".base-card__subtitle, .job-card-container__company-name, h4")
            link_el    = card.select_one("a[href*='linkedin.com/jobs']")
            desc_el    = card.select_one(".base-card__metadata, p")
            if title_el:
                jobs.append({
                    "title":       title_el.get_text(strip=True),
                    "company":     company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":         link_el["href"] if link_el else url,
                    "description": desc_el.get_text(strip=True)[:500] if desc_el else "",
                    "source":      "LinkedIn"
                })
    return jobs

def scrape_glassdoor():
    """Glassdoor job search"""
    jobs = []
    searches = [
        "https://www.glassdoor.com/Job/europe-insurtech-jobs-SRCH_IL.0,6_IN1_KO7,16.htm",
        "https://www.glassdoor.com/Job/remote-insurance-operations-jobs-SRCH_IL.0,6_IS11047_KO7,27.htm",
    ]
    for url in searches:
        html = fetch(url, delay=2)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='jobCard'], [data-test='job-link'], .react-job-listing"):
            title_el   = card.select_one("[class*='title'], [data-test='job-title'], h2, h3")
            company_el = card.select_one("[class*='employer'], [data-test='employer-name']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.glassdoor.com" + href
                jobs.append({
                    "title":       title_el.get_text(strip=True),
                    "company":     company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":         href,
                    "description": card.get_text(strip=True)[:500],
                    "source":      "Glassdoor"
                })
    return jobs

def scrape_recruiters():
    """Specialist insurtech & insurance recruiters"""
    jobs = []
    recruiter_sites = [
        # Insurance specialist recruiters
        ("Barclay Simpson",      "https://www.barclaysimpson.com/jobs/?sector=insurance&work_type=remote"),
        ("Idex Consulting",      "https://www.idexconsulting.com/jobs/?sector=insurance"),
        ("Sellick Partnership",  "https://www.sellickpartnership.co.uk/jobs/?sector=insurance"),
        ("Talentspa Insurance",  "https://www.talentspa.co.uk/jobs/insurance/"),
        ("Marks Sattin",         "https://www.markssattin.co.uk/jobs/insurance/"),
        ("JM Maguire",           "https://www.jmmaguire.co.uk/vacancies/"),
        ("Hanover Insurance",    "https://www.hanoverinsurance.co.uk/jobs/"),
        ("Heat Recruitment",     "https://www.heatrecruitment.co.uk/jobs/insurance/"),
        ("Paul Bridges Group",   "https://www.paulbridgesgroup.com/vacancies/"),
        ("Cactus Search",        "https://www.cactussearch.co.uk/jobs/"),
        # European / Spanish recruiters
        ("Michael Page ES",      "https://www.michaelpage.es/empleo/seguros-banca-finanzas"),
        ("Robert Walters ES",    "https://www.robertwalters.es/jobs/search.html?query=insurance"),
        ("Hays Spain",           "https://www.hays.es/empleo/busqueda-empleo?q=seguros"),
        # Insurtech specific
        ("InsTech Foundry",      "https://www.instech.ie/meet-the-insurtechs"),
        ("Wellfound Insurtech",  "https://wellfound.com/jobs?role=insurance&remote=true"),
    ]
    for recruiter_name, url in recruiter_sites:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("article, .job, .vacancy, li[class*='job'], [class*='job-item']"):
            title_el = card.select_one("h2, h3, h4, .job-title, [class*='title']")
            link_el  = card.select_one("a")
            if title_el and len(title_el.get_text(strip=True)) > 5:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = url.split("/jobs")[0] + href
                jobs.append({
                    "title":       title_el.get_text(strip=True),
                    "company":     recruiter_name,
                    "url":         href,
                    "description": card.get_text(strip=True)[:500],
                    "source":      f"Recruiter: {recruiter_name}"
                })
    return jobs

def scrape_insurtech_companies():
    """Direct career pages of top European insurtechs"""
    jobs = []
    company_sites = [
        ("Alan",              "https://alan.com/en/careers"),
        ("wefox",             "https://www.wefox.com/careers"),
        ("Kota",              "https://jobs.ashbyhq.com/kota"),
        ("Lassie",            "https://lassie.se/en/careers"),
        ("Descartes UW",      "https://careers.descartesunderwriting.com/jobs"),
        ("Inaza",             "https://www.inaza.com/careers"),
        ("Blink Parametric",  "https://www.blinkparametric.com/careers"),
        ("Kayna",             "https://www.kayna.io/careers"),
        ("Qover",             "https://www.qover.com/careers"),
        ("Wakam",             "https://www.wakam.com/en/careers"),
        ("Shift Technology",  "https://www.shift-technology.com/careers/"),
        ("Friss",             "https://www.friss.com/careers"),
        ("Tractable",         "https://tractable.ai/careers/"),
        ("Cytora",            "https://www.cytora.com/careers"),
        ("Hyperexponential",  "https://hyperexponential.com/careers"),
        ("Artificial Labs",   "https://www.artificial.io/careers"),
        ("EbaoTech",          "https://www.ebaotech.com/careers"),
        ("Socotra",           "https://www.socotra.com/company/careers"),
        ("FINEOS",            "https://careers.fineos.com/viewalljobs/"),
        ("DOCOsoft",          "https://www.docosoft.com/careers/"),
        ("Gamma Risk",        "https://www.gammarisk.com/careers"),
        ("Zywave",            "https://www.zywave.com/careers/"),
        ("Applied Systems",   "https://www1.appliedsystems.com/en-us/about/careers/"),
        ("Verisk",            "https://careers.verisk.com/"),
    ]
    for company_name, url in company_sites:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("a[href*='job'], a[href*='career'], a[href*='position'], a[href*='role'], li, [class*='job'], [class*='position']"):
            text = card.get_text(strip=True)
            href = card.get("href", "") if card.name == "a" else ""
            if not href:
                link = card.find("a")
                href = link.get("href", "") if link else url
            if 10 < len(text) < 150:
                if not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href.lstrip("/")
                jobs.append({
                    "title":       text,
                    "company":     company_name,
                    "url":         href,
                    "description": text,
                    "source":      f"Company: {company_name}"
                })
    return jobs

def scrape_remote_boards():
    """Remote-first and digital nomad job boards"""
    jobs = []

    # ── We Work Remotely ─────────────────────────────────────────────────────
    # Has RSS feeds — most reliable
    wwr_feeds = [
        ("https://weworkremotely.com/remote-jobs/search.rss?term=insurance+operations", "We Work Remotely"),
        ("https://weworkremotely.com/remote-jobs/search.rss?term=insurtech",             "We Work Remotely"),
        ("https://weworkremotely.com/remote-jobs/search.rss?term=insurance+manager",     "We Work Remotely"),
    ]
    for url, source in wwr_feeds:
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "xml")
        for item in soup.find_all("item"):
            title   = item.find("title").get_text(strip=True) if item.find("title") else ""
            link    = item.find("link").get_text(strip=True) if item.find("link") else ""
            desc    = item.find("description").get_text(strip=True) if item.find("description") else ""
            company = item.find("company_name")
            company = company.get_text(strip=True) if company else "Unknown"
            if title:
                jobs.append({"title": title, "company": company,
                             "url": link, "description": desc[:600], "source": source})

    # ── Remote OK ────────────────────────────────────────────────────────────
    # JSON API — very reliable
    remoteok_queries = [
        "https://remoteok.com/api?tag=insurance",
        "https://remoteok.com/api?tag=fintech",
        "https://remoteok.com/api?tag=operations",
    ]
    for url in remoteok_queries:
        try:
            time.sleep(1)
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=20)
            data = r.json()
            for item in data[1:20]:   # first item is metadata
                if not isinstance(item, dict):
                    continue
                title   = item.get("position", "")
                company = item.get("company", "Unknown")
                link    = item.get("url", "https://remoteok.com")
                desc    = item.get("description", "")[:600]
                if title:
                    jobs.append({"title": title, "company": company,
                                 "url": link, "description": desc, "source": "Remote OK"})
        except Exception as e:
            print(f"  ⚠️  Remote OK error: {e}")

    # ── Himalayas ────────────────────────────────────────────────────────────
    himalaya_searches = [
        "https://himalayas.app/jobs/remote?q=insurance+operations",
        "https://himalayas.app/jobs/remote?q=insurtech",
        "https://himalayas.app/jobs/remote?q=insurance+manager",
    ]
    for url in himalaya_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='job'], article, li[class*='position']"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company'], [class*='employer']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://himalayas.app" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Himalayas"
                })

    # ── EuroRemote / EU Remote ───────────────────────────────────────────────
    euroremote_searches = [
        "https://euroremote.io/jobs?q=insurance",
        "https://euroremote.io/jobs?q=insurtech",
        "https://euroremote.io/jobs?q=operations",
    ]
    for url in euroremote_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("article, [class*='job-card'], [class*='listing']"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://euroremote.io" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "EuroRemote"
                })

    # ── Jobgether (EU remote focus) ──────────────────────────────────────────
    jobgether_searches = [
        "https://jobgether.com/search?q=insurance+operations&remote=true",
        "https://jobgether.com/search?q=insurtech&remote=true",
    ]
    for url in jobgether_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='job'], article"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://jobgether.com" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Jobgether"
                })

    # ── Wellfound (AngelList) ─────────────────────────────────────────────────
    wellfound_searches = [
        "https://wellfound.com/jobs?q=insurance+operations&remote=true",
        "https://wellfound.com/jobs?q=insurtech&remote=true",
    ]
    for url in wellfound_searches:
        html = fetch(url, delay=2)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='job'], [data-test*='job']"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://wellfound.com" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Wellfound"
                })

    # ── Otta (London / EU tech) ──────────────────────────────────────────────
    otta_searches = [
        "https://app.otta.com/jobs/search?query=insurance+operations",
        "https://app.otta.com/jobs/search?query=insurtech",
    ]
    for url in otta_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='JobCard'], article"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://app.otta.com" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Otta"
                })

    # ── Remotive ─────────────────────────────────────────────────────────────
    # JSON API
    try:
        time.sleep(1)
        r = requests.get(
            "https://remotive.com/api/remote-jobs?search=insurance&limit=30",
            headers=HEADERS, timeout=20
        )
        data = r.json()
        for item in data.get("jobs", []):
            jobs.append({
                "title":       item.get("title", ""),
                "company":     item.get("company_name", "Unknown"),
                "url":         item.get("url", "https://remotive.com"),
                "description": BeautifulSoup(item.get("description", ""), "html.parser").get_text()[:600],
                "source":      "Remotive"
            })
    except Exception as e:
        print(f"  ⚠️  Remotive API error: {e}")

    # ── NoDesk (remote-only niche board) ─────────────────────────────────────
    nodesk_searches = [
        "https://nodesk.co/remote-jobs/?search=insurance",
        "https://nodesk.co/remote-jobs/?search=operations",
    ]
    for url in nodesk_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("article, [class*='job']"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "NoDesk"
                })

    # ── Working Nomads ───────────────────────────────────────────────────────
    workingnomads_searches = [
        "https://www.workingnomads.com/jobs?category=management&remote=true",
        "https://www.workingnomads.com/jobs?category=business&remote=true",
    ]
    for url in workingnomads_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='job'], article, li"):
            title_el   = card.select_one("h2, h3, h4, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el and len(title_el.get_text(strip=True)) > 8:
                href = link_el["href"] if link_el else url
                if href and not href.startswith("http"):
                    href = "https://www.workingnomads.com" + href
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Working Nomads"
                })

    # ── Dynamite Jobs ────────────────────────────────────────────────────────
    dynamite_searches = [
        "https://dynamitejobs.com/remote-jobs?search=insurance+operations",
        "https://dynamitejobs.com/remote-jobs?search=insurtech",
    ]
    for url in dynamite_searches:
        html = fetch(url, delay=1)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("[class*='job'], article"):
            title_el   = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company']")
            link_el    = card.select_one("a")
            if title_el:
                href = link_el["href"] if link_el else url
                jobs.append({
                    "title":   title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "url":     href,
                    "description": card.get_text(strip=True)[:400],
                    "source":  "Dynamite Jobs"
                })

    print(f"     Remote boards total: {len(jobs)}")
    return jobs

# ── AI Matching ───────────────────────────────────────────────────────────────

def ai_score_and_match(job):
    """Use Claude API to score job against Marc's profile"""
    if not ANTHROPIC_API_KEY:
        return simple_score(job), "AI scoring unavailable — using keyword match"

    profile_summary = f"""
Name: {PROFILE['name']}
Current role: Operations Data Manager at Accelerant (Lloyd's MGA)
Years experience: 9+ years in insurance/insurtech
Background: Broker + Insurer. International programs, underwriting, operations, BPO, data
Skills: {', '.join(PROFILE['skills_technical'][:10])}
Languages: English (native), Spanish (native), French (advanced), Italian (intermediate)
Target roles: {', '.join(PROFILE['target_roles'][:6])}
Location: Barcelona, open to remote or EU
"""

    prompt = f"""You are a recruitment expert. Score this job opportunity for Marc on a scale of 0-100.

MARC'S PROFILE:
{profile_summary}

JOB OPPORTUNITY:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}
Description: {job['description'][:600]}

Respond in this EXACT JSON format only, no other text:
{{
  "score": <number 0-100>,
  "match_reasons": ["reason 1", "reason 2", "reason 3"],
  "concerns": ["concern 1"],
  "verdict": "one sentence summary"
}}

Score 80+ only if: role matches operations/product/consulting in insurance/insurtech AND seniority fits AND language fits."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        data = resp.json()
        text = data["content"][0]["text"].strip()
        # Clean JSON
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        return result.get("score", 0), result
    except Exception as e:
        print(f"  ⚠️  AI scoring failed: {e}")
        return simple_score(job), {"score": simple_score(job), "verdict": "Keyword match only"}

def simple_score(job):
    """Fallback keyword-based scoring"""
    text = (job["title"] + " " + job["description"] + " " + job["company"]).lower()
    score = 0
    high_value = ["insurtech", "mga", "lloyd", "operations", "underwriting", "insurance operations"]
    medium_value = ["insurance", "reinsurance", "claims", "broker", "product manager", "consultant"]
    low_value = ["remote", "europe", "barcelona", "fintech", "data"]
    for kw in high_value:
        if kw in text: score += 15
    for kw in medium_value:
        if kw in text: score += 8
    for kw in low_value:
        if kw in text: score += 5
    return min(score, 100)

# ── CV & Cover Letter Generation ─────────────────────────────────────────────

def generate_cv_and_letter(job, lang="en"):
    """Use Claude AI to generate tailored CV and cover letter"""
    if not ANTHROPIC_API_KEY:
        return generate_simple_cv(job, lang), generate_simple_letter(job, lang)

    lang_instruction = "in English" if lang == "en" else "in Spanish"
    lang_label = "English" if lang == "en" else "Spanish"

    prompt = f"""You are an expert CV writer. Create a tailored CV and cover letter {lang_instruction} for Marc Planas Callico applying to this specific role.

JOB:
Title: {job['title']}
Company: {job['company']}
Description: {job['description'][:800]}

MARC'S BACKGROUND:
- Current: Operations Data Manager at Accelerant (Lloyd's MGA) — April 2025 to present
  - Member onboarding, BDX gap analysis, BPO supervision, Solvency reports, data ingestion
- Sompo Insurance Spain: Underwriting Assistant French Market (Apr 2024 - Mar 2025)
  - Guidewire, French market ops, credit control, procedure manuals
- Zurich Seguros: International Business Consultant (Feb 2023 - Mar 2024)
  - International programs, co-insurance, reinsurance, OFAC/SDN sanctions compliance
- Confide: Account Executive International (Oct 2021 - Jan 2023)
  - 17 international programs, GL, D&O, Aviation, TOBA negotiations
- Riskmedia: Account Executive Media (Dec 2019 - Sep 2021)
  - Large accounts, GL, PL, Media Production, E&O
- Liberty Seguros: Expat Broker Underwriter (Aug 2016 - Nov 2019)
  - Personal lines, Salesforce CRM innovation award, broker support
- SegurCaixa: Claims Advisor (Mar 2015 - Jul 2016)
Skills: {', '.join(PROFILE['skills_technical'][:12])}
Languages: English (native), Spanish (native), French (advanced), Italian (intermediate)
Education: Certified Insurance Broker (ICEA 2022)
Contact: marcplanas11@gmail.com | +34 672 32 99 11 | Barcelona | linkedin.com/in/intlinsure

INSTRUCTIONS:
1. Tailor the CV to highlight experience most relevant to THIS specific job
2. Write a compelling cover letter that references the company by name
3. Keep CV to 1 page worth of content, cover letter to 3 paragraphs
4. Format as clean HTML with inline styles (will be sent as email attachment)
5. Make it professional and specific — not generic

Respond with EXACTLY this structure:
===CV_START===
[Full CV in HTML format]
===CV_END===
===LETTER_START===
[Full cover letter in HTML format]
===LETTER_END==="""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        data = resp.json()
        text = data["content"][0]["text"]

        cv_match     = re.search(r'===CV_START===(.*?)===CV_END===', text, re.DOTALL)
        letter_match = re.search(r'===LETTER_START===(.*?)===LETTER_END===', text, re.DOTALL)

        cv     = cv_match.group(1).strip() if cv_match else generate_simple_cv(job, lang)
        letter = letter_match.group(1).strip() if letter_match else generate_simple_letter(job, lang)
        return cv, letter
    except Exception as e:
        print(f"  ⚠️  CV generation failed: {e}")
        return generate_simple_cv(job, lang), generate_simple_letter(job, lang)

def generate_simple_cv(job, lang="en"):
    """Fallback HTML CV"""
    name  = PROFILE["name"]
    title = PROFILE["title"]
    today = datetime.today().strftime("%B %Y")
    return f"""<html><body style="font-family:Arial,sans-serif;max-width:750px;margin:auto;padding:30px">
<h1 style="color:#1a1a2e;margin-bottom:4px">{name}</h1>
<h3 style="color:#666;margin-top:0">{title}</h3>
<p>{PROFILE['email']} | {PROFILE['phone']} | Barcelona | {PROFILE['linkedin']}</p>
<hr/>
<h2>Professional Summary</h2>
<p>{PROFILE['summary_en'] if lang=='en' else PROFILE['summary_es']}</p>
<h2>Experience</h2>
{"".join(f"<h3>{e['title']} — {e['company']}</h3><p><em>{e['period']}</em></p><ul>{''.join(f'<li>{b}</li>' for b in e['bullets_en'])}</ul>" for e in PROFILE['experience'])}
<h2>Skills</h2><p>{' | '.join(PROFILE['skills_technical'])}</p>
<h2>Languages</h2><p>{' | '.join(f"{k}: {v}" for k,v in PROFILE['languages'].items())}</p>
<h2>Education</h2><ul>{"".join(f'<li>{e}</li>' for e in PROFILE['education'])}</ul>
</body></html>"""

def generate_simple_letter(job, lang="en"):
    """Fallback cover letter"""
    today = datetime.today().strftime("%d %B %Y")
    if lang == "en":
        return f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:30px">
<p>{today}</p>
<p>Dear Hiring Manager at {job['company']},</p>
<p>I am writing to express my strong interest in the <strong>{job['title']}</strong> position. 
With over 9 years of insurance and insurtech experience across broker and insurer environments — 
including my current role as Operations Data Manager at Accelerant, a Lloyd's MGA — I am confident 
I would bring immediate value to your team.</p>
<p>My background in international insurance programs, BDX data management, BPO supervision, 
underwriting operations, and multilingual client management (English, Spanish, French, Italian) 
aligns well with the requirements of this role. I am recognised as a high-performing professional 
with a track record of optimising processes and delivering results in fast-moving insurtech environments.</p>
<p>I would welcome the opportunity to discuss how my experience can contribute to {job['company']}'s 
goals. Please find my CV attached.</p>
<p>Kind regards,<br/><strong>Marc Planas Callico</strong><br/>
{PROFILE['email']} | {PROFILE['phone']}<br/>{PROFILE['linkedin']}</p>
</body></html>"""
    else:
        return f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:30px">
<p>{today}</p>
<p>Estimado equipo de selección de {job['company']},</p>
<p>Me dirijo a ustedes para expresar mi interés en el puesto de <strong>{job['title']}</strong>. 
Con más de 9 años de experiencia en seguros e insurtech, tanto en corredurías como en 
aseguradoras, y actualmente como Operations Data Manager en Accelerant (Lloyd's MGA), 
estoy seguro de poder aportar valor inmediato a su equipo.</p>
<p>Mi experiencia en programas internacionales de seguros, gestión de datos BDX, supervisión 
de BPO, operaciones de suscripción y gestión de clientes en múltiples idiomas (inglés, 
español, francés, italiano) se alinea directamente con los requisitos del puesto. 
Soy reconocido como un profesional de alto rendimiento con trayectoria probada en 
optimización de procesos en entornos insurtech de rápido crecimiento.</p>
<p>Quedará a su disposición para una entrevista donde pueda explicar cómo mi experiencia 
puede contribuir a los objetivos de {job['company']}. Adjunto mi currículum.</p>
<p>Atentamente,<br/><strong>Marc Planas Callico</strong><br/>
{PROFILE['email']} | {PROFILE['phone']}<br/>{PROFILE['linkedin']}</p>
</body></html>"""

# ── Email ─────────────────────────────────────────────────────────────────────

def send_job_email(matched_jobs):
    today = datetime.today().strftime('%d %b %Y')
    subject = f"🎯 {len(matched_jobs)} High-Match Insurtech Job(s) Found — {today}"

    job_cards = ""
    for item in matched_jobs:
        job   = item["job"]
        score = item["score"]
        info  = item.get("match_info", {})
        verdict = info.get("verdict", "") if isinstance(info, dict) else str(info)
        reasons = info.get("match_reasons", []) if isinstance(info, dict) else []
        reasons_html = "".join(f"<li style='color:#2d6a2d'>{r}</li>" for r in reasons[:3])

        job_cards += f"""
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <h3 style="margin:0;color:#1a1a2e">{job['title']}</h3>
            <span style="background:{'#2d6a2d' if score>=90 else '#1a5276'};color:white;
                         padding:4px 12px;border-radius:20px;font-weight:bold">{score}% match</span>
          </div>
          <p style="color:#666;margin:4px 0"><strong>{job['company']}</strong> · {job['source']}</p>
          <p style="color:#444;font-size:14px">{verdict}</p>
          {'<ul style="font-size:13px">' + reasons_html + '</ul>' if reasons_html else ''}
          <p style="font-size:13px;color:#555">{job['description'][:200]}...</p>
          <a href="{job['url']}" style="display:inline-block;background:#1a1a2e;color:white;
             padding:8px 18px;border-radius:6px;text-decoration:none;margin-top:8px">
            View Job & Apply →
          </a>
          <p style="font-size:11px;color:#999;margin-top:8px">
            📎 Tailored CV (EN/ES) + Cover Letter (EN/ES) attached below
          </p>
        </div>"""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:750px;margin:auto;padding:20px">
      <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:24px;border-radius:10px;margin-bottom:28px">
        <h1 style="color:#fff;margin:0;font-size:22px">🎯 Your Daily Insurtech Job Hunt</h1>
        <p style="color:#aaa;margin:8px 0 0">{today} · Sources: Indeed, LinkedIn, Glassdoor, Recruiters & Company Sites</p>
        <p style="color:#7fb3f5;margin:4px 0 0"><strong>{len(matched_jobs)} jobs scored 80%+</strong> out of all positions scanned today</p>
      </div>
      {job_cards}
      <p style="font-size:11px;color:#999;border-top:1px solid #eee;padding-top:16px;margin-top:24px">
        AI-powered job hunt by your GitHub Actions bot · marcplanas11@gmail.com<br/>
        Each matching job has a tailored CV and cover letter attached (EN + ES).
      </p>
    </body></html>"""

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    # Attach CV and cover letters for each job
    for i, item in enumerate(matched_jobs[:5], 1):   # Max 5 attachments
        job = item["job"]
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', job['title'])[:30]

        for lang, label in [("en", "EN"), ("es", "ES")]:
            cv_html, letter_html = generate_cv_and_letter(job, lang)

            # Attach CV
            cv_part = MIMEBase("text", "html")
            cv_part.set_payload(cv_html.encode("utf-8"))
            encoders.encode_base64(cv_part)
            cv_part.add_header("Content-Disposition", "attachment",
                               filename=f"CV_Marc_Planas_{safe_name}_{label}.html")
            msg.attach(cv_part)

            # Attach Cover Letter
            letter_part = MIMEBase("text", "html")
            letter_part.set_payload(letter_html.encode("utf-8"))
            encoders.encode_base64(letter_part)
            letter_part.add_header("Content-Disposition", "attachment",
                                   filename=f"CoverLetter_Marc_Planas_{safe_name}_{label}.html")
            msg.attach(letter_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email sent with {len(matched_jobs)} matched job(s) + attached CVs.")

# ── Core logic ────────────────────────────────────────────────────────────────

def load_seen():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def deduplicate(jobs):
    seen_titles = {}
    for job in jobs:
        key = f"{job['title'].lower()[:40]}|{job['company'].lower()[:20]}"
        if key not in seen_titles:
            seen_titles[key] = job
    return list(seen_titles.values())

def main():
    print(f"\n🎯 Running AI Job Hunter for Marc Planas — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Target: {MATCH_THRESHOLD}%+ match threshold\n")

    seen = load_seen()

    # Scrape all sources
    print("📡 Scraping job sources...")
    all_jobs = []
    sources = [
        ("Indeed",              scrape_indeed),
        ("LinkedIn",            scrape_linkedin),
        ("Glassdoor",           scrape_glassdoor),
        ("Recruiters",          scrape_recruiters),
        ("Insurtech Companies", scrape_insurtech_companies),
        ("Remote Boards",       scrape_remote_boards),
    ]
    for name, func in sources:
        print(f"  → Checking {name}...")
        try:
            jobs = func()
            print(f"     Found {len(jobs)} listings")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"     ⚠️ Error: {e}")

    # Deduplicate
    all_jobs = deduplicate(all_jobs)
    print(f"\n📊 Total unique jobs found: {len(all_jobs)}")

    # Filter already seen
    new_jobs = [j for j in all_jobs
                if f"{j['title'][:40]}|{j['company'][:20]}".lower() not in seen]
    print(f"🆕 New (unseen) jobs: {len(new_jobs)}")

    if not new_jobs:
        print("✅ No new jobs to evaluate today.")
        return

    # AI score each job
    print(f"\n🤖 AI scoring {len(new_jobs)} jobs against Marc's profile...")
    matched = []
    new_seen_keys = set()

    for job in new_jobs:
        key = f"{job['title'].lower()[:40]}|{job['company'].lower()[:20]}"
        score, match_info = ai_score_and_match(job)
        new_seen_keys.add(key)
        print(f"  {score:3d}% — {job['title'][:50]} @ {job['company'][:25]}")

        if score >= MATCH_THRESHOLD:
            matched.append({"job": job, "score": score, "match_info": match_info})

    # Sort by score descending
    matched.sort(key=lambda x: x["score"], reverse=True)
    print(f"\n🎯 Jobs scoring {MATCH_THRESHOLD}%+: {len(matched)}")

    # Update seen
    seen.update(new_seen_keys)
    save_seen(seen)

    if matched:
        print("📧 Generating CVs, cover letters and sending email...")
        send_job_email(matched)
    else:
        print(f"✅ No jobs met the {MATCH_THRESHOLD}% threshold today.")

if __name__ == "__main__":
    main()
