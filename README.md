# Insuretechdaily — AI-Enabled Insurance Job & Company Discovery Portfolio

**Automated AI-powered job discovery and company intelligence system for insurance operations roles**

This portfolio project demonstrates **AI automation, multi-source API integration, and intelligent job matching** for the insurance sector. Built with Claude API, Python, and GitHub Actions orchestration — showcasing practical skills in operations, insurtech discovery, and agentic AI systems.

---

## The Problem This Solves

Recruiting for insurance operations roles across Europe requires:
- Manual scanning of 30+ company job boards daily
- Inconsistent filtering (location, seniority, domain relevance)
- Time-consuming shortlisting and CV tailoring
- Missed opportunities in niche insurtech/MGA markets

**Insuretechdaily automates this workflow**: Daily scans across all major job sources, AI-powered scoring aligned to insurance operations expertise, auto-generated tailored CVs + cover letters, and smart alerts — reducing manual job search time by 80%+.

---

## What It Does

### Daily Job Monitoring (Mon–Fri, 8am UTC)
1. **Multi-Source Job Scanning** — Queries 30+ insurance companies via APIs (Ashby, Greenhouse, Lever, Remotive, RSS)
2. **EU-Focused Filtering** — Remote + EU-eligible roles only, hardcoded guardrails (no junior, no on-site outside Barcelona, salary floor €50K)
3. **AI Scoring** — Claude AI scores each job 0–100 based on insurance operations expertise, role seniority, and domain fit
4. **Smart Matching** — Generates role-specific PDF CVs + cover letters in EN/ES for matches ≥75
5. **Email Alerts** — Sends matched jobs with scoring rationale to Gmail

### Weekly Intelligence Digest (Monday, 9am UTC)
6. **Company Monitoring** — Tracks 7 RSS feeds for insurtech/MGA news (funding, launches, expansions)
7. **Weekly Summary** — Aggregates top matches, scoring stats, company intelligence → email digest

---

## Architecture

| Component | Purpose |
|-----------|---------|
| `marc_profile.py` | Professional profile data (skills, keywords, experience) |
| `job_hunter.py` | Job scanning, Claude AI scoring, PDF/letter generation |
| `company_scanner.py` | Insurtech news monitoring via RSS feeds |
| `weekly_digest.py` | Weekly summary email generation |
| `.github/workflows/jobmonitor.yml` | GitHub Actions orchestration (cron triggers) |

---

## Job Sources (All Tested & Working)

| Source | Type | Coverage |
|--------|------|----------|
| **Ashby API** | JSON | Descartes, Cytora, Artificial Labs, wefox, Alan, Marshmallow, Zego, etc. |
| **Greenhouse API** | JSON | Shift Technology, Tractable, Guidewire, Duck Creek, Hokodo, etc. |
| **Lever API** | JSON | Wakam, Prima, Superscript, Laka, Flock |
| **Remotive API** | JSON | 100+ remote insurance/finance jobs |
| **RSS Feeds** | XML | Remotive, We Work Remotely, industry news |
| **Career Pages** | HTML scraping | Accelerant, Ledgebrook, Swiss Re, Munich Re, Gen Re, SCOR |

---

## Getting Started

### Prerequisites
- Python 3.10+
- Claude API key (Anthropic) — [Get here](https://console.anthropic.com)
- Gmail account with App Password enabled

### Local Setup
```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
pip install -r requirements.txt
python job_hunter.py  # Run once manually
```

### GitHub Actions Automation
1. **Add GitHub Secrets:** ANTHROPIC_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD
2. **Enable Actions** in Settings → Actions → Allow workflows
3. **Trigger manually:** Actions tab → "EU Insurance Remote Job Monitor v2" → Run workflow

**Automated runs:**
- Monday–Friday 8am UTC: Full job scan + email alerts
- Monday 9am UTC: Weekly digest email

---

## AI Scoring Logic

Claude AI scores jobs **0–100** based on insurance operations fit, seniority, remote+EU eligibility, and company maturity.

| Score | Action |
|-------|--------|
| 90–100 | **Perfect match** — Senior ops at insurer/insurtech/MGA |
| 80–89 | **Strong match** — Operations focus |
| 75–79 | **Good match** — Adjacent role at insurer |
| <75 | **Below threshold** — Not emailed |

**Hard rejects:** On-site outside Barcelona, junior roles, non-insurance, salary <€50K

---

## Tech Stack

**Languages:** Python 3.10+  
**AI/Automation:** Claude API (Anthropic), intelligent scoring & document generation  
**APIs:** Ashby, Greenhouse, Lever, Remotive, RSS feeds  
**Infrastructure:** GitHub Actions (cron triggers, smart caching)  
**Notifications:** Gmail SMTP  

---

## Portfolio Value

This project demonstrates:
- **AI Integration**: Claude API for intelligent job scoring and CV generation
- **API Engineering**: Multi-source job board APIs (Ashby, Greenhouse, Lever, Remotive)
- **Python Automation**: Full-stack automation (scraping, PDF generation, email)
- **CI/CD Orchestration**: GitHub Actions, smart caching, scheduled workflows
- **Domain Expertise**: 10+ years insurance operations (MGA, reinsurance, delegated authority)
- **Real-World Problem Solving**: Automates 80%+ of manual job search

---

## Certifications & Technologies

**AI & Automation:**
- Building with the Claude API (Anthropic Academy 2025)
- AI Fluency & Prompt Engineering (Anthropic Academy 2025)
- Multi-Agent AI Systems with CrewAI (DeepLearning.AI 2026)
- AI Agents with LangGraph (DeepLearning.AI 2026)

**Technical:**
- Python 3.10+ (Pandas, openpyxl, requests, reportlab)
- Claude API & Anthropic SDK
- GitHub Actions & CI/CD
- SQL (Mode Analytics — Window Functions, CTEs)

**Insurance Operations:**
- 10+ years: MGAs, Lloyd's Market, reinsurance platforms
- Expertise: Delegated authority, bordereaux management, DORA/Solvency II compliance
- License: Corredor de Seguros Grupo B (Spanish insurance broker, ICEA 2022)

---

## Author

**Marc Planas Callico**

Insurance & Reinsurance Operations Leader | AI Automation | MGA | Lloyd's Market

**Background:** 10+ years across MGAs, brokers, global carriers, and reinsurance platforms. Specializing in operations transformation and AI-enabled automation.

**Languages:** English C2 · French C1 · Spanish Native · Italian B2

**Connect:**
- LinkedIn: https://linkedin.com/in/marcplanas11
- Email: marcplanas11@gmail.com

---

## Licensing

This project is provided as-is for educational and professional reference.

---

## Feedback & Collaboration

Recommendations on insurance AI or operations automation? Open an issue or reach out via LinkedIn.
