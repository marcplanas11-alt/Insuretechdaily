"""
AI Job Hunter — Marc Planas
Scans multiple job sources daily, scores matches with Claude AI,
and emails tailored CVs + cover letters for 80%+ matches.
"""

import os
import json
import smtplib
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from marc_profile import PROFILE

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SEEN_JOBS_FILE = "seen_jobs.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobHunterBot/1.0)"
}

# ─────────────────────────────────────────────
# SOURCES
# ─────────────────────────────────────────────

INDEED_RSS_FEEDS = [
    "https://www.indeed.com/rss?q=insurtech+operations&l=remote&sort=date",
    "https://www.indeed.com/rss?q=MGA+insurance&l=remote&sort=date",
    "https://www.indeed.com/rss?q=insurtech+product+manager&l=remote&sort=date",
    "https://www.indeed.com/rss?q=insurance+digital+transformation&l=remote&sort=date",
    "https://www.indeed.co.uk/rss?q=insurtech&l=remote&sort=date",
]

REMOTE_BOARDS = [
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss",
        "type": "rss"
    },
    {
        "name": "We Work Remotely (Ops)",
        "url": "https://weworkremotely.com/categories/remote-management-finance-jobs.rss",
        "type": "rss"
    },
    {
        "name": "Remote OK",
        "url": "https://remoteok.com/api",
        "type": "json"
    },
    {
        "name": "Remotive",
        "url": "https://remotive.com/api/remote-jobs?category=finance&limit=30",
        "type": "json_remotive"
    },
]

INSURTECH_COMPANIES = [
    {"name": "Alan", "url": "https://alan.com/en/careers", "keywords": ["insurance", "health"]},
    {"name": "wefox", "url": "https://careers.wefox.com", "keywords": ["insurance"]},
    {"name": "Kota", "url": "https://jobs.ashbyhq.com/kota", "keywords": ["insurance", "benefits"]},
    {"name": "Descartes Underwriting", "url": "https://careers.descartesunderwriting.com", "keywords": ["insurance", "underwriting"]},
    {"name": "Shift Technology", "url": "https://www.shift-technology.com/careers", "keywords": ["insurance", "AI"]},
    {"name": "Cytora", "url": "https://www.cytora.com/careers", "keywords": ["insurance", "underwriting"]},
    {"name": "Tractable", "url": "https://tractable.ai/careers", "keywords": ["insurance", "AI"]},
    {"name": "FINEOS", "url": "https://careers.fineos.com", "keywords": ["insurance"]},
    {"name": "Laka", "url": "https://laka.co/careers", "keywords": ["insurance", "mobility"]},
    {"name": "Inaza", "url": "https://www.inaza.com/careers", "keywords": ["insurance", "motor"]},
    {"name": "Kayna", "url": "https://www.kayna.io/careers", "keywords": ["embedded insurance"]},
    {"name": "Blink Parametric", "url": "https://www.blinkparametric.com/careers", "keywords": ["parametric"]},
    {"name": "CoverGo", "url": "https://covergo.com/careers", "keywords": ["insurance"]},
    {"name": "Wakam", "url": "https://www.wakam.com/en/careers", "keywords": ["insurance"]},
    {"name": "Artificial Labs", "url": "https://www.artificial.io/careers", "keywords": ["insurance", "MGA"]},
    {"name": "Novidea", "url": "https://www.novidea.com/careers", "keywords": ["insurance", "broker"]},
    {"name": "EIS Group", "url": "https://eisgroup.com/careers", "keywords": ["insurance"]},
    {"name": "Majesco", "url": "https://www.majesco.com/careers", "keywords": ["insurance"]},
    {"name": "Guidewire", "url": "https://www.guidewire.com/careers", "keywords": ["insurance"]},
    {"name": "Duck Creek", "url": "https://www.duckcreek.com/about/careers", "keywords": ["insurance"]},
]

RECRUITERS = [
    {"name": "IDEX Consulting", "url": "https://www.idexconsulting.com/jobs/?search=insurtech&location=remote"},
    {"name": "Barclay Simpson", "url": "https://www.barclaysimpson.com/jobs/?search=insurance&remote=1"},
    {"name": "Hays Spain", "url": "https://www.hays.es/en/job/search-jobs/q-insurance/p-remote"},
    {"name": "Michael Page Spain", "url": "https://www.michaelpage.es/jobs/insurance?remote=true"},
    {"name": "Robert Walters", "url": "https://www.robertwalters.es/jobs.html?query=insurance&workType=remote"},
    {"name": "Marks Sattin", "url": "https://www.markssattin.co.uk/jobs/insurance/?remote=true"},
    {"name": "Morgan McKinley", "url": "https://www.morganmckinley.com/jobs?q=insurtech&workType=remote"},
    {"name": "Eames Consulting", "url": "https://www.eamesconsulting.com/jobs/?search=insurance+remote"},
    {"name": "Optio Search", "url": "https://www.optiosearch.com/jobs/?sector=insurance"},
    {"name": "Insnerds Jobs", "url": "https://insnerds.com/jobs"},
    {"name": "InsTech Jobs", "url": "https://www.instech.london/jobs"},
]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_seen_jobs():
    try:
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(title, company):
    return hashlib.md5(f"{title}|{company}".lower().encode()).hexdigest()

def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r
    except Exception as e:
        print(f"  ⚠️  Fetch error: {e}")
        return None

# ─────────────────────────────────────────────
# SCRAPERS
# ─────────────────────────────────────────────

def scrape_indeed_rss():
    jobs = []
    for feed_url in INDEED_RSS_FEEDS:
        r = fetch(feed_url)
        if not r or r.status_code != 200:
            continue
        try:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                desc = item.findtext("description", "").strip()
                jobs.append({
                    "title": title,
                    "company": "Indeed Listing",
                    "link": link,
                    "description": desc,
                    "source": "Indeed"
                })
        except Exception as e:
            print(f"  ⚠️  Indeed parse error: {e}")
    print(f"  Indeed: {len(jobs)} listings")
    return jobs

def scrape_remote_boards():
    jobs = []
    for board in REMOTE_BOARDS:
        r = fetch(board["url"])
        if not r or r.status_code != 200:
            print(f"  ⚠️  {board['name']}: HTTP {r.status_code if r else 'no response'}")
            continue
        try:
            if board["type"] == "rss":
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    jobs.append({
                        "title": item.findtext("title", "").strip(),
                        "company": board["name"],
                        "link": item.findtext("link", "").strip(),
                        "description": item.findtext("description", "").strip(),
                        "source": board["name"]
                    })
            elif board["type"] == "json":
                data = r.json()
                if isinstance(data, list):
                    for job in data[1:]:  # RemoteOK: first item is metadata
                        if isinstance(job, dict):
                            jobs.append({
                                "title": job.get("position", ""),
                                "company": job.get("company", ""),
                                "link": job.get("url", ""),
                                "description": " ".join(job.get("tags", [])),
                                "source": board["name"]
                            })
            elif board["type"] == "json_remotive":
                data = r.json()
                for job in data.get("jobs", []):
                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "link": job.get("url", ""),
                        "description": job.get("description", "")[:500],
                        "source": board["name"]
                    })
        except Exception as e:
            print(f"  ⚠️  {board['name']} parse error: {e}")
    print(f"  Remote boards: {len(jobs)} listings")
    return jobs

def scrape_company_pages():
    jobs = []
    for company in INSURTECH_COMPANIES:
        r = fetch(company["url"])
        if not r or r.status_code != 200:
            continue
        text = r.text.lower()
        for kw in company["keywords"]:
            if kw.lower() in text:
                jobs.append({
                    "title": f"Open roles at {company['name']}",
                    "company": company["name"],
                    "link": company["url"],
                    "description": f"Insurtech company with open roles: {', '.join(company['keywords'])}",
                    "source": "Insurtech Company"
                })
                break
    print(f"  Company sites: {len(jobs)} active listings found")
    return jobs

def scrape_recruiters():
    jobs = []
    for rec in RECRUITERS:
        r = fetch(rec["url"])
        if not r or r.status_code != 200:
            continue
        text = r.text.lower()
        if any(kw in text for kw in ["insurance", "insurtech", "underwriting", "mga"]):
            jobs.append({
                "title": f"Recruiter listings — {rec['name']}",
                "company": rec["name"],
                "link": rec["url"],
                "description": "Insurance / insurtech recruiter with active listings",
                "source": "Recruiter"
            })
    print(f"  Recruiters: {len(jobs)} active")
    return jobs

# ─────────────────────────────────────────────
# AI SCORING & CV GENERATION
# ─────────────────────────────────────────────

def score_and_generate(job):
    """Call Claude AI to score the job and generate CV + cover letter."""
    if not ANTHROPIC_API_KEY:
        return None

    profile_summary = f"""
Name: {PROFILE['name']}
Target roles: {', '.join(PROFILE['target_roles'][:6])}
Skills: {', '.join(PROFILE['experience'][0]['skills'][:10])}
Languages: {', '.join(PROFILE['languages'])}
Location: {PROFILE['location']}
CV Summary (EN): {PROFILE['cv_summary_en'].strip()}
"""

    prompt = f"""You are a professional career coach and CV writer specializing in insurance and insurtech.

CANDIDATE PROFILE:
{profile_summary}

JOB LISTING:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}
Description: {job['description'][:800]}

TASKS:
1. Score this job 0-100 based on fit with the candidate profile. Consider: role relevance, domain match, seniority fit, remote compatibility.
2. If score >= 80, write:
   a) A tailored CV summary in English (3-4 sentences)
   b) A tailored CV summary in Spanish (3-4 sentences)
   c) A cover letter opening paragraph in English (3-4 sentences)
   d) A cover letter opening paragraph in Spanish (3-4 sentences)

Respond ONLY in valid JSON with this structure:
{{
  "score": <integer 0-100>,
  "reason": "<one sentence why>",
  "cv_summary_en": "<tailored CV summary in English or empty string>",
  "cv_summary_es": "<tailored CV summary in Spanish or empty string>",
  "cover_letter_en": "<cover letter paragraph in English or empty string>",
  "cover_letter_es": "<cover letter paragraph in Spanish or empty string>"
}}"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        data = response.json()
        text = data["content"][0]["text"]
        # Strip markdown code fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  AI scoring error: {e}")
        return None

# ─────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────

def send_email(matched_jobs):
    if not matched_jobs:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(matched_jobs)} New Insurtech Job Match(es) — {TODAY}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    html_parts = [f"""
<html><body>
<h2>🎯 {len(matched_jobs)} New Job Match(es) — {TODAY}</h2>
<p>Jobs scoring 80%+ against your profile:</p>
"""]

    for job in matched_jobs:
        ai = job.get("ai_result", {})
        score = ai.get("score", "N/A")
        html_parts.append(f"""
<hr>
<h3><a href="{job['link']}">{job['title']}</a></h3>
<p><strong>Company:</strong> {job['company']} &nbsp;|&nbsp;
   <strong>Source:</strong> {job['source']} &nbsp;|&nbsp;
   <strong>Match Score:</strong> {score}%</p>
<p><em>{ai.get('reason', '')}</em></p>

<h4>📄 Tailored CV Summary (EN)</h4>
<p>{ai.get('cv_summary_en', '')}</p>

<h4>📄 Resumen CV (ES)</h4>
<p>{ai.get('cv_summary_es', '')}</p>

<h4>✉️ Cover Letter Opening (EN)</h4>
<p>{ai.get('cover_letter_en', '')}</p>

<h4>✉️ Carta de Presentación (ES)</h4>
<p>{ai.get('cover_letter_es', '')}</p>

<p><a href="{job['link']}">👉 Apply here</a></p>
""")

    html_parts.append("</body></html>")
    msg.attach(MIMEText("".join(html_parts), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Email sent with {len(matched_jobs)} matched job(s).")
    except Exception as e:
        print(f"❌ Email error: {e}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"\n🔍 AI Job Hunter — {TODAY}\n")
    seen = load_seen_jobs()

    all_jobs = []
    print("📡 Scanning sources...")
    all_jobs += scrape_indeed_rss()
    all_jobs += scrape_remote_boards()
    all_jobs += scrape_company_pages()
    all_jobs += scrape_recruiters()

    print(f"\n📊 Total listings found: {len(all_jobs)}")

    new_jobs = []
    for job in all_jobs:
        jid = job_id(job["title"], job["company"])
        if jid not in seen:
            new_jobs.append(job)
            seen.add(jid)

    print(f"🆕 New listings (not seen before): {len(new_jobs)}")

    if not new_jobs:
        print("✅ No new jobs today.")
        save_seen_jobs(seen)
        return

    # Score with AI
    matched = []
    print("\n🤖 Scoring with Claude AI...")
    for job in new_jobs:
        result = score_and_generate(job)
        if result and result.get("score", 0) >= PROFILE["min_match_score"]:
            job["ai_result"] = result
            matched.append(job)
            print(f"  ✅ {result['score']}% — {job['title']} @ {job['company']}")
        elif result:
            print(f"  ⬇️  {result['score']}% — {job['title']} @ {job['company']} (below threshold)")

    print(f"\n🎯 Matches at 80%+: {len(matched)}")
    send_email(matched)
    save_seen_jobs(seen)

if __name__ == "__main__":
    main()
