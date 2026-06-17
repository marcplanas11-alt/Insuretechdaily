# Insuretechdaily — EU Insurance Job Intelligence Monitor

Portfolio project for monitoring EU insurance, reinsurance, MGA, Business Analyst, digital transformation and AI consulting roles.

> **Positioning:** this is a local/GitHub Actions automation prototype. It does not apply for jobs automatically. It collects signals, scores relevance and presents outputs for human review.

---

## Executive Summary

Relevant insurance and AI transformation roles are spread across multiple job boards, ATS platforms, company pages and RSS feeds. Manual monitoring is slow and noisy. This repo automates first-pass discovery and review.

The workflow is:

```text
Job and company sources
   ↓
Python scanners
   ↓
Filtering and scoring rules
   ↓
CSV / JSON outputs
   ↓
Streamlit dashboard or scheduled digest
   ↓
Human review
```

The project demonstrates Python automation, data filtering, scoring logic, scheduled GitHub workflows and Streamlit dashboarding in an insurance operations context.

---

## Main Components

| File | Purpose |
|---|---|
| `app.py` | Streamlit dashboard for reviewing job matches from sample data, uploaded CSVs or generated local CSVs |
| `job_hunter.py` | Main job scanning, filtering, scoring and tracker generation script |
| `company_scanner.py` | RSS-based insurtech and MGA company signal scanner |
| `coverholder_scanner.py` | Lloyd's coverholder / MGA expansion signal scanner |
| `weekly_digest.py` | Weekly summary generator |
| `marc_profile.py` | Search preferences, scoring keywords, salary floor and location rules |
| `.github/workflows/jobmonitor.yml` | Scheduled and manually triggered GitHub Actions workflow |
| `requirements.txt` | Python dependencies needed to run the project |

Runtime files such as `seen_jobs.json`, `seen_companies.json`, `seen_coverholders.json` and `job_tracker.csv` are generated outputs, not source code.

---

## Full Setup and Execution Guide

### 1. Clone the repository

```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

| Package | Use |
|---|---|
| `streamlit` | Browser dashboard |
| `pandas` | CSV loading, filtering and table operations |
| `requests` | API, RSS and web endpoint calls |

---

## Run the Streamlit Dashboard

```bash
streamlit run app.py
```

Expected output:

```text
Local URL: http://localhost:8501
```

Open the local URL in the browser. The dashboard lets you:

- use built-in sample data;
- upload a jobs CSV;
- load the latest local CSV if one has been generated;
- filter roles by score;
- search company or role text;
- download top matches.

---

## Run the Scanners Locally

Run the core job monitor:

```bash
python job_hunter.py
```

Run the company scanner:

```bash
python company_scanner.py
```

Run the coverholder scanner:

```bash
python coverholder_scanner.py
```

Run the weekly digest script:

```bash
python weekly_digest.py
```

Optional external service configuration should be set locally or in GitHub Actions settings, never committed to the repository.

---

## Complete Command Formula

### Windows CMD

```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Windows PowerShell

```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
git clone https://github.com/marcplanas11-alt/Insuretechdaily.git
cd Insuretechdaily
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

---

## GitHub Actions

The workflow in `.github/workflows/jobmonitor.yml` can run daily scans, company scans, coverholder scans and weekly digest generation. It can also be launched manually from the GitHub Actions tab.

---

## Troubleshooting

### `streamlit` is not recognized

```bash
python -m streamlit run app.py
```

### Missing `requests`

```bash
pip install -r requirements.txt
```

### No dashboard data appears

Use sample data first, upload a CSV, or run:

```bash
python job_hunter.py
```

Then enable the local CSV option in the sidebar.

---

## Cleanup Notes

- `requirements.txt` includes `requests` because the scanner modules import it directly.
- Generated tracker/cache files are operational outputs.
- Sensitive local configuration should never be committed.

---

## Author

Built by Marc Planas Callico — Insurance & Reinsurance Operations | Business Analysis | AI-Enabled Transformation.
