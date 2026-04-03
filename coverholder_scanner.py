"""
Lloyd's Coverholder EU Expansion Scanner — Marc Planas
Scans insurance news RSS feeds daily for:
1. New Lloyd's coverholder approvals (UK MGAs / insurtechs)
2. EU expansion signals (new offices, regulatory approvals, hiring)
3. Lloyd's Europe coverholder announcements

Sends email alerts when new companies are detected.
Integrates into the Insuretechdaily GitHub Actions pipeline.
"""

import os
import json
import hashlib
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SEEN_FILE          = "seen_coverholders.json"
WATCHLIST_FILE     = "coverholder_watchlist.json"
TODAY              = datetime.now().strftime("%Y-%m-%d")
HEADERS            = {"User-Agent": "Mozilla/5.0 (compatible; CoverholderScanner/1.0)"}

# ═════════════════════════════════════════════════════════════
# KNOWN WATCHLIST — Recently approved Lloyd's coverholders
# expanding to EU. Manually curated, auto-enriched by scanner.
# ═════════════════════════════════════════════════════════════

KNOWN_COVERHOLDERS = [
    {
        "name": "Aspect MGA",
        "status": "Lloyd's Europe coverholder (Feb 2026)",
        "sector": "Complex/high-hazard property",
        "eu_markets": "Netherlands, Ireland, Scandinavia, Spain, Germany, France, Belgium",
        "website": "https://www.aspectmga.com",
        "careers": "https://www.aspectmga.com/careers",
        "priority": "HIGH",
        "notes": "52% YoY growth. Expanding into Spain. Key hire opportunity.",
    },
    {
        "name": "Amiga Specialty",
        "status": "Lloyd's + Accelerant capacity (Dec 2025–Mar 2026)",
        "sector": "D&O, Prof Indemnity, Financial Institutions, Transactional Risk",
        "eu_markets": "UK and Europe core, international expansion",
        "website": "https://www.amigaspecialty.com",
        "careers": "https://www.amigaspecialty.com/careers",
        "priority": "HIGH",
        "notes": "Founded Jun 2025, backed by BP Marsh then Sodalis Capital. Fast-growing.",
    },
    {
        "name": "Helmsgate",
        "status": "Lloyd's coverholder (Sep 2025)",
        "sector": "Waste & recycling property",
        "eu_markets": "UK, Australia, NZ — exploring new territories",
        "website": "https://www.helmsgate.com",
        "careers": "",
        "priority": "MEDIUM",
        "notes": "OneAdvent-managed. Niche waste/recycling sector.",
    },
    {
        "name": "Amphitrite Underwriting",
        "status": "Lloyd's coverholder (Sep 2024)",
        "sector": "Marine specialty",
        "eu_markets": "London-based, international marine expansion",
        "website": "https://www.amphitriteuw.com",
        "careers": "",
        "priority": "MEDIUM",
        "notes": "Specialist marine MGA.",
    },
    {
        "name": "Loadsure",
        "status": "Lloyd's coverholder",
        "sector": "Freight/cargo insurtech",
        "eu_markets": "Benelux, Denmark, Finland, France, Germany, Norway, Sweden",
        "website": "https://www.loadsure.net",
        "careers": "https://www.loadsure.net/careers",
        "priority": "HIGH",
        "notes": "AI-driven cargo insurance. Active EU operations since 2024.",
    },
    {
        "name": "Augmented UW",
        "status": "MGA launch (2025), Artificial Labs platform",
        "sector": "AI-driven smart-follow underwriting",
        "eu_markets": "London market, digital EU broker infrastructure",
        "website": "https://www.augmented.insure",
        "careers": "",
        "priority": "MEDIUM",
        "notes": "AI/digital MGA. Early stage but watch for EU hiring.",
    },
    {
        "name": "Specialty MGA UK",
        "status": "Lloyd's coverholder (Jul 2023)",
        "sector": "A&H, Construction, Cyber, Energy, Forestry",
        "eu_markets": "UK and international specialty",
        "website": "https://www.specialtymga.co.uk",
        "careers": "",
        "priority": "LOW",
        "notes": "Includes ForestRe parametric wildfire team.",
    },
]

# ═════════════════════════════════════════════════════════════
# DETECTION KEYWORDS
# ═════════════════════════════════════════════════════════════

COVERHOLDER_KEYWORDS = [
    "coverholder", "cover holder", "lloyd's coverholder", "lloyd's europe coverholder",
    "binding authority", "delegated authority", "lloyd's europe",
    "coverholder status", "coverholder approved", "coverholder approval",
]

EU_EXPANSION_KEYWORDS = [
    "eu expansion", "european expansion", "expanding to europe",
    "european operations", "eu market entry", "continental expansion",
    "lloyd's europe", "eea", "european economic area",
    "spain", "germany", "france", "netherlands", "ireland",
    "scandinavia", "belgium", "italy", "portugal",
    "pan-european", "passporting", "eu licence",
]

MGA_KEYWORDS = [
    "mga", "managing general agent", "insurtech", "specialty mga",
    "mgu", "managing general underwriter", "delegated underwriting",
]

# ═════════════════════════════════════════════════════════════
# NEWS RSS FEEDS — Insurance-specific, tested and working
# ═════════════════════════════════════════════════════════════

RSS_FEEDS = [
    {"name": "Insurance Edge",       "url": "https://insurance-edge.net/feed/"},
    {"name": "InsTech London",       "url": "https://www.instech.london/feed"},
    {"name": "Reinsurance News",     "url": "https://www.reinsurancene.ws/feed/"},
    {"name": "Insurance Business UK", "url": "https://www.insurancebusinessmag.com/uk/rss/news/breaking-news/"},
    {"name": "EU-Startups Insurtech", "url": "https://www.eu-startups.com/category/insurtech/feed/"},
    {"name": "Sifted",               "url": "https://sifted.eu/feed"},
    {"name": "AltFi",                "url": "https://www.altfi.com/feed"},
]

# ═════════════════════════════════════════════════════════════
# CAREER PAGE MONITORING — Check watchlist companies for jobs
# ═════════════════════════════════════════════════════════════

EU_CITIES_IN_JOBS = [
    "spain", "barcelona", "madrid", "amsterdam", "dublin", "paris",
    "berlin", "munich", "frankfurt", "brussels", "copenhagen",
    "stockholm", "oslo", "milan", "lisbon", "vienna", "warsaw",
    "operations", "ops manager", "programme manager", "compliance",
]


# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════

def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r if r.status_code == 200 else None
    except Exception as e:
        print(f"    fetch error: {str(e)[:50]}")
        return None

def sig_id(title, source):
    return hashlib.md5(f"{title}|{source}".lower().encode()).hexdigest()[:12]

def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()

def save_seen(seen):
    json.dump(list(seen), open(SEEN_FILE, "w"))

def has_keywords(text, keywords):
    t = text.lower()
    return any(kw in t for kw in keywords)


# ═════════════════════════════════════════════════════════════
# SCANNER 1 — RSS feeds for new coverholder announcements
# ═════════════════════════════════════════════════════════════

def scan_rss_for_coverholders():
    """Scan insurance news RSS for coverholder + EU expansion signals."""
    signals = []
    for feed in RSS_FEEDS:
        r = fetch(feed["url"])
        if not r:
            print(f"  {feed['name']}: no response")
            continue
        try:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            count = 0
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                link  = (item.findtext("link") or "").strip()
                text  = f"{title} {desc}"

                is_coverholder = has_keywords(text, COVERHOLDER_KEYWORDS)
                is_mga = has_keywords(text, MGA_KEYWORDS)
                is_eu = has_keywords(text, EU_EXPANSION_KEYWORDS)

                # We want: coverholder news OR (MGA + EU expansion)
                if is_coverholder or (is_mga and is_eu):
                    signal_type = "coverholder" if is_coverholder else "mga_eu_expansion"
                    signals.append({
                        "title": title[:150],
                        "source": feed["name"],
                        "url": link,
                        "snippet": desc[:300],
                        "type": signal_type,
                        "has_eu": is_eu,
                    })
                    count += 1
            print(f"  {feed['name']}: {count} signal(s) from {len(items)} articles")
        except ET.ParseError as e:
            print(f"  {feed['name']}: XML error — {e}")
        except Exception as e:
            print(f"  {feed['name']}: error — {e}")
    return signals


# ═════════════════════════════════════════════════════════════
# SCANNER 2 — Check watchlist career pages for EU ops jobs
# ═════════════════════════════════════════════════════════════

def scan_career_pages():
    """Check known coverholder career pages for EU operations roles."""
    signals = []
    for co in KNOWN_COVERHOLDERS:
        if not co.get("careers"):
            continue
        r = fetch(co["careers"])
        if not r:
            continue
        text = r.text.lower()
        found = [kw for kw in EU_CITIES_IN_JOBS if kw in text]
        if found:
            signals.append({
                "title": f"{co['name']}: EU/ops keywords on careers page",
                "source": "Career page check",
                "url": co["careers"],
                "snippet": f"Keywords found: {', '.join(found[:8])}",
                "type": "careers_signal",
                "has_eu": True,
                "company": co["name"],
                "priority": co["priority"],
            })
            print(f"  {co['name']}: {len(found)} keyword(s) found")
        else:
            print(f"  {co['name']}: no EU/ops keywords")
    return signals


# ═════════════════════════════════════════════════════════════
# DEDUPLICATION & FILTERING
# ═════════════════════════════════════════════════════════════

def filter_new(signals, seen):
    new = []
    seen_titles = set()
    for s in signals:
        sid = sig_id(s["title"], s["source"])
        short = s["title"][:60].lower()
        if sid not in seen and short not in seen_titles:
            seen.add(sid)
            seen_titles.add(short)
            new.append(s)
    return new


# ═════════════════════════════════════════════════════════════
# EMAIL ALERT
# ═════════════════════════════════════════════════════════════

def send_alert(new_signals):
    if not GMAIL_USER or not new_signals:
        return

    coverholder_sigs = [s for s in new_signals if s["type"] == "coverholder"]
    eu_sigs = [s for s in new_signals if s["type"] == "mga_eu_expansion"]
    career_sigs = [s for s in new_signals if s["type"] == "careers_signal"]

    subject = f"🏛️ Lloyd's Coverholder Alert — {len(new_signals)} signal(s) — {TODAY}"

    def make_rows(sigs, label):
        if not sigs:
            return ""
        rows = f"<h3 style='color:#1a2744;margin-top:20px;'>{label}</h3>"
        for s in sigs:
            eu_badge = " <span style='background:#d4edda;color:#155724;padding:2px 8px;border-radius:10px;font-size:11px;'>EU</span>" if s.get("has_eu") else ""
            priority = s.get("priority", "")
            pri_badge = f" <span style='background:#fff3cd;color:#856404;padding:2px 8px;border-radius:10px;font-size:11px;'>{priority}</span>" if priority else ""
            rows += f"""
            <div style="border-left:4px solid #2563eb;padding:10px 14px;margin:10px 0;background:#f8fafc;border-radius:0 6px 6px 0;">
              <div style="font-weight:bold;font-size:13px;">{s['title'][:100]}{eu_badge}{pri_badge}</div>
              <div style="font-size:12px;color:#666;margin:4px 0;">{s['source']}</div>
              <div style="font-size:11px;color:#555;margin:4px 0;font-style:italic;">{s.get('snippet','')[:200]}</div>
              <a href="{s['url']}" style="color:#2563eb;font-size:12px;">Read more →</a>
            </div>"""
        return rows

    # Watchlist summary table
    watchlist_rows = ""
    for co in KNOWN_COVERHOLDERS:
        pri_color = {"HIGH": "#16a34a", "MEDIUM": "#d97706", "LOW": "#9ca3af"}.get(co["priority"], "#6b7280")
        watchlist_rows += f"""<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;font-weight:bold;">{co['name']}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:11px;">{co['sector'][:40]}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:11px;">{co['eu_markets'][:50]}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:center;"><b style="color:{pri_color};">{co['priority']}</b></td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;"><a href="{co['website']}" style="color:#2563eb;font-size:11px;">Web</a>
          {f' · <a href="{co["careers"]}" style="color:#2563eb;font-size:11px;">Careers</a>' if co.get('careers') else ''}</td>
        </tr>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
<div style="background:linear-gradient(135deg,#1a2744,#2563eb);padding:20px;border-radius:8px;margin-bottom:16px;">
  <h2 style="color:#fff;margin:0;">🏛️ Lloyd's Coverholder EU Expansion Alert</h2>
  <p style="color:#ddd;margin:6px 0 0;">{TODAY} · {len(new_signals)} new signal(s)</p>
</div>

{make_rows(coverholder_sigs, "🏛️ New Coverholder Approvals")}
{make_rows(eu_sigs, "🌍 MGA EU Expansion News")}
{make_rows(career_sigs, "💼 Career Page Signals")}

<h3 style="color:#1a2744;margin-top:24px;">📋 Active Watchlist — Lloyd's Coverholders Expanding to EU</h3>
<table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #eee;">
  <tr style="background:#1a2744;color:white;">
    <th style="padding:8px;">Company</th><th style="padding:8px;">Sector</th>
    <th style="padding:8px;">EU Markets</th><th style="padding:8px;">Priority</th><th style="padding:8px;">Links</th>
  </tr>
  {watchlist_rows}
</table>

<div style="margin-top:16px;padding:14px;background:#fff3cd;border-radius:6px;border-left:4px solid #ffc107;">
  <b>⚡ Action:</b> Check HIGH-priority career pages for operations roles.
  Aspect MGA is expanding into Spain — proactive outreach recommended.
</div>

<p style="font-size:11px;color:#999;margin-top:20px;border-top:1px solid #eee;padding-top:12px;">
  Lloyd's Coverholder Scanner · {len(RSS_FEEDS)} RSS feeds + {len(KNOWN_COVERHOLDERS)} watchlist companies · {TODAY}
</p></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Coverholder Scanner <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Alert sent: {len(new_signals)} signal(s)")
    except Exception as e:
        print(f"❌ Email error: {e}")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*55}")
    print(f"  Lloyd's Coverholder EU Expansion Scanner — {TODAY}")
    print(f"{'='*55}\n")

    seen = load_seen()

    print("📡 Scanning RSS feeds for coverholder news...")
    all_signals = scan_rss_for_coverholders()

    print("\n💼 Checking watchlist career pages...")
    all_signals += scan_career_pages()

    print(f"\n📊 Total signals found: {len(all_signals)}")

    new_signals = filter_new(all_signals, seen)
    print(f"🆕 New (not seen before): {len(new_signals)}")

    if new_signals:
        send_alert(new_signals)
        save_seen(seen)
    else:
        print("✅ No new coverholder/expansion signals today.")
        save_seen(seen)

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
