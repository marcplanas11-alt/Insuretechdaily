import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Config ───────────────────────────────────────────────────────────────────
RECIPIENT_EMAIL   = "marcplanas11@gmail.com"
SENDER_EMAIL      = os.environ["GMAIL_USER"]
SENDER_PASSWORD   = os.environ["GMAIL_APP_PASSWORD"]
SEEN_COMPANIES_FILE = "seen_companies.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

INSURTECH_KEYWORDS = [
    "insurtech", "insuretech", "insurance tech", "insurance technology",
    "parametric insurance", "embedded insurance", "digital insurance",
    "insurance platform", "insurance startup", "insurtech startup"
]

# ── Sources ───────────────────────────────────────────────────────────────────

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠️  Could not fetch {url}: {e}")
        return ""

def is_insurtech_related(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in INSURTECH_KEYWORDS)

def parse_eu_startups(html):
    """eu-startups.com — covers EU startup news and funding rounds"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for article in soup.select("article, .post, .entry"):
        title_el = article.select_one("h2, h3, .entry-title, .post-title")
        link_el  = article.select_one("a[href]")
        excerpt  = article.get_text(strip=True)
        if title_el and is_insurtech_related(excerpt):
            title = title_el.get_text(strip=True)
            url   = link_el["href"] if link_el else "https://www.eu-startups.com"
            companies.append({
                "name":    title,
                "source":  "EU Startups",
                "url":     url,
                "snippet": excerpt[:200]
            })
    return companies[:5]

def parse_tech_eu(html):
    """tech.eu — European tech & startup news"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for article in soup.select("article, .post, [class*='article'], [class*='story']"):
        title_el = article.select_one("h2, h3, h4")
        link_el  = article.select_one("a[href]")
        excerpt  = article.get_text(strip=True)
        if title_el and is_insurtech_related(excerpt):
            title = title_el.get_text(strip=True)
            url   = link_el["href"] if link_el else "https://tech.eu"
            if url.startswith("/"):
                url = "https://tech.eu" + url
            companies.append({
                "name":    title,
                "source":  "Tech.eu",
                "url":     url,
                "snippet": excerpt[:200]
            })
    return companies[:5]

def parse_sifted(html):
    """sifted.eu — European startup intelligence"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for article in soup.select("article, [class*='card'], [class*='story']"):
        title_el = article.select_one("h2, h3, h4")
        link_el  = article.select_one("a[href]")
        excerpt  = article.get_text(strip=True)
        if title_el and is_insurtech_related(excerpt):
            title = title_el.get_text(strip=True)
            url   = link_el["href"] if link_el else "https://sifted.eu"
            if url.startswith("/"):
                url = "https://sifted.eu" + url
            companies.append({
                "name":    title,
                "source":  "Sifted",
                "url":     url,
                "snippet": excerpt[:200]
            })
    return companies[:5]

def parse_fintech_global(html):
    """fintech.global — insurtech-specific news and company launches"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for article in soup.select("article, .post, [class*='post']"):
        title_el = article.select_one("h2, h3, .entry-title")
        link_el  = article.select_one("a[href]")
        excerpt  = article.get_text(strip=True)
        if title_el:
            title = title_el.get_text(strip=True)
            url   = link_el["href"] if link_el else "https://fintech.global"
            if url.startswith("/"):
                url = "https://fintech.global" + url
            companies.append({
                "name":    title,
                "source":  "Fintech Global",
                "url":     url,
                "snippet": excerpt[:200]
            })
    return companies[:5]

def parse_instech_london(html):
    """instech.london — dedicated insurtech news"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for article in soup.select("article, .post, [class*='post'], [class*='news']"):
        title_el = article.select_one("h2, h3, h4")
        link_el  = article.select_one("a[href]")
        excerpt  = article.get_text(strip=True)
        if title_el:
            title = title_el.get_text(strip=True)
            url   = link_el["href"] if link_el else "https://www.instech.london"
            if url.startswith("/"):
                url = "https://www.instech.london" + url
            companies.append({
                "name":    title,
                "source":  "InsTech London",
                "url":     url,
                "snippet": excerpt[:200]
            })
    return companies[:5]

# ── News sources to scan ──────────────────────────────────────────────────────
COMPANY_SOURCES = [
    {
        "name":   "EU Startups — Insurtech",
        "url":    "https://www.eu-startups.com/?s=insurtech",
        "parser": parse_eu_startups,
    },
    {
        "name":   "Tech.eu — Insurtech",
        "url":    "https://tech.eu/?s=insurtech",
        "parser": parse_tech_eu,
    },
    {
        "name":   "Sifted — Insurance",
        "url":    "https://sifted.eu/?s=insurtech",
        "parser": parse_sifted,
    },
    {
        "name":   "Fintech Global — Insurtech",
        "url":    "https://fintech.global/category/insurtech/",
        "parser": parse_fintech_global,
    },
    {
        "name":   "InsTech London — News",
        "url":    "https://www.instech.london/news/",
        "parser": parse_instech_london,
    },
]

# ── Core logic ────────────────────────────────────────────────────────────────

def load_seen_companies():
    if os.path.exists(SEEN_COMPANIES_FILE):
        with open(SEEN_COMPANIES_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_companies(seen):
    with open(SEEN_COMPANIES_FILE, "w") as f:
        json.dump(list(seen), f)

def scrape_all_sources():
    results = []
    for source in COMPANY_SOURCES:
        print(f"Scanning {source['name']}...")
        html = fetch(source["url"])
        if html:
            companies = source["parser"](html)
            print(f"  → Found {len(companies)} insurtech mention(s)")
            results.extend(companies)
    return results

def find_new_companies(all_companies, seen):
    new = []
    for company in all_companies:
        key = f"{company['source']}|{company['name']}"
        if key not in seen:
            new.append((key, company))
    # Deduplicate by name
    seen_names = set()
    deduped = []
    for key, company in new:
        if company["name"] not in seen_names and len(company["name"]) > 10:
            seen_names.add(company["name"])
            deduped.append((key, company))
    return deduped

def send_email(new_companies):
    today = datetime.today().strftime('%d %b %Y')
    subject = f"🚀 {len(new_companies)} New Insurtech Compan{'y' if len(new_companies)==1 else 'ies'} Detected — {today}"

    rows = ""
    for _, company in new_companies:
        snippet = company.get("snippet", "")[:150] + "..." if company.get("snippet") else ""
        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;font-weight:bold;color:#1a1a2e;">
            {company['name']}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;color:#666;font-size:13px;">
            {company['source']}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;font-size:12px;color:#555;">
            {snippet}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            <a href="{company['url']}" style="color:#0066cc;white-space:nowrap;">Read more →</a>
          </td>
        </tr>"""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:800px;margin:auto;padding:20px">
      <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px;border-radius:8px;margin-bottom:24px">
        <h2 style="color:#fff;margin:0">🚀 New Insurtech Companies Detected</h2>
        <p style="color:#aaa;margin:8px 0 0">{today} · Scanned EU Startups, Tech.eu, Sifted, Fintech Global & InsTech London</p>
      </div>
      <p>The following new insurtech companies or funding announcements were found today:</p>
      <table style="width:100%;border-collapse:collapse;margin-top:16px">
        <thead>
          <tr style="background:#f4f4f4">
            <th style="padding:10px;text-align:left;width:25%">Company / Story</th>
            <th style="padding:10px;text-align:left;width:15%">Source</th>
            <th style="padding:10px;text-align:left;width:45%">Summary</th>
            <th style="padding:10px;text-align:left;width:15%">Link</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:30px;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:16px">
        Auto-alert from your EU Insurtech Company Scanner · Runs daily via GitHub Actions
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
    print(f"✅ Email sent with {len(new_companies)} new insurtech compan{'y' if len(new_companies)==1 else 'ies'}.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🔍 Running EU Insurtech Company Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    seen       = load_seen_companies()
    all_found  = scrape_all_sources()
    new_ones   = find_new_companies(all_found, seen)

    if new_ones:
        print(f"🆕 Found {len(new_ones)} new insurtech mention(s)!")
        send_email(new_ones)
        seen.update(key for key, _ in new_ones)
        save_seen_companies(seen)
    else:
        print("✅ No new insurtech companies found today.")

if __name__ == "__main__":
    main()
