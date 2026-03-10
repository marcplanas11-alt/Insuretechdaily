"""
Weekly Digest — Marc Planas Job Hunt
Runs every Monday at 8am UTC.
Reads job_tracker.csv and sends a summary email.
"""

import os
import csv
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import Counter

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TRACKER_FILE       = "job_tracker.csv"
TODAY              = datetime.now().strftime("%Y-%m-%d")
WEEK_AGO           = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

def load_tracker():
    rows = []
    try:
        with open(TRACKER_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        pass
    return rows

def send_digest(all_rows):
    this_week = [r for r in all_rows if r.get("Date","") >= WEEK_AGO]
    total_all  = len(all_rows)
    total_week = len(this_week)

    # Stats
    companies_week = Counter(r["Company"] for r in this_week)
    sources_week   = Counter(r["Source"] for r in this_week)
    scores_week    = [int(r["Score"]) for r in this_week if r.get("Score","").isdigit()]
    avg_score      = round(sum(scores_week) / len(scores_week), 1) if scores_week else 0
    top_score      = max(scores_week) if scores_week else 0

    applied = [r for r in all_rows if "Applied" in r.get("Status","")]
    pending = [r for r in all_rows if r.get("Status","") == "New — Not Applied"]

    # Build recent matches table
    recent_rows_html = ""
    for r in sorted(this_week, key=lambda x: x.get("Score","0"), reverse=True)[:10]:
        recent_rows_html += f"""
<tr>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get('Date','')}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;"><a href="{r.get('Link','')}" style="color:#4a4a8a;">{r.get('Title','')}</a></td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get('Company','')}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:center;"><b>{r.get('Score','?')}%</b></td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get('Salary Info','?')}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get('Status','')}</td>
</tr>"""

    top_companies_html = "".join(
        f"<li><b>{co}</b> — {cnt} match(es)</li>"
        for co, cnt in companies_week.most_common(5)
    )
    top_sources_html = "".join(
        f"<li>{src} — {cnt}</li>"
        for src, cnt in sources_week.most_common(5)
    )

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">

<div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
  <h2 style="margin:0;">📊 Weekly Job Hunt Digest</h2>
  <p style="margin:6px 0 0;opacity:0.8;">Week ending {TODAY} · Marc Planas</p>
</div>

<div style="background:#f8f8ff;padding:20px 24px;">

  <h3 style="color:#1a1a2e;">This Week at a Glance</h3>
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="background:#4a4a8a;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;">
        <div style="font-size:28px;font-weight:bold;">{total_week}</div>
        <div style="font-size:11px;opacity:0.9;">New Matches</div>
      </td>
      <td style="width:4%;"></td>
      <td style="background:#2d6a4f;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;">
        <div style="font-size:28px;font-weight:bold;">{avg_score}%</div>
        <div style="font-size:11px;opacity:0.9;">Avg Match Score</div>
      </td>
      <td style="width:4%;"></td>
      <td style="background:#e76f51;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;">
        <div style="font-size:28px;font-weight:bold;">{top_score}%</div>
        <div style="font-size:11px;opacity:0.9;">Top Score</div>
      </td>
      <td style="width:4%;"></td>
      <td style="background:#457b9d;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;">
        <div style="font-size:28px;font-weight:bold;">{total_all}</div>
        <div style="font-size:11px;opacity:0.9;">Total (All Time)</div>
      </td>
    </tr>
  </table>

  <h3 style="color:#1a1a2e;margin-top:24px;">📋 Application Pipeline</h3>
  <table style="width:100%;font-size:13px;">
    <tr>
      <td>🟡 Not yet applied</td><td><b>{len(pending)}</b></td>
    </tr>
    <tr>
      <td>✅ Applied</td><td><b>{len(applied)}</b></td>
    </tr>
  </table>

  <h3 style="color:#1a1a2e;margin-top:24px;">🏆 Top Companies This Week</h3>
  <ul style="font-size:13px;">{top_companies_html if top_companies_html else "<li>No matches this week</li>"}</ul>

  <h3 style="color:#1a1a2e;">📡 Top Sources This Week</h3>
  <ul style="font-size:13px;">{top_sources_html if top_sources_html else "<li>No data</li>"}</ul>

  <h3 style="color:#1a1a2e;margin-top:24px;">🎯 This Week's Matches (Top 10)</h3>
  <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #eee;">
    <tr style="background:#4a4a8a;color:white;">
      <th style="padding:8px 10px;text-align:left;">Date</th>
      <th style="padding:8px 10px;text-align:left;">Role</th>
      <th style="padding:8px 10px;text-align:left;">Company</th>
      <th style="padding:8px 10px;text-align:center;">Score</th>
      <th style="padding:8px 10px;text-align:left;">Salary</th>
      <th style="padding:8px 10px;text-align:left;">Status</th>
    </tr>
    {recent_rows_html if recent_rows_html else '<tr><td colspan="6" style="padding:12px;text-align:center;color:#888;">No matches this week</td></tr>'}
  </table>

  <div style="margin-top:24px;padding:16px;background:#fff3cd;border-radius:6px;border-left:4px solid #ffc107;">
    <b>💡 Action Reminder</b><br>
    You have <b>{len(pending)}</b> matched job(s) not yet applied to.
    {"Consider following up on any applications older than 7 days." if len(applied) > 0 else ""}
  </div>

</div>

<div style="background:#1a1a2e;color:white;padding:12px 24px;border-radius:0 0 8px 8px;font-size:11px;opacity:0.8;">
  Auto-generated by EU Insurtech Job Hunter · {TODAY}
</div>

</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Weekly Job Hunt Digest — {TODAY}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"Weekly digest sent. {total_week} matches this week, {total_all} total.")
    except Exception as e:
        print(f"Email error: {e}")

if __name__ == "__main__":
    rows = load_tracker()
    send_digest(rows)
