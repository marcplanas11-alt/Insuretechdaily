import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
RECIPIENT_EMAIL = "marcplanas11@gmail.com"
SENDER_EMAIL    = os.environ["GMAIL_USER"]
SENDER_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
SEEN_JOBS_FILE  = "seen_jobs.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; InsurtechJobBot/1.0)"}

# ── Job sources ──────────────────────────────────────────────────────────────
# Each entry: (company, url, parser_function)

def parse_alan(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select("a[href*='/jobs/']"):
        title = card.get_text(strip=True)
        href  = card.get("href", "")
        if not href.startswith("http"):
            href = "https://alan.com" + href
        if title and ("remote" in title.lower() or "remote" in card.parent.get_text().lower()):
            jobs.append({"title": title, "url": href})
    return jobs

def parse_wefox(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select("a"):
        text = card.get_text(strip=True)
        href = card.get("href", "")
        if ("remote" in text.lower() or "remote" in href.lower()) and len(text) > 5:
            if not href.startswith("http"):
                href = "https://careers.wefox.com" + href
            jobs.append({"title": text, "url": href})
    return jobs

def parse_kota(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select("[class*='job'], [class*='position'], [class*='role'], li, div"):
        text = card.get_text(strip=True)
        if "remote" in text.lower() and 10 < len(text) < 200:
            link = card.find("a")
            url  = link["href"] if link and link.get("href") else "https://jobs.ashbyhq.com/kota"
            if not url.startswith("http"):
                url = "https://jobs.ashbyhq.com" + url
            jobs.append({"title": text[:100], "url": url})
    return list({j["title"]: j for j in jobs}.values())  # dedupe

def parse_lassie(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select("a"):
        text = card.get_text(strip=True)
        href = card.get("href", "")
        if text and "remote" in soup.get_text().lower() and len(text) > 8:
            if "job" in href.lower() or "career" in href.lower() or "position" in href.lower():
                if not href.startswith("http"):
                    href = "https://lassie.se" + href
                jobs.append({"title": text, "url": href})
    return jobs[:10]

SOURCES = [
    {
        "company": "Alan (🇫🇷)",
        "url":     "https://alan.com/en/careers",
        "parser":  parse_alan,
    },
    {
        "company": "wefox (🇩🇪)",
        "url":     "https://www.wefox.com/careers",
        "parser":  parse_wefox,
    },
    {
        "company": "Kota (🇮🇪)",
        "url":     "https://jobs.ashbyhq.com/kota",
        "parser":  parse_kota,
    },
    {
        "company": "Lassie (🇸🇪)",
        "url":     "https://www.lassie.se/careers",
        "parser":  parse_lassie,
    },
]

# ── Core logic ───────────────────────────────────────────────────────────────

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠️  Could not fetch {url}: {e}")
        return ""

def scrape_all():
    results = []
    for source in SOURCES:
        print(f"Checking {source['company']}...")
        html = fetch(source["url"])
        if html:
            jobs = source["parser"](html)
            for job in jobs:
                job["company"] = source["company"]
            results.extend(jobs)
    return results

def find_new_jobs(all_jobs, seen_jobs):
    new = []
    for job in all_jobs:
        key = f"{job['company']}|{job['title']}|{job['url']}"
        if key not in seen_jobs:
            new.append((key, job))
    return new

def send_email(new_jobs):
    subject = f"🚨 {len(new_jobs)} New Remote Insurtech Job(s) Found — {datetime.today().strftime('%d %b %Y')}"

    rows = ""
    for _, job in new_jobs:
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;font-weight:bold;">{job['company']}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{job['title']}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <a href="{job['url']}" style="color:#0066cc;">View Job →</a>
          </td>
        </tr>"""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:700px;margin:auto">
      <h2 style="color:#1a1a2e;">🛡️ New Remote Insurtech Jobs</h2>
      <p>The following new <strong>fully remote</strong> positions were detected today:</p>
      <table style="width:100%;border-collapse:collapse;margin-top:20px">
        <thead>
          <tr style="background:#f4f4f4">
            <th style="padding:10px;text-align:left">Company</th>
            <th style="padding:10px;text-align:left">Role</th>
            <th style="padding:10px;text-align:left">Link</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:30px;font-size:12px;color:#999">
        Auto-alert from your EU Insurtech Job Monitor · Runs daily via GitHub Actions
      </p>
    </body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email sent with {len(new_jobs)} new job(s).")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🔍 Running EU Insurtech Job Monitor — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    seen_jobs = load_seen_jobs()
    all_jobs  = scrape_all()
    new_jobs  = find_new_jobs(all_jobs, seen_jobs)

    if new_jobs:
        print(f"🆕 Found {len(new_jobs)} new remote job(s)!")
        send_email(new_jobs)
        seen_jobs.update(key for key, _ in new_jobs)
        save_seen_jobs(seen_jobs)
    else:
        print("✅ No new remote jobs found today.")

if __name__ == "__main__":
    main()
