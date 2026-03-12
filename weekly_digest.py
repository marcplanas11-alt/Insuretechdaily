"""
Weekly Digest — Marc Planas Job Hunt
Runs every Monday at 8am UTC.
Reads job_tracker.csv + expansion_weekly.json and sends a combined summary email.
"""

import os
import csv
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import Counter

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TRACKER_FILE       = "job_tracker.csv"
EXPANSION_FILE     = "expansion_weekly.json"
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

def load_expansions():
    try:
        data = json.load(open(EXPANSION_FILE))
        return [e for e in data if e.get("date", "") >= WEEK_AGO]
    except Exception:
        return []

def send_digest(all_rows, expansion_signals):
    this_week      = [r for r in all_rows if r.get("Date", "") >= WEEK_AGO]
    total_all      = len(all_rows)
    total_week     = len(this_week)
    companies_week = Counter(r["Company"] for r in this_week)
    sources_week   = Counter(r["Source"] for r in this_week)
    scores_week    = [int(r["Score"]) for r in this_week if r.get("Score", "").isdigit()]
    avg_score      = round(sum(scores_week) / len(scores_week), 1) if scores_week else 0
    top_score      = max(scores_week) if scores_week else 0
    applied        = [r for r in all_rows if "Applied" in r.get("Status", "")]
    pending        = [r for r in all_rows if r.get("Status", "") == "New — Not Applied"]

    exp_companies  = Counter(e["company"] for e in expansion_signals)
    exp_high_hire  = [e for e in expansion_signals if e.get("hiring_opportunity") == "high"]
    exp_top        = sorted(expansion_signals, key=lambda x: x.get("score", 0), reverse=True)[:5]

    recent_rows_html = ""
    for r in sorted(this_week, key=lambda x: x.get("Score", "0"), reverse=True)[:10]:
        recent_rows_html += f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("Date","")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;"><a href="{r.get("Link","")}" style="color:#4a4a8a;">{r.get("Title","")}</a></td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("Company","")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:center;"><b>{r.get("Score","?")}%</b></td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("Salary Info","?")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{r.get("Status","")}</td></tr>'

    top_cos   = "".join(f"<li><b>{co}</b> — {cnt}</li>" for co, cnt in companies_week.most_common(5))
    top_srcs  = "".join(f"<li>{s} — {cnt}</li>" for s, cnt in sources_week.most_common(5))

    exp_rows_html = ""
    for e in exp_top:
        sc = e.get("score", 0)
        col = "#1a7a3a" if sc >= 80 else "#4a4a8a" if sc >= 60 else "#888"
        hb  = {"high": '<span style="background:#d4edda;color:#155724;padding:2px 6px;border-radius:10px;font-size:11px;">High</span>', "medium": '<span style="background:#fff3cd;color:#856404;padding:2px 6px;border-radius:10px;font-size:11px;">Mid</span>', "low": '<span style="background:#f8d7da;color:#721c24;padding:2px 6px;border-radius:10px;font-size:11px;">Low</span>'}.get(e.get("hiring_opportunity", ""), "")
        exp_rows_html += f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;">{e.get("date","")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;font-weight:bold;">{e.get("company","")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;"><a href="{e.get("link","")}" style="color:#4a4a8a;">{e.get("title","")[:70]}</a></td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{e.get("eu_markets","")}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:center;"><b style="color:{col};">{sc}%</b></td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{hb}</td></tr>'

    exp_cos_html = "".join(f"<li><b>{co}</b> — {cnt} signal(s)</li>" for co, cnt in exp_companies.most_common(5))
    high_hire_alert = (f'<div style="margin-top:16px;padding:14px;background:#d4edda;border-radius:6px;border-left:4px solid #28a745;"><b>High hiring opportunity:</b> {", ".join(set(e["company"] for e in exp_high_hire))} — consider proactive outreach.</div>' if exp_high_hire else "")

    exp_section = f"""
  <hr style="border:1px solid #ddd;margin:28px 0 20px;">
  <h3 style="color:#1a1a2e;">EU Expansion Radar — This Week</h3>
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="background:#1a6e3c;color:white;padding:14px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:26px;font-weight:bold;">{len(expansion_signals)}</div><div style="font-size:11px;opacity:.9;">Expansion Signals</div></td>
      <td style="width:4%;"></td>
      <td style="background:#2c5f8a;color:white;padding:14px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:26px;font-weight:bold;">{len(exp_companies)}</div><div style="font-size:11px;opacity:.9;">Companies Moving</div></td>
      <td style="width:4%;"></td>
      <td style="background:#7b3f9e;color:white;padding:14px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:26px;font-weight:bold;">{len(exp_high_hire)}</div><div style="font-size:11px;opacity:.9;">High Hiring Signals</div></td>
      <td style="width:4%;"></td>
      <td style="background:#c05c1a;color:white;padding:14px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:26px;font-weight:bold;">{exp_top[0]["score"] if exp_top else 0}%</div><div style="font-size:11px;opacity:.9;">Top Confidence</div></td>
    </tr>
  </table>
  <h3 style="color:#1a1a2e;margin-top:20px;">Active Expanding Companies</h3>
  <ul style="font-size:13px;">{exp_cos_html or "<li>None this week</li>"}</ul>
  <h3 style="color:#1a1a2e;">Top Expansion Signals</h3>
  <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #eee;">
    <tr style="background:#1a6e3c;color:white;">
      <th style="padding:8px 10px;text-align:left;">Date</th><th style="padding:8px 10px;text-align:left;">Company</th><th style="padding:8px 10px;text-align:left;">Signal</th><th style="padding:8px 10px;text-align:left;">EU Markets</th><th style="padding:8px 10px;text-align:center;">Score</th><th style="padding:8px 10px;text-align:left;">Hiring</th>
    </tr>
    {exp_rows_html or '<tr><td colspan="6" style="padding:12px;text-align:center;color:#888;">No signals this week</td></tr>'}
  </table>
  {high_hire_alert}
""" if expansion_signals else ""

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:720px;margin:auto;">
<div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
  <h2 style="margin:0;">Weekly Intelligence Digest</h2>
  <p style="margin:6px 0 0;opacity:.8;">Week ending {TODAY} · Marc Planas · EU Insurtech</p>
</div>
<div style="background:#f8f8ff;padding:20px 24px;">
  <h3 style="color:#1a1a2e;">Job Matches — This Week</h3>
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="background:#4a4a8a;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:28px;font-weight:bold;">{total_week}</div><div style="font-size:11px;opacity:.9;">New Matches</div></td>
      <td style="width:4%;"></td>
      <td style="background:#2d6a4f;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:28px;font-weight:bold;">{avg_score}%</div><div style="font-size:11px;opacity:.9;">Avg Score</div></td>
      <td style="width:4%;"></td>
      <td style="background:#e76f51;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:28px;font-weight:bold;">{top_score}%</div><div style="font-size:11px;opacity:.9;">Top Score</div></td>
      <td style="width:4%;"></td>
      <td style="background:#457b9d;color:white;padding:16px;text-align:center;border-radius:6px;width:22%;"><div style="font-size:28px;font-weight:bold;">{total_all}</div><div style="font-size:11px;opacity:.9;">All Time</div></td>
    </tr>
  </table>
  <h3 style="color:#1a1a2e;margin-top:24px;">Application Pipeline</h3>
  <table style="width:100%;font-size:13px;">
    <tr><td>Not yet applied</td><td><b>{len(pending)}</b></td></tr>
    <tr><td>Applied</td><td><b>{len(applied)}</b></td></tr>
  </table>
  <h3 style="color:#1a1a2e;margin-top:20px;">Top Companies This Week</h3>
  <ul style="font-size:13px;">{top_cos or "<li>None</li>"}</ul>
  <h3 style="color:#1a1a2e;">Top Sources</h3>
  <ul style="font-size:13px;">{top_srcs or "<li>None</li>"}</ul>
  <h3 style="color:#1a1a2e;margin-top:20px;">This Week's Matches (Top 10)</h3>
  <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #eee;">
    <tr style="background:#4a4a8a;color:white;">
      <th style="padding:8px 10px;text-align:left;">Date</th><th style="padding:8px 10px;text-align:left;">Role</th><th style="padding:8px 10px;text-align:left;">Company</th><th style="padding:8px 10px;text-align:center;">Score</th><th style="padding:8px 10px;text-align:left;">Salary</th><th style="padding:8px 10px;text-align:left;">Status</th>
    </tr>
    {recent_rows_html or '<tr><td colspan="6" style="padding:12px;text-align:center;color:#888;">No matches this week</td></tr>'}
  </table>
  {exp_section}
  <div style="margin-top:24px;padding:16px;background:#fff3cd;border-radius:6px;border-left:4px solid #ffc107;">
    <b>Action Reminder</b><br>
    {len(pending)} matched job(s) not yet applied to.
    {"Follow up on applications older than 7 days." if applied else ""}
  </div>
</div>
<div style="background:#1a1a2e;color:white;padding:12px 24px;border-radius:0 0 8px 8px;font-size:11px;opacity:.8;">
  Auto-generated by EU Insurtech Job Hunter + EU Expansion Scanner · {TODAY}
</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Weekly Intelligence Digest {TODAY} - {total_week} job matches, {len(expansion_signals)} expansion signals"
    msg["From"]    = f"Insurtech Job Hunter <{GMAIL_USER}>"
    msg["To"]      = GMAIL_USER
    msg["Reply-To"]= GMAIL_USER
    msg["X-Mailer"]= "Python/smtplib"
    msg.attach(MIMEText(f"Weekly Digest {TODAY}\nJob matches: {total_week} | Expansion signals: {len(expansion_signals)}", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"Weekly digest sent. {total_week} job matches, {len(expansion_signals)} expansion signals.")
    except Exception as e:
        print(f"Email error: {e}")

if __name__ == "__main__":
    send_digest(load_tracker(), load_expansions())
