"""
AI Job Hunter — Marc Planas
Scans multiple job sources daily, scores matches with Claude AI,
generates PDF CVs + cover letters, researches companies, and logs to tracker.
"""

import os
import json
import csv
import smtplib
import hashlib
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
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("reportlab not installed — PDF generation disabled")

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

SEEN_JOBS_FILE = "seen_jobs.json"
TRACKER_FILE   = "job_tracker.csv"
TODAY          = datetime.now().strftime("%Y-%m-%d")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobHunterBot/1.0)"}

# ─────────────────────────────────────────────────────────────
# SOURCES
# ─────────────────────────────────────────────────────────────

INDEED_RSS_FEEDS = [
    "https://www.indeed.com/rss?q=insurtech+operations&l=remote&sort=date",
    "https://www.indeed.com/rss?q=MGA+insurance&l=remote&sort=date",
    "https://www.indeed.com/rss?q=insurtech+product+manager&l=remote&sort=date",
    "https://www.indeed.com/rss?q=insurance+digital+transformation&l=remote&sort=date",
    "https://www.indeed.co.uk/rss?q=insurtech&l=remote&sort=date",
]

REMOTE_BOARDS = [
    {"name": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss", "type": "rss"},
    {"name": "We Work Remotely Ops", "url": "https://weworkremotely.com/categories/remote-management-finance-jobs.rss", "type": "rss"},
    {"name": "Remote OK", "url": "https://remoteok.com/api", "type": "json"},
    {"name": "Remotive", "url": "https://remotive.com/api/remote-jobs?category=finance&limit=30", "type": "json_remotive"},
]

# Companies using Ashby ATS — fetched via public JSON API (no JS needed)
ASHBY_COMPANIES = [
    {"name": "Alan",                "client": "alan"},
    {"name": "Kota",                "client": "kota"},
    {"name": "Artificial Labs",     "client": "artificial"},
    {"name": "Cytora",              "client": "cytora"},
    {"name": "wefox",               "client": "wefox"},
    {"name": "Inaza",               "client": "inaza"},
    {"name": "Lassie",              "client": "lassie"},
    {"name": "Descartes Underwriting", "client": "descartesunderwriting"},
]

# Companies using Greenhouse ATS — public JSON API
GREENHOUSE_COMPANIES = [
    {"name": "Guidewire",           "client": "guidewire"},
    {"name": "Duck Creek",          "client": "duckcreek"},
    {"name": "Shift Technology",    "client": "shifttechnology"},
    {"name": "Tractable",           "client": "tractable"},
    {"name": "FINEOS",              "client": "fineos"},
    {"name": "CoverGo",             "client": "covergo"},
]

# Companies using Lever ATS — public JSON API
LEVER_COMPANIES = [
    {"name": "Wakam",               "client": "wakam"},
    {"name": "Laka",                "client": "laka"},
]

# Companies with standard HTML careers pages (fallback scrape)
INSURTECH_COMPANIES = [
    {"name": "Novidea",     "url": "https://www.novidea.com/careers",          "keywords": ["insurance"]},
    {"name": "EIS Group",   "url": "https://eisgroup.com/careers",             "keywords": ["insurance"]},
    {"name": "Majesco",     "url": "https://www.majesco.com/careers",          "keywords": ["insurance"]},
    {"name": "Kayna",       "url": "https://www.kayna.io/careers",             "keywords": ["insurance"]},
    {"name": "Blink Parametric", "url": "https://www.blinkparametric.com/careers", "keywords": ["parametric"]},
]

RECRUITERS = [
    {"name": "IDEX Consulting", "url": "https://www.idexconsulting.com/jobs/?search=insurtech"},
    {"name": "Barclay Simpson", "url": "https://www.barclaysimpson.com/jobs/?search=insurance"},
    {"name": "Hays Spain", "url": "https://www.hays.es/en/job/search-jobs/q-insurance"},
    {"name": "Michael Page Spain", "url": "https://www.michaelpage.es/jobs/insurance"},
    {"name": "Robert Walters", "url": "https://www.robertwalters.es/jobs.html?query=insurance"},
    {"name": "Marks Sattin", "url": "https://www.markssattin.co.uk/jobs/insurance"},
    {"name": "Morgan McKinley", "url": "https://www.morganmckinley.com/jobs?q=insurtech"},
    {"name": "Eames Consulting", "url": "https://www.eamesconsulting.com/jobs/?search=insurance"},
    {"name": "Optio Search", "url": "https://www.optiosearch.com/jobs/?sector=insurance"},
    {"name": "Insnerds Jobs", "url": "https://insnerds.com/jobs"},
    {"name": "InsTech Jobs", "url": "https://www.instech.london/jobs"},
]

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def load_seen_jobs():
    try:
        with open(SEEN_JOBS_FILE) as f:
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
        return requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        print(f"  Fetch error {url[:50]}: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# JOB TRACKER
# ─────────────────────────────────────────────────────────────

def log_to_tracker(job, ai_result):
    file_exists = os.path.exists(TRACKER_FILE)
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date","Title","Company","Source","Score",
                             "Location Type","Salary Info","Reason","Link","Status"])
        writer.writerow([
            TODAY, job.get("title",""), job.get("company",""),
            job.get("source",""), ai_result.get("score",""),
            ai_result.get("location_type",""), ai_result.get("salary_info","not specified"),
            ai_result.get("reason",""), job.get("link",""), "New — Not Applied"
        ])
    print(f"  Logged to tracker: {job['title']} @ {job['company']}")

# ─────────────────────────────────────────────────────────────
# COMPANY RESEARCH
# ─────────────────────────────────────────────────────────────

def research_company(company_name, job_title):
    if not ANTHROPIC_API_KEY:
        return ""
    prompt = f"""Write a concise 'Know Before You Apply' brief about "{company_name}" for a candidate applying for "{job_title}".

Cover in 4-5 bullet points:
- What the company does (insurtech focus)
- Funding stage / size / valuation if known
- Culture and remote work policy
- Recent news or milestones (2024-2025)
- One interview tip

Be factual. If you don't know a specific fact, say so."""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"  Company research error: {e}")
        return ""

# ─────────────────────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────────────────────

def build_pdf_cv(job, ai_result, lang="en"):
    if not REPORTLAB_AVAILABLE:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    name_s   = ParagraphStyle("N", fontSize=22, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#1a1a2e"), spaceAfter=4)
    role_s   = ParagraphStyle("R", fontSize=12, fontName="Helvetica",
                               textColor=colors.HexColor("#4a4a8a"), spaceAfter=2)
    meta_s   = ParagraphStyle("M", fontSize=9, textColor=colors.grey, spaceAfter=10)
    sec_s    = ParagraphStyle("S", fontSize=11, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#1a1a2e"), spaceBefore=12, spaceAfter=4)
    body_s   = ParagraphStyle("B", fontSize=9.5, leading=14, spaceAfter=6)
    bullet_s = ParagraphStyle("BU", fontSize=9.5, leading=14, leftIndent=12, spaceAfter=3)

    summary = ai_result.get("cv_summary_en" if lang == "en" else "cv_summary_es",
                             PROFILE["cv_summary_en"]).strip()
    elems = []
    elems.append(Paragraph(PROFILE["name"], name_s))
    elems.append(Paragraph(job.get("title", "Insurance & Insurtech Professional"), role_s))
    elems.append(Paragraph(f"Email: {PROFILE['email']}  |  Location: {PROFILE['location']}", meta_s))
    elems.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4a4a8a"), spaceAfter=10))

    sec_title_summary = "PROFESSIONAL SUMMARY" if lang == "en" else "PERFIL PROFESIONAL"
    sec_title_skills  = "CORE SKILLS" if lang == "en" else "COMPETENCIAS CLAVE"
    sec_title_exp     = "PROFESSIONAL EXPERIENCE" if lang == "en" else "EXPERIENCIA PROFESIONAL"
    sec_title_lang    = "LANGUAGES" if lang == "en" else "IDIOMAS"

    elems.append(Paragraph(sec_title_summary, sec_s))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    elems.append(Paragraph(summary, body_s))

    elems.append(Paragraph(sec_title_skills, sec_s))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    tdata = [
        ["Insurance & Insurtech", "Technical", "Methodologies"],
        ["Insurance Operations\nMGA Management\nUnderwriting\nLloyd's Market\nParametric Insurance\nEmbedded Insurance",
         "Python\nSQL\nExcel & Data Analysis\nCRM Systems\nAPI Integrations",
         "Agile / Scrum\nStakeholder Management\nP&L Management\nDigital Transformation\nProcess Automation"],
    ]
    t = Table(tdata, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#4a4a8a")),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,0), 9),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,1),(-1,-1), 8.5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("PADDING",(0,0),(-1,-1), 6),
        ("GRID",(0,0),(-1,-1), 0.5, colors.lightgrey),
    ]))
    elems.append(t)

    elems.append(Paragraph(sec_title_exp, sec_s))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    elems.append(Paragraph("<b>Insurance & Insurtech Professional</b> | EU Markets", body_s))
    for b in [
        "Led insurance operations and MGA management across European markets",
        "Delivered digital transformation on insurtech platforms (30%+ efficiency gains)",
        "Built broker and partner relationships across Lloyd's and EU insurance markets",
        "Implemented Agile/Scrum for product and strategy delivery",
        "Developed Python/SQL data pipelines for underwriting and claims analysis",
        "Managed P&L and stakeholder reporting for insurance product lines",
    ]:
        elems.append(Paragraph(f"• {b}", bullet_s))

    elems.append(Paragraph(sec_title_lang, sec_s))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    for ln, lv in [("English","Full professional proficiency"),("Spanish","Native"),("Catalan","Native")]:
        elems.append(Paragraph(f"• <b>{ln}</b> — {lv}", bullet_s))

    elems.append(Spacer(1, 0.4*cm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elems.append(Paragraph(
        f"<i>CV tailored for: {job.get('title','')} at {job.get('company','')} | {TODAY}</i>",
        ParagraphStyle("Ft", fontSize=8, textColor=colors.grey, spaceBefore=4)
    ))
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()


def build_pdf_cover_letter(job, ai_result, lang="en"):
    if not REPORTLAB_AVAILABLE:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)

    hdr_s  = ParagraphStyle("H", fontSize=11, fontName="Helvetica-Bold",
                              textColor=colors.HexColor("#1a1a2e"), spaceAfter=4)
    meta_s = ParagraphStyle("M", fontSize=9, textColor=colors.grey, spaceAfter=16)
    body_s = ParagraphStyle("B", fontSize=10, leading=16, spaceAfter=12)
    re_s   = ParagraphStyle("Re", fontSize=10, fontName="Helvetica-Bold", spaceAfter=16)

    opening = ai_result.get("cover_letter_en" if lang=="en" else "cover_letter_es","").strip()
    company = job.get("company","your company")
    title   = job.get("title","the role")

    if lang == "en":
        paragraphs = [
            f"I am writing to express my strong interest in the {title} position at {company}.",
            opening,
            f"I bring hands-on experience in Python, SQL, Agile/Scrum, and CRM systems, alongside deep domain expertise in insurance operations, MGA management, and Lloyd's market relationships. I am confident these skills will add immediate value at {company}.",
            "I would welcome the opportunity to discuss how my background aligns with your needs. Thank you for your consideration.",
            f"Yours sincerely,\n{PROFILE['name']}\n{PROFILE['email']}",
        ]
        salutation = "Dear Hiring Manager,"
        re_line = f"Re: {title} — {company}"
    else:
        paragraphs = [
            f"Me dirijo a usted para expresar mi interés en el puesto de {title} en {company}.",
            opening,
            f"Cuento con experiencia práctica en Python, SQL, Agile/Scrum y sistemas CRM, junto con un profundo conocimiento en operaciones de seguros, gestión de MGAs y el mercado de Lloyd's. Estoy convencido de que estas competencias aportarán valor inmediato a {company}.",
            "Estaría encantado de poder comentar cómo mi perfil se alinea con sus necesidades. Gracias por su consideración.",
            f"Atentamente,\n{PROFILE['name']}\n{PROFILE['email']}",
        ]
        salutation = "Estimado/a equipo de selección,"
        re_line = f"Asunto: {title} — {company}"

    elems = []
    elems.append(Paragraph(PROFILE["name"], hdr_s))
    elems.append(Paragraph(f"{PROFILE['email']} | {PROFILE['location']}", meta_s))
    elems.append(Paragraph(TODAY, meta_s))
    elems.append(Paragraph(re_line, re_s))
    elems.append(Paragraph(salutation, body_s))
    for p in paragraphs:
        if p.strip():
            elems.append(Paragraph(p.strip().replace("\n","<br/>"), body_s))

    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────
# SCRAPERS
# ─────────────────────────────────────────────────────────────

def scrape_indeed_rss():
    jobs = []
    for url in INDEED_RSS_FEEDS:
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        try:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                jobs.append({"title": item.findtext("title","").strip(),
                             "company": "Indeed", "link": item.findtext("link","").strip(),
                             "description": item.findtext("description","").strip(),
                             "source": "Indeed"})
        except Exception as e:
            print(f"  Indeed parse error: {e}")
    print(f"  Indeed: {len(jobs)} listings")
    return jobs

def scrape_remote_boards():
    jobs = []
    for board in REMOTE_BOARDS:
        r = fetch(board["url"])
        if not r or r.status_code != 200:
            continue
        try:
            if board["type"] == "rss":
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    jobs.append({"title": item.findtext("title","").strip(),
                                 "company": board["name"], "link": item.findtext("link","").strip(),
                                 "description": item.findtext("description","").strip(),
                                 "source": board["name"]})
            elif board["type"] == "json":
                for job in r.json()[1:]:
                    if isinstance(job, dict):
                        jobs.append({"title": job.get("position",""), "company": job.get("company",""),
                                     "link": job.get("url",""),
                                     "description": " ".join(job.get("tags",[])),
                                     "source": board["name"]})
            elif board["type"] == "json_remotive":
                for job in r.json().get("jobs",[]):
                    jobs.append({"title": job.get("title",""), "company": job.get("company_name",""),
                                 "link": job.get("url",""),
                                 "description": job.get("description","")[:500],
                                 "source": board["name"]})
        except Exception as e:
            print(f"  {board['name']} error: {e}")
    print(f"  Remote boards: {len(jobs)} listings")
    return jobs

def scrape_ashby():
    """Fetch jobs from Ashby ATS public API — returns real job listings, not JS pages."""
    jobs = []
    for co in ASHBY_COMPANIES:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{co['client']}?includeCompensation=true"
        r = fetch(url)
        if not r or r.status_code != 200:
            print(f"  Ashby {co['name']}: no response")
            continue
        try:
            data = r.json()
            listings = data.get("jobs", [])
            for job in listings:
                if not job.get("isListed", True):
                    continue
                location = job.get("location", "")
                is_remote = job.get("isRemote", False)
                workplace = job.get("workplaceType", "")
                salary_info = ""
                comp = job.get("compensation", {})
                if comp:
                    salary_info = comp.get("compensationTierSummary", "") or comp.get("scrapeableCompensationSalarySummary", "")
                # Build explicit location signal so AI filter cannot miss it
                if is_remote or workplace.lower() in ("remote", "fully remote"):
                    loc_signal = "FULLY REMOTE eligible"
                elif workplace.lower() == "hybrid" and any(
                    city in location.lower() for city in ["barcelona", "madrid", "spain"]
                ):
                    loc_signal = f"HYBRID BARCELONA/SPAIN eligible Location {location}"
                elif workplace.lower() == "hybrid":
                    loc_signal = f"HYBRID {location} NOT Barcelona NOT Spain REJECT THIS JOB"
                else:
                    loc_signal = f"ON-SITE {location} REJECT unless Barcelona Spain"

                jobs.append({
                    "title": job.get("title", ""),
                    "company": co["name"],
                    "link": job.get("jobUrl", f"https://jobs.ashbyhq.com/{co['client']}"),
                    "description": (
                        f"LOCATION FILTER: {loc_signal} | "
                        f"Workplace: {workplace} | Salary: {salary_info} | "
                        + job.get("descriptionPlain", "")[:400]
                    ),
                    "source": "Ashby API"
                })
            print(f"  Ashby {co['name']}: {len(listings)} job(s)")
        except Exception as e:
            print(f"  Ashby {co['name']} error: {e}")
    print(f"  Ashby total: {len(jobs)} listings")
    return jobs


def scrape_greenhouse():
    """Fetch jobs from Greenhouse ATS public API."""
    jobs = []
    for co in GREENHOUSE_COMPANIES:
        url = f"https://api.greenhouse.io/v1/boards/{co['client']}/jobs?content=true"
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        try:
            listings = r.json().get("jobs", [])
            for job in listings:
                location = job.get("location", {}).get("name", "")
                jobs.append({
                    "title": job.get("title", ""),
                    "company": co["name"],
                    "link": job.get("absolute_url", ""),
                    "description": f"Location: {location} | " + job.get("content", "")[:400],
                    "source": "Greenhouse API"
                })
            print(f"  Greenhouse {co['name']}: {len(listings)} job(s)")
        except Exception as e:
            print(f"  Greenhouse {co['name']} error: {e}")
    print(f"  Greenhouse total: {len(jobs)} listings")
    return jobs


def scrape_lever():
    """Fetch jobs from Lever ATS public API."""
    jobs = []
    for co in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{co['client']}?mode=json"
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        try:
            listings = r.json()
            for job in listings:
                categories = job.get("categories", {})
                location = categories.get("location", categories.get("allLocations", ""))
                jobs.append({
                    "title": job.get("text", ""),
                    "company": co["name"],
                    "link": job.get("hostedUrl", ""),
                    "description": f"Location: {location} | Team: {categories.get('team','')} | " + job.get("descriptionPlain", "")[:400],
                    "source": "Lever API"
                })
            print(f"  Lever {co['name']}: {len(listings)} job(s)")
        except Exception as e:
            print(f"  Lever {co['name']} error: {e}")
    print(f"  Lever total: {len(jobs)} listings")
    return jobs


def scrape_company_pages():
    jobs = []
    for co in INSURTECH_COMPANIES:
        r = fetch(co["url"])
        if not r or r.status_code != 200:
            continue
        if any(kw in r.text.lower() for kw in co["keywords"]):
            jobs.append({"title": f"Open roles at {co['name']}", "company": co["name"],
                         "link": co["url"], "description": f"Insurtech: {', '.join(co['keywords'])}",
                         "source": "Insurtech Company"})
    print(f"  Company sites: {len(jobs)} active")
    return jobs

def scrape_recruiters():
    jobs = []
    for rec in RECRUITERS:
        r = fetch(rec["url"])
        if not r or r.status_code != 200:
            continue
        if any(kw in r.text.lower() for kw in ["insurance","insurtech","underwriting","mga"]):
            jobs.append({"title": f"Recruiter — {rec['name']}", "company": rec["name"],
                         "link": rec["url"],
                         "description": "Insurance/insurtech recruiter with active listings",
                         "source": "Recruiter"})
    print(f"  Recruiters: {len(jobs)} active")
    return jobs

# ─────────────────────────────────────────────────────────────
# AI SCORING
# ─────────────────────────────────────────────────────────────

def score_and_generate(job):
    if not ANTHROPIC_API_KEY:
        return None
    prompt = f"""You are a career coach specializing in insurance and insurtech.

CANDIDATE: Marc Planas, Barcelona
Target roles: {', '.join(PROFILE['target_roles'][:6])}
Domain skills: {', '.join(PROFILE['experience'][0]['skills'][:8])}
Technical skills: Python, SQL, Agile/Scrum, Excel, CRM Systems
Languages: English, Spanish, Catalan
Min salary: €60,000/year
Location: Remote EU OK | Hybrid Barcelona OK | Hybrid elsewhere = REJECT | On-site outside Spain = REJECT

HARD FILTERS — score 0 if any apply:
- Salary explicitly below €60,000
- On-site only outside Barcelona/Spain
- Hybrid but not Barcelona/Spain
- Junior/graduate/intern/entry-level

JOB:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}
Description: {job['description'][:700]}

Score 0-100. If >= 80, write tailored CV summaries and cover letter openings.
Respond ONLY in valid JSON:
{{"score":<int>,"reason":"<1 sentence>","location_type":"<remote|hybrid-barcelona|hybrid-other|onsite>","salary_info":"<salary or not specified>","cv_summary_en":"<3-4 sentences or empty>","cv_summary_es":"<3-4 sentences or empty>","cover_letter_en":"<3-4 sentences or empty>","cover_letter_es":"<3-4 sentences or empty>"}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"  AI error: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────

def attach_pdf(msg, pdf_bytes, filename):
    part = MIMEBase("application","octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)

def send_email(matched_jobs):
    if not matched_jobs:
        return
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Job Matches {TODAY} - {len(matched_jobs)} new insurtech role(s)"
    msg["From"] = f"Insurtech Job Hunter <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER
    msg["Reply-To"] = GMAIL_USER
    msg["X-Mailer"] = "Python/smtplib"

    html = [f"""<html><body style="font-family:Arial,sans-serif;">
<h2 style="color:#1a1a2e;">🎯 {len(matched_jobs)} Job Match(es) — {TODAY}</h2>
<p>Scoring 80%+ | PDF CVs & cover letters attached per job</p>"""]

    pdf_count = 0
    for i, job in enumerate(matched_jobs, 1):
        ai  = job.get("ai_result", {})
        res = job.get("company_research", "Not available")
        html.append(f"""
<hr style="border:2px solid #4a4a8a;margin:20px 0;">
<h3>#{i} — <a href="{job['link']}" style="color:#4a4a8a;">{job['title']}</a></h3>
<table style="font-size:13px;border-collapse:collapse;margin-bottom:12px;">
  <tr><td style="padding:3px 12px 3px 0;"><b>Company</b></td><td>{job['company']}</td></tr>
  <tr><td style="padding:3px 12px 3px 0;"><b>Source</b></td><td>{job['source']}</td></tr>
  <tr><td style="padding:3px 12px 3px 0;"><b>Match Score</b></td><td><b style="color:#4a4a8a;font-size:15px;">{ai.get('score','?')}%</b></td></tr>
  <tr><td style="padding:3px 12px 3px 0;"><b>Location</b></td><td>{ai.get('location_type','').replace('-',' ').title()}</td></tr>
  <tr><td style="padding:3px 12px 3px 0;"><b>Salary</b></td><td>{ai.get('salary_info','not specified')}</td></tr>
</table>
<p><em>{ai.get('reason','')}</em></p>

<h4 style="color:#4a4a8a;">🏢 Company Research Brief</h4>
<div style="background:#f8f8ff;padding:12px;border-left:4px solid #4a4a8a;border-radius:4px;white-space:pre-wrap;font-size:12px;">{res}</div>

<h4 style="color:#4a4a8a;">📄 CV Summary (EN)</h4><p>{ai.get('cv_summary_en','')}</p>
<h4 style="color:#4a4a8a;">📄 Resumen CV (ES)</h4><p>{ai.get('cv_summary_es','')}</p>
<h4 style="color:#4a4a8a;">✉️ Cover Letter (EN)</h4><p>{ai.get('cover_letter_en','')}</p>
<h4 style="color:#4a4a8a;">✉️ Carta de Presentación (ES)</h4><p>{ai.get('cover_letter_es','')}</p>
<p>📎 <b>4 PDFs attached:</b> CV (EN + ES) + Cover Letter (EN + ES)</p>
<p><a href="{job['link']}" style="background:#4a4a8a;color:white;padding:8px 18px;text-decoration:none;border-radius:4px;display:inline-block;">👉 Apply Now</a></p>""")

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

    html.append("</body></html>")
    # Plain text version (helps avoid spam filters)
    plain_lines = [f"Job Matches - {TODAY}", f"{len(matched_jobs)} new insurtech role(s) scoring 80%+", ""]
    for i, job in enumerate(matched_jobs, 1):
        ai = job.get("ai_result", {})
        plain_lines.append(f"#{i} {job['title']} at {job['company']}")
        plain_lines.append(f"Score: {ai.get('score','?')}% | {job['link']}")
        plain_lines.append("")
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("\n".join(plain_lines), "plain"))
    alt.attach(MIMEText("".join(html), "html"))
    msg.attach(alt)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"Email sent: {len(matched_jobs)} match(es), {pdf_count} PDFs attached.")
    except Exception as e:
        print(f"Email error: {e}")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print(f"\nAI Job Hunter — {TODAY}\n")
    seen = load_seen_jobs()

    print("Scanning sources...")
    all_jobs  = scrape_indeed_rss()
    all_jobs += scrape_remote_boards()
    all_jobs += scrape_ashby()
    all_jobs += scrape_greenhouse()
    all_jobs += scrape_lever()
    all_jobs += scrape_company_pages()
    all_jobs += scrape_recruiters()
    print(f"Total listings: {len(all_jobs)}")

    new_jobs = [j for j in all_jobs if job_id(j["title"],j["company"]) not in seen]
    for j in new_jobs:
        seen.add(job_id(j["title"], j["company"]))
    print(f"New (not seen before): {len(new_jobs)}")

    if not new_jobs:
        print("No new jobs today.")
        save_seen_jobs(seen)
        return

    matched = []
    print("\nScoring with Claude AI...")
    for job in new_jobs:
        result = score_and_generate(job)
        if result and result.get("score", 0) >= PROFILE["min_match_score"]:
            job["ai_result"] = result
            print(f"  {result['score']}% MATCH — {job['title']} @ {job['company']}")
            print(f"  Researching {job['company']}...")
            job["company_research"] = research_company(job["company"], job["title"])
            log_to_tracker(job, result)
            matched.append(job)
        elif result:
            print(f"  {result['score']}% — {job['title']} (below threshold)")

    print(f"\nMatches at 80%+: {len(matched)}")
    send_email(matched)
    save_seen_jobs(seen)
    print("Done.")

if __name__ == "__main__":
    main()
