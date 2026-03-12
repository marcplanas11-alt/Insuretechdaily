"""
EU Expansion Scanner — Marc Planas
Monitors UK insurtechs for signals of EU expansion (new offices, EU job postings,
regulatory filings, funding announcements, press releases).
Scores each signal with Claude AI and emails alerts for high-confidence expansions.
Runs daily via GitHub Actions.
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

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

SEEN_FILE     = "seen_expansions.json"
TRACKER_FILE  = "expansion_tracker.csv"
TODAY         = datetime.now().strftime("%Y-%m-%d")
HEADERS       = {"User-Agent": "Mozilla/5.0 (compatible; ExpansionScanner/1.0)"}
MIN_SCORE     = 60   # alert threshold — lower than job hunter, we want early signals

# ─────────────────────────────────────────────────────────────
# WATCHLIST — UK insurtechs most likely to expand to EU
# ─────────────────────────────────────────────────────────────

UK_INSURTECHS = [
    # MGA & Underwriting
    {"name": "Marshmallow",        "hq": "London",    "sector": "Motor MGA",             "ashby": "marshmallow",     "greenhouse": None,       "lever": None},
    {"name": "Zego",               "hq": "London",    "sector": "Motor/Fleet MGA",        "ashby": "zego",            "greenhouse": None,       "lever": None},
    {"name": "By Miles",           "hq": "London",    "sector": "Pay-per-mile motor",     "ashby": None,              "greenhouse": None,       "lever": "bymiles"},
    {"name": "Wakam",              "hq": "London/Paris","sector": "B2B2C carrier",        "ashby": None,              "greenhouse": None,       "lever": "wakam"},
    {"name": "Concirrus",          "hq": "London",    "sector": "Marine AI",              "ashby": None,              "greenhouse": "concirrus","lever": None},
    {"name": "Cytora",             "hq": "London",    "sector": "Risk digitisation",      "ashby": "cytora",          "greenhouse": None,       "lever": None},
    {"name": "Tractable",          "hq": "London",    "sector": "AI claims",              "ashby": None,              "greenhouse": "tractable","lever": None},
    {"name": "Artificial Labs",    "hq": "London",    "sector": "Specialty underwriting", "ashby": "artificial",      "greenhouse": None,       "lever": None},
    {"name": "Blink Parametric",   "hq": "Dublin/London","sector": "Parametric travel",  "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Inaza",              "hq": "London",    "sector": "Motor MGA AI",           "ashby": "inaza",           "greenhouse": None,       "lever": None},
    {"name": "Kayna",              "hq": "London",    "sector": "Embedded SME",           "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Laka",               "hq": "London",    "sector": "Collective cycling",     "ashby": None,              "greenhouse": None,       "lever": "laka"},
    # Benefits & HR tech
    {"name": "Kota",               "hq": "Dublin",    "sector": "Benefits infrastructure","ashby": "kota",            "greenhouse": None,       "lever": None},
    {"name": "YuLife",             "hq": "London",    "sector": "Group life/wellness",    "ashby": None,              "greenhouse": "yulife",   "lever": None},
    {"name": "Bennie",             "hq": "London",    "sector": "SME benefits",           "ashby": None,              "greenhouse": None,       "lever": None},
    # Embedded & API
    {"name": "Descartes Underwriting","hq": "Paris/London","sector": "Parametric climate","ashby":"descartesunderwriting","greenhouse": None,  "lever": None},
    {"name": "wefox",              "hq": "Berlin/London","sector": "Digital broker",      "ashby": "wefox",           "greenhouse": None,       "lever": None},
    {"name": "Lassie",             "hq": "Stockholm", "sector": "Pet insurance",          "ashby": "lassie",          "greenhouse": None,       "lever": None},
    {"name": "Flock",              "hq": "London",    "sector": "Drone/fleet MGA",        "ashby": None,              "greenhouse": None,       "lever": "flock"},
    {"name": "Collective Benefits","hq": "London",    "sector": "Gig economy",            "ashby": None,              "greenhouse": None,       "lever": "collectivebenefits"},
    # Claims & Data
    {"name": "Shift Technology",   "hq": "Paris/London","sector": "Claims AI",           "ashby": None,              "greenhouse": "shifttechnology","lever": None},
    {"name": "EXL Service",        "hq": "London",    "sector": "Insurance analytics",    "ashby": None,              "greenhouse": None,       "lever": None},
    # Distribution
    {"name": "360GlobalNet",       "hq": "London",    "sector": "Claims platform",        "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Trov",               "hq": "London",    "sector": "Embedded on-demand",     "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Wrisk",              "hq": "London",    "sector": "Embedded lifestyle",     "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Hokodo",             "hq": "London",    "sector": "B2B trade credit",       "ashby": None,              "greenhouse": "hokodo",   "lever": None},
    {"name": "Superscript",        "hq": "London",    "sector": "SME commercial",         "ashby": None,              "greenhouse": None,       "lever": "superscript"},
    {"name": "Hiscox Digital",     "hq": "London",    "sector": "SME cyber/commercial",   "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "ELEMENT Insurance",  "hq": "Berlin",    "sector": "Embedded carrier",       "ashby": None,              "greenhouse": None,       "lever": None},
    {"name": "Saturday Insurance", "hq": "London",    "sector": "Construction",           "ashby": None,              "greenhouse": None,       "lever": None},
]

# EU expansion keywords — if any of these appear in a signal, it's worth scoring
EU_KEYWORDS = [
    "EU", "Europe", "European", "Dublin", "Amsterdam", "Frankfurt", "Paris",
    "Berlin", "Madrid", "Barcelona", "Munich", "Zurich", "Vienna", "Milan",
    "CBI authorisation", "BaFin", "AMF", "DNB authorised", "Solvency II",
    "passporting", "EU licence", "EU license", "EIOPA", "pan-European",
    "European expansion", "EU market", "EU office", "European market",
    "continental Europe", "DACH", "Benelux", "Nordics", "Southern Europe",
    "Spanish market", "French market", "German market", "Italian market",
    "EU hub", "European hub", "regulatory approval", "EU subsidiary",
]

# News RSS feeds covering insurtech / fintech expansion
NEWS_RSS_FEEDS = [
    {"name": "InsTech London",  "url": "https://www.instech.london/feed"},
    {"name": "Sifted",          "url": "https://sifted.eu/feed"},
    {"name": "EU-Startups",     "url": "https://www.eu-startups.com/category/insurtech/feed/"},
    {"name": "Fintech Global",  "url": "https://fintech.global/insurtech/feed/"},
    {"name": "AltFi",           "url": "https://www.altfi.com/feed"},
    {"name": "The Insurer",     "url": "https://www.theinsurer.com/feed/"},
    {"name": "Insurance Age",   "url": "https://www.insuranceage.co.uk/feed"},
]

EU_CITIES = [
    "dublin", "amsterdam", "paris", "frankfurt", "berlin", "madrid", "barcelona",
    "munich", "zurich", "vienna", "milan", "brussels", "lisbon", "stockholm",
    "oslo", "copenhagen", "warsaw", "prague", "budapest", "rotterdam", "hamburg",
    "lyon", "marseille", "valencia", "seville", "cologne", "düsseldorf",
]

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r if r.status_code == 200 else None
    except Exception as e:
        print(f"    fetch error {url[:60]}: {e}")
        return None

def signal_id(company, title, source):
    raw = f"{company}|{title}|{source}".lower()
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()

def save_seen(seen):
    json.dump(list(seen), open(SEEN_FILE, "w"))

def contains_eu_keyword(text):
    t = text.lower()
    return any(kw.lower() in t for kw in EU_KEYWORDS)

def is_uk_company(name):
    return any(c["name"].lower() == name.lower() for c in UK_INSURTECHS)

# ─────────────────────────────────────────────────────────────
# SOURCE 1 — NEWS RSS (InsTech, Sifted, EU-Startups, etc.)
# ─────────────────────────────────────────────────────────────

def scan_news_rss():
    signals = []
    company_names = [c["name"].lower() for c in UK_INSURTECHS]

    for feed in NEWS_RSS_FEEDS:
        r = fetch(feed["url"])
        if not r:
            print(f"  RSS {feed['name']}: no response")
            continue
        try:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            count = 0
            for item in items:
                title   = (item.findtext("title") or "").strip()
                desc    = (item.findtext("description") or "").strip()
                link    = (item.findtext("link") or "").strip()
                content = f"{title} {desc}"

                # Must mention a watchlist company AND an EU keyword
                mentioned = [c["name"] for c in UK_INSURTECHS
                             if c["name"].lower() in content.lower()]
                if not mentioned:
                    continue
                if not contains_eu_keyword(content):
                    continue

                for company in mentioned:
                    signals.append({
                        "company":     company,
                        "signal_type": "news",
                        "title":       title[:120],
                        "detail":      desc[:300],
                        "source":      feed["name"],
                        "link":        link,
                    })
                    count += 1
            print(f"  RSS {feed['name']}: {count} signal(s)")
        except Exception as e:
            print(f"  RSS {feed['name']} parse error: {e}")

    return signals

# ─────────────────────────────────────────────────────────────
# SOURCE 2 — JOB BOARD APIS (Ashby / Greenhouse / Lever)
# Check watchlist companies for EU city job postings
# ─────────────────────────────────────────────────────────────

def scan_job_boards():
    signals = []

    # — Ashby —
    for co in UK_INSURTECHS:
        if not co.get("ashby"):
            continue
        url = f"https://api.ashbyhq.com/posting-api/job-board/{co['ashby']}?includeCompensation=true"
        r = fetch(url)
        if not r:
            continue
        try:
            jobs = r.json().get("jobs", [])
            for job in jobs:
                if not job.get("isListed", True):
                    continue
                location  = (job.get("location") or "").lower()
                workplace = (job.get("workplaceType") or "").lower()
                title     = job.get("title", "")
                jurl      = job.get("jobUrl", "")

                is_eu_city   = any(city in location for city in EU_CITIES)
                is_eu_remote = "remote" in workplace and any(
                    kw in (job.get("descriptionPlain") or "").lower()
                    for kw in ["europe", "eu", "european"]
                )
                if is_eu_city or is_eu_remote:
                    signals.append({
                        "company":     co["name"],
                        "signal_type": "job_posting_eu_city",
                        "title":       f"Job posted: {title}",
                        "detail":      f"Location: {job.get('location','')} | Type: {workplace}",
                        "source":      "Ashby API",
                        "link":        jurl,
                    })
        except Exception as e:
            print(f"  Ashby {co['name']} error: {e}")

    # — Greenhouse —
    for co in UK_INSURTECHS:
        if not co.get("greenhouse"):
            continue
        url = f"https://api.greenhouse.io/v1/boards/{co['greenhouse']}/jobs?content=true"
        r = fetch(url)
        if not r:
            continue
        try:
            jobs = r.json().get("jobs", [])
            for job in jobs:
                location = (job.get("location", {}).get("name") or "").lower()
                if any(city in location for city in EU_CITIES):
                    signals.append({
                        "company":     co["name"],
                        "signal_type": "job_posting_eu_city",
                        "title":       f"Job posted: {job.get('title','')}",
                        "detail":      f"Location: {job.get('location',{}).get('name','')}",
                        "source":      "Greenhouse API",
                        "link":        job.get("absolute_url", ""),
                    })
        except Exception as e:
            print(f"  Greenhouse {co['name']} error: {e}")

    # — Lever —
    for co in UK_INSURTECHS:
        if not co.get("lever"):
            continue
        url = f"https://api.lever.co/v0/postings/{co['lever']}?mode=json"
        r = fetch(url)
        if not r:
            continue
        try:
            for job in r.json():
                location = (job.get("categories", {}).get("location") or "").lower()
                workplace = (job.get("categories", {}).get("commitment") or "").lower()
                if any(city in location for city in EU_CITIES):
                    signals.append({
                        "company":     co["name"],
                        "signal_type": "job_posting_eu_city",
                        "title":       f"Job posted: {job.get('text','')}",
                        "detail":      f"Location: {job.get('categories',{}).get('location','')}",
                        "source":      "Lever API",
                        "link":        job.get("hostedUrl", ""),
                    })
        except Exception as e:
            print(f"  Lever {co['name']} error: {e}")

    print(f"  Job boards: {len(signals)} EU-city posting(s)")
    return signals

# ─────────────────────────────────────────────────────────────
# SOURCE 3 — FUNDING NEWS RSS (Crunchbase-style aggregators)
# ─────────────────────────────────────────────────────────────

FUNDING_RSS = [
    {"name": "EU-Startups Funding", "url": "https://www.eu-startups.com/category/funding-news/feed/"},
    {"name": "Sifted Funding",      "url": "https://sifted.eu/sector/fintech/feed"},
    {"name": "AltFi News",          "url": "https://www.altfi.com/category/news/feed"},
]

def scan_funding_news():
    signals = []
    for feed in FUNDING_RSS:
        r = fetch(feed["url"])
        if not r:
            continue
        try:
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items:
                title  = (item.findtext("title") or "").strip()
                desc   = (item.findtext("description") or "").strip()
                link   = (item.findtext("link") or "").strip()
                text   = f"{title} {desc}"

                mentioned = [c["name"] for c in UK_INSURTECHS
                             if c["name"].lower() in text.lower()]
                if not mentioned:
                    continue

                # Funding news with EU keywords = expansion round
                funding_kws = ["raises", "funding", "series", "investment", "round", "million", "secured"]
                is_funding = any(kw in text.lower() for kw in funding_kws)
                if not is_funding:
                    continue
                if not contains_eu_keyword(text):
                    continue

                for company in mentioned:
                    signals.append({
                        "company":     company,
                        "signal_type": "funding_eu_mention",
                        "title":       title[:120],
                        "detail":      desc[:300],
                        "source":      feed["name"],
                        "link":        link,
                    })
        except Exception as e:
            print(f"  Funding RSS {feed['name']} error: {e}")

    print(f"  Funding news: {len(signals)} signal(s)")
    return signals

# ─────────────────────────────────────────────────────────────
# SOURCE 4 — REGULATORY NEWS
# CBI (Ireland), BaFin (Germany), ACPR/AMF (France) new entrant mentions
# ─────────────────────────────────────────────────────────────

REGULATORY_RSS = [
    {"name": "CBI News",    "url": "https://www.centralbank.ie/news/rss/allarticles",
     "regulator": "CBI",   "country": "Ireland"},
    {"name": "BaFin News",  "url": "https://www.bafin.de/SiteGlobals/Functions/RSS/EN/RSS_Aktuelles_en.xml;jsessionid=",
     "regulator": "BaFin", "country": "Germany"},
    {"name": "EIOPA News",  "url": "https://www.eiopa.europa.eu/rss.xml",
     "regulator": "EIOPA", "country": "EU"},
]

def scan_regulatory():
    signals = []
    for feed in REGULATORY_RSS:
        r = fetch(feed["url"])
        if not r:
            print(f"  Regulatory {feed['name']}: no response")
            continue
        try:
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                link  = (item.findtext("link") or "").strip()
                text  = f"{title} {desc}"

                mentioned = [c["name"] for c in UK_INSURTECHS
                             if c["name"].lower() in text.lower()]
                if not mentioned:
                    continue

                auth_kws = ["authoris", "authoriz", "licens", "register", "approv",
                            "passporting", "notif", "withdrawal", "permission"]
                if not any(kw in text.lower() for kw in auth_kws):
                    continue

                for company in mentioned:
                    signals.append({
                        "company":     company,
                        "signal_type": f"regulatory_{feed['regulator'].lower()}",
                        "title":       f"{feed['regulator']}: {title[:100]}",
                        "detail":      desc[:300],
                        "source":      feed["name"],
                        "link":        link,
                    })
        except Exception as e:
            print(f"  Regulatory {feed['name']} error: {e}")

    print(f"  Regulatory feeds: {len(signals)} signal(s)")
    return signals

# ─────────────────────────────────────────────────────────────
# SOURCE 5 — LINKEDIN JOBS (unofficial search endpoint)
# Search EU city + insurtech, filter to watchlist companies
# ─────────────────────────────────────────────────────────────

def scan_linkedin_jobs():
    """
    Uses LinkedIn's public jobs search endpoint (no auth required for basic search).
    Filters results to watchlist company names.
    """
    signals = []
    search_queries = [
        ("insurtech", "Dublin"),
        ("insurtech", "Amsterdam"),
        ("insurance technology", "Madrid"),
        ("MGA insurance", "Frankfurt"),
        ("embedded insurance", "Paris"),
    ]

    company_names_lower = {c["name"].lower(): c["name"] for c in UK_INSURTECHS}

    for keyword, city in search_queries:
        url = (
            f"https://www.linkedin.com/jobs/search/?keywords={requests.utils.quote(keyword)}"
            f"&location={requests.utils.quote(city)}&f_WT=2&sortBy=DD"
        )
        r = fetch(url)
        if not r:
            continue
        try:
            text = r.text.lower()
            for name_lower, name_original in company_names_lower.items():
                if name_lower in text:
                    signals.append({
                        "company":     name_original,
                        "signal_type": "linkedin_eu_job",
                        "title":       f"LinkedIn job detected in {city}: {keyword}",
                        "detail":      f"Search: {keyword} in {city} — {name_original} appeared in results",
                        "source":      "LinkedIn Jobs",
                        "link":        url,
                    })
        except Exception as e:
            print(f"  LinkedIn {city} error: {e}")

    # Deduplicate — one signal per company per day from LinkedIn
    seen_li = set()
    deduped = []
    for s in signals:
        key = s["company"]
        if key not in seen_li:
            seen_li.add(key)
            deduped.append(s)

    print(f"  LinkedIn jobs: {len(deduped)} signal(s)")
    return deduped

# ─────────────────────────────────────────────────────────────
# SOURCE 6 — COMPANY CAREER PAGES (HTML scrape for EU mentions)
# Spot-checks career pages of companies without ATS APIs
# ─────────────────────────────────────────────────────────────

CAREER_PAGES = [
    {"name": "Marshmallow",    "url": "https://www.marshmallow.com/careers"},
    {"name": "Zego",           "url": "https://www.zego.com/careers"},
    {"name": "By Miles",       "url": "https://www.bymiles.co.uk/careers"},
    {"name": "Flock",          "url": "https://www.flock.co/careers"},
    {"name": "YuLife",         "url": "https://www.yulife.com/careers"},
    {"name": "Hokodo",         "url": "https://www.hokodo.co/careers"},
    {"name": "Superscript",    "url": "https://www.superscript.com/careers"},
    {"name": "Concirrus",      "url": "https://www.concirrus.com/careers"},
    {"name": "Wrisk",          "url": "https://www.wrisk.co/careers"},
    {"name": "Kayna",          "url": "https://kayna.io/careers"},
]

def scan_career_pages():
    signals = []
    for co in CAREER_PAGES:
        r = fetch(co["url"])
        if not r:
            continue
        try:
            text = r.text.lower()
            found_cities = [city for city in EU_CITIES if city in text]
            if found_cities:
                signals.append({
                    "company":     co["name"],
                    "signal_type": "careers_page_eu_location",
                    "title":       f"EU city mention on {co['name']} careers page",
                    "detail":      f"Cities detected: {', '.join(found_cities[:5])}",
                    "source":      "Career page scrape",
                    "link":        co["url"],
                })
        except Exception as e:
            print(f"  Career page {co['name']} error: {e}")

    print(f"  Career pages: {len(signals)} signal(s)")
    return signals

# ─────────────────────────────────────────────────────────────
# AI SCORER — Claude rates expansion confidence 0-100
# ─────────────────────────────────────────────────────────────

def score_signal(signal):
    if not ANTHROPIC_API_KEY:
        return {"score": 50, "summary": "No API key — scored at 50 by default",
                "expansion_type": "unknown", "eu_markets": "unknown",
                "hiring_opportunity": "unknown"}

    co_info = next((c for c in UK_INSURTECHS if c["name"] == signal["company"]), {})

    prompt = f"""You are an insurance industry analyst. A UK-based insurtech is showing a potential signal of expanding to the EU.

COMPANY: {signal['company']}
HQ: {co_info.get('hq', 'UK')}
SECTOR: {co_info.get('sector', 'Insurtech')}

SIGNAL TYPE: {signal['signal_type']}
SIGNAL TITLE: {signal['title']}
SIGNAL DETAIL: {signal['detail']}
SOURCE: {signal['source']}

Score the EU expansion confidence from 0-100:
- 90-100: Definitive (regulatory filing, office opening announcement, press release confirming EU launch)
- 70-89: Strong (EU city job postings in senior/operational roles, funding round explicitly mentioning EU expansion)
- 50-69: Moderate (junior EU city jobs, EU keyword in funding news but not primary focus)
- 30-49: Weak (career page EU mention, indirect news reference)
- 0-29: Noise (incidental mention, no real expansion signal)

Also identify:
- Which EU markets are being targeted (specific countries/cities if clear, or "unclear")
- Expansion type: "regulatory", "office", "hiring", "funding", "partnership", or "unclear"
- Hiring opportunity for EU-based insurance professionals: "high", "medium", "low", or "none"

Respond ONLY in valid JSON:
{{"score":<int>,"summary":"<2 sentences explaining the signal>","expansion_type":"<type>","eu_markets":"<markets>","hiring_opportunity":"<level>"}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 400,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"    AI scorer error: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# TRACKER
# ─────────────────────────────────────────────────────────────

def log_to_tracker(signal, score_result):
    file_exists = os.path.exists(TRACKER_FILE)
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date","Company","Sector","Signal Type","Title",
                             "EU Markets","Expansion Type","Hiring Opportunity",
                             "Score","Summary","Source","Link"])
        co_info = next((c for c in UK_INSURTECHS if c["name"] == signal["company"]), {})
        writer.writerow([
            TODAY,
            signal["company"],
            co_info.get("sector", ""),
            signal["signal_type"],
            signal["title"],
            score_result.get("eu_markets", ""),
            score_result.get("expansion_type", ""),
            score_result.get("hiring_opportunity", ""),
            score_result.get("score", ""),
            score_result.get("summary", ""),
            signal["source"],
            signal["link"],
        ])

# ─────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────

SIGNAL_TYPE_LABELS = {
    "news":                    "📰 News article",
    "job_posting_eu_city":     "💼 EU city job posting",
    "funding_eu_mention":      "💰 Funding with EU mention",
    "regulatory_cbi":          "🏛️ CBI regulatory signal",
    "regulatory_bafin":        "🏛️ BaFin regulatory signal",
    "regulatory_eiopa":        "🏛️ EIOPA regulatory signal",
    "linkedin_eu_job":         "🔗 LinkedIn EU job signal",
    "careers_page_eu_location":"🌍 EU location on careers page",
}

def score_color(score):
    if score >= 80: return "#1a7a3a"
    if score >= 60: return "#4a4a8a"
    return "#888888"

def send_alert_email(matched_signals):
    if not matched_signals:
        return

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"EU Expansion Alert {TODAY} - {len(matched_signals)} UK insurtech(s) moving"
    msg["From"]    = f"EU Expansion Scanner <{GMAIL_USER}>"
    msg["To"]      = GMAIL_USER
    msg["Reply-To"]= GMAIL_USER
    msg["X-Mailer"]= "Python/smtplib"

    # Group signals by company for cleaner email
    by_company = {}
    for s in matched_signals:
        co = s["company"]
        by_company.setdefault(co, []).append(s)

    html = [f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;">
<h2 style="color:#1a1a2e;border-bottom:3px solid #4a4a8a;padding-bottom:8px;">
  🌍 EU Expansion Radar — {TODAY}
</h2>
<p style="color:#666;">
  {len(matched_signals)} signal(s) detected across {len(by_company)} UK insurtech(s).
  Scored {MIN_SCORE}%+ confidence of EU market entry.
</p>"""]

    for company, signals in by_company.items():
        co_info = next((c for c in UK_INSURTECHS if c["name"] == company), {})
        top_score = max(s["ai_result"]["score"] for s in signals)
        color = score_color(top_score)

        html.append(f"""
<div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin:20px 0;">
  <h3 style="color:{color};margin:0 0 4px 0;">{company}
    <span style="font-size:13px;font-weight:normal;color:#666;margin-left:8px;">
      {co_info.get('hq','')} · {co_info.get('sector','')}
    </span>
  </h3>""")

        for s in signals:
            ai = s["ai_result"]
            label = SIGNAL_TYPE_LABELS.get(s["signal_type"], s["signal_type"])
            html.append(f"""
  <div style="background:#f8f8ff;border-left:4px solid {score_color(ai['score'])};
              padding:10px 12px;margin:10px 0;border-radius:0 6px 6px 0;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span style="font-weight:bold;font-size:13px;">{label}</span>
      <span style="font-size:18px;font-weight:bold;color:{score_color(ai['score'])};">
        {ai['score']}%
      </span>
    </div>
    <div style="font-size:13px;color:#333;margin:4px 0;">{s['title']}</div>
    <div style="font-size:12px;color:#666;margin:4px 0;font-style:italic;">
      {ai.get('summary','')}
    </div>
    <table style="font-size:12px;color:#555;margin-top:6px;">
      <tr>
        <td style="padding-right:16px;"><b>EU Markets:</b> {ai.get('eu_markets','—')}</td>
        <td style="padding-right:16px;"><b>Type:</b> {ai.get('expansion_type','—')}</td>
        <td><b>Hiring:</b> {ai.get('hiring_opportunity','—')}</td>
      </tr>
    </table>
    <div style="margin-top:8px;">
      <a href="{s['link']}" style="background:#4a4a8a;color:white;padding:5px 12px;
         text-decoration:none;border-radius:4px;font-size:12px;">View Source →</a>
    </div>
  </div>""")

        html.append("</div>")

    html.append(f"""
<hr style="border:1px solid #eee;margin:20px 0;">
<p style="color:#888;font-size:11px;">
  EU Expansion Scanner · {len(UK_INSURTECHS)} companies monitored ·
  All signals logged to expansion_tracker.csv
</p>
</body></html>""")

    # Plain text fallback
    plain = [f"EU Expansion Alert — {TODAY}", ""]
    for company, signals in by_company.items():
        plain.append(f"{company}:")
        for s in signals:
            plain.append(f"  [{s['ai_result']['score']}%] {s['title']}")
            plain.append(f"  {s['link']}")
        plain.append("")

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("\n".join(plain), "plain"))
    alt.attach(MIMEText("".join(html), "html"))
    msg.attach(alt)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"Alert email sent: {len(matched_signals)} signal(s) across {len(by_company)} company/companies.")
    except Exception as e:
        print(f"Email error: {e}")

# ─────────────────────────────────────────────────────────────
# WEEKLY SUMMARY DATA (written to file for weekly_digest.py)
# ─────────────────────────────────────────────────────────────

def save_weekly_data(matched_signals):
    """Append today's expansion signals to a JSON file for the weekly digest."""
    weekly_file = "expansion_weekly.json"
    try:
        existing = json.load(open(weekly_file))
    except Exception:
        existing = []

    for s in matched_signals:
        existing.append({
            "date":              TODAY,
            "company":          s["company"],
            "signal_type":      s["signal_type"],
            "title":            s["title"],
            "score":            s["ai_result"]["score"],
            "eu_markets":       s["ai_result"].get("eu_markets", ""),
            "expansion_type":   s["ai_result"].get("expansion_type", ""),
            "hiring_opportunity": s["ai_result"].get("hiring_opportunity", ""),
            "link":             s["link"],
        })

    # Keep only last 30 days
    cutoff = datetime.now().strftime("%Y-%m-%d")
    existing = [e for e in existing if e["date"] >= cutoff[:7]]  # current month
    json.dump(existing, open(weekly_file, "w"), indent=2)

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print(f"\nEU Expansion Scanner — {TODAY}\n")
    seen = load_seen()

    print("Scanning signal sources...")
    print("→ Source 1: News RSS feeds")
    all_signals  = scan_news_rss()
    print("→ Source 2: Job board APIs (Ashby/Greenhouse/Lever)")
    all_signals += scan_job_boards()
    print("→ Source 3: Funding news RSS")
    all_signals += scan_funding_news()
    print("→ Source 4: Regulatory feeds")
    all_signals += scan_regulatory()
    print("→ Source 5: LinkedIn jobs")
    all_signals += scan_linkedin_jobs()
    print("→ Source 6: Career page scrape")
    all_signals += scan_career_pages()

    print(f"\nTotal raw signals: {len(all_signals)}")

    # Deduplicate
    new_signals = []
    for s in all_signals:
        sid = signal_id(s["company"], s["title"], s["source"])
        if sid not in seen:
            seen.add(sid)
            new_signals.append(s)

    print(f"New (not seen before): {len(new_signals)}")

    if not new_signals:
        print("No new expansion signals today.")
        save_seen(seen)
        return

    # Score with Claude AI
    matched = []
    print("\nScoring with Claude AI...")
    for s in new_signals:
        result = score_signal(s)
        if not result:
            continue
        score = result.get("score", 0)
        label = SIGNAL_TYPE_LABELS.get(s["signal_type"], s["signal_type"])
        print(f"  {score:3d}% — {s['company']} | {label}")
        log_to_tracker(s, result)
        if score >= MIN_SCORE:
            s["ai_result"] = result
            matched.append(s)

    print(f"\nAlerts at {MIN_SCORE}%+: {len(matched)}")
    if matched:
        save_weekly_data(matched)
        send_alert_email(matched)

    save_seen(seen)
    print("Done.")

if __name__ == "__main__":
    main()
