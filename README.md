# Insuretechdaily — EU Insurance, BA & AI Consulting Job Monitor

**Automated job discovery and company intelligence system for EU insurance operations, Business Analyst, digital transformation and AI consulting roles.**

This portfolio project demonstrates **AI automation, multi-source API integration, job-market monitoring and intelligent role matching** across the European insurance, insurtech, financial services and AI automation market. It is built with Python, Claude API-compatible scoring, public job-board APIs and GitHub Actions orchestration.

---

## The Problem This Solves

Searching for relevant EU roles across insurance, consulting and AI automation requires:

- Manual scanning of insurer, reinsurer, MGA, insurtech and consulting job boards
- Separate monitoring for Business Analyst, transformation and AI implementation roles
- Careful filtering by geography, remote policy, seniority, salary and domain relevance
- Avoiding poor-fit roles: junior, pure sales, pure ML research, US-only or Madrid-presential roles
- Keeping track of niche opportunities in Guidewire, claims, underwriting, delegated authority and reinsurance operations

**Insuretechdaily automates this workflow**: daily scans across major ATS APIs, RSS feeds and curated career pages; deterministic/AI-assisted scoring; EU-focused filtering; smart alerts; and a tracker of new opportunities.

---

## Current Search Scope

The monitor now runs a **three-track search**:

### Track A — Insurance Operations / Guidewire / Claims / Underwriting
Core roles similar to Marc's existing insurance operations background:

- Insurance Operations Manager / Analyst
- Underwriting Operations
- Claims Operations / Claims Transformation
- Reinsurance Operations
- Bordereaux / Delegated Authority / DUA
- MGA / Coverholder / Lloyd's market roles
- Guidewire / PolicyCenter / ClaimCenter / Duck Creek / FINEOS roles
- Programme Manager / Process Owner roles in insurance contexts

### Track B — Business Analyst / Digital Transformation / Consulting
Target BA and transformation roles across Europe:

- Business Analyst / IT Business Analyst / Technical Business Analyst
- Digital Transformation Consultant
- Process Analyst / Business Process Analyst
- Implementation Consultant / Functional Consultant
- Product Owner in insurance, fintech or financial services
- Consulting roles where insurance operations + automation is an advantage

For Track B, the monitor accepts **fully remote EU roles** and **relocation/hybrid roles across Europe** when the role is strong enough. Madrid presencial remains a hard blocker.

### Track C — AI Consultant / AI Automation / AI Implementation
AI roles where domain expertise and operational transformation matter:

- AI Consultant
- AI Automation Consultant
- AI Implementation Consultant
- Intelligent Automation Consultant
- AI Governance / Responsible AI / EU AI Act / DORA roles
- Workflow automation / agentic process automation roles
- AI solution roles in insurance, fintech, operations or regulated industries

---

## What It Does

### Daily Job Monitoring

1. **Multi-source job scanning** — Queries insurance, consulting, insurtech, AI and remote-job sources via Ashby, Greenhouse, Lever, Remotive, RSS and curated career pages.
2. **EU-focused filtering** — Prioritises Europe-wide remote roles, EU/EMEA remote roles, Barcelona hybrid roles and strong BA/consulting roles with possible EU relocation.
3. **Guardrails** — Rejects junior/intern/graduate roles, pure sales roles, US-only remote roles, pure ML research roles and Madrid-presential roles.
4. **Salary floor** — Uses **€45K minimum floor**. Roles without salary information are still considered instead of being discarded.
5. **Scoring** — Uses Claude when `ANTHROPIC_API_KEY` is configured; otherwise falls back to deterministic keyword scoring so the GitHub Action remains useful.
6. **Email alerts** — Sends matched roles and manual-check company signals when email secrets are configured.

### Weekly Intelligence Digest

1. **Company monitoring** — Tracks RSS feeds and curated company sources for insurtech/MGA funding, launches, expansion and hiring signals.
2. **Weekly summary** — Aggregates top matches, sources, companies and pending opportunities into a digest email.

---

## Architecture

| Component | Purpose |
|-----------|---------|
| `marc_profile.py` | Professional profile, role preferences, salary floor, location rules and scoring keywords |
| `job_hunter.py` | Job scanning, filtering, scoring, tracker logging and email alerts |
| `company_scanner.py` | Insurtech/MGA news monitoring via RSS feeds |
| `coverholder_scanner.py` | Lloyd's coverholder and MGA EU-expansion signal monitoring |
| `weekly_digest.py` | Weekly summary email generation |
| `.github/workflows/jobmonitor.yml` | GitHub Actions orchestration, schedule, cache and secret handling |

---

## Job Sources

| Source | Type | Coverage |
|--------|------|----------|
| **Ashby API** | JSON | Descartes, Cytora, Artificial Labs, wefox, Alan, Marshmallow, Zego, Qover, Embat, etc. |
| **Greenhouse API** | JSON | Shift Technology, Guidewire, Duck Creek, FINEOS, CoverGo, Hokodo, Concirrus, Coalition, At-Bay, etc. |
| **Lever API** | JSON | Wakam, Prima, Superscript, Laka, Flock, Embroker, Mistral AI, etc. |
| **Remotive API** | JSON | Remote finance, business, software and operations jobs |
| **RSS Feeds** | XML | Remotive, We Work Remotely, Jobicy and insurance/insurtech feeds |
| **Career Pages** | HTML | Accelerant, Swiss Re, Munich Re, SCOR, Hannover Re, Novidea, Synpulse, Capco, Capgemini Invent, EY, Deloitte, KPMG, WTW, Aon, Milliman, Oliver Wyman, Maisa and others |
| **Adzuna API** | JSON | Optional extended search across UK, Spain, Germany, France and Netherlands when API keys are configured |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Optional: Claude / Anthropic API key for AI-assisted scoring
- Optional: Gmail account with App Password enabled for email alerts
- Optional: Adzuna API credentials for extended job search

### Local Setup

```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
pip install requests
python job_hunter.py
```

### GitHub Actions Automation

Recommended secrets:

```text
ANTHROPIC_API_KEY       # optional, enables Claude scoring
SMTP_USER               # preferred email username secret
SMTP_PASS               # preferred email app-password secret
GMAIL_USER              # accepted fallback
GMAIL_APP_PASSWORD      # accepted fallback
ADZUNA_APP_ID           # optional
ADZUNA_APP_KEY          # optional
```

Automated runs:

- Daily 07:00 UTC: job scan, company scan and coverholder scan
- Monday 08:00 UTC: weekly digest
- Manual trigger: Actions → “EU Insurance Remote Job Monitor v2” → `Run workflow`

The workflow is designed to be resilient: missing optional secrets, cache errors or transient API failures should not break the whole scheduled run.

---

## Scoring Logic

The monitor scores jobs **0–100** using either Claude or deterministic fallback scoring.

| Score | Action |
|-------|--------|
| 85–100 | **High-priority match** — apply or review immediately |
| 70–84 | **Relevant match** — review and tailor CV |
| 50–69 | **Watchlist / conditional** — useful signal but not automatic priority |
| <50 | **Low relevance** — usually ignored |

**Hard rejects:** junior/graduate/intern roles, pure sales, US-only remote, pure ML research, Madrid-presential roles, and explicit salary below **€45K**.

**Important nuance:** roles with no salary published are not rejected automatically. Many EU insurance/consulting postings omit salary, so the monitor keeps them if the domain, seniority and location fit are strong.

---

## Tech Stack

**Languages:** Python 3.10+  
**AI/Automation:** Claude API-compatible scoring, deterministic fallback scoring, workflow automation  
**APIs:** Ashby, Greenhouse, Lever, Remotive, Adzuna, RSS feeds  
**Infrastructure:** GitHub Actions, scheduled workflows, cache restore/save, resilient error handling  
**Notifications:** Gmail SMTP  

---

## Portfolio Value

This project demonstrates:

- **AI-enabled automation:** job scoring, role matching and structured alerting
- **API engineering:** multi-source job board integrations across ATS systems
- **Python automation:** scraping, filtering, deduplication, scoring, CSV tracking and email notifications
- **CI/CD orchestration:** scheduled GitHub Actions with secret handling and failure resilience
- **Insurance domain expertise:** MGA, delegated authority, bordereaux, reinsurance operations, Guidewire and claims/underwriting workflows
- **BA / transformation positioning:** requirements, process analysis, implementation consulting and insurance digital transformation
- **Practical problem solving:** automates a high-friction real-world job-search workflow

---

## Certifications & Technologies

**AI & Automation:**

- Building with the Claude API — Anthropic Academy
- AI Fluency & Prompt Engineering — Anthropic Academy
- Multi-Agent AI Systems with CrewAI — DeepLearning.AI course
- AI Agents with LangGraph — DeepLearning.AI course

**Technical:**

- Python 3.10+ with `requests`, `csv`, `json`, `smtplib` and XML parsing
- Claude API / Anthropic-compatible scoring
- GitHub Actions & CI/CD
- SQL intermediate
- Power BI / Snowflake exposure from insurance operations contexts

**Insurance Operations:**

- 10+ years across MGAs, brokers, carriers and reinsurance platforms
- Delegated authority, bordereaux management, operational controls and regulatory workflows
- Corredor de Seguros Grupo B — ICEA, 2022

---

## Author

**Marc Planas Callico**

Insurance & Reinsurance Operations | Business Analysis | AI-Enabled Transformation | MGA / Lloyd's Market

**Background:** 10+ years across MGAs, brokers, global carriers and reinsurance platforms. Focused on insurance operations transformation, BA/consulting roles and AI-enabled process automation across Europe.

**Languages:** English C2 · French C1 · Spanish Native · Catalan Native · Italian B2

**Connect:**

- LinkedIn: https://linkedin.com/in/marcplanas11
- Email: marcplanas11@gmail.com

---

## Licensing

This project is provided as-is for educational and professional reference.

---

## Feedback & Collaboration

Recommendations on insurance, BA, consulting or AI automation job sources? Open an issue or reach out via LinkedIn.
