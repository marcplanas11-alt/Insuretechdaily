I have a GitHub repo at `https://github.com/marcplanas11-alt/insurance-ai-pipeline` with a bordereaux cleaner pipeline that is not working end-to-end.

**What the repo contains:**
- `src/bordereaux_cleaner.py` — Python module with a `clean_bordereaux(df)` function that takes a pandas DataFrame and returns `(cleaned_df, report_dict, issues_list)`
- `run_cleaner.py` — local runner script in repo root
- `input/` — folder where users upload bordereaux CSV/XLSX files
- `input/.gitkeep` — placeholder file (causes pandas EmptyDataError when accidentally read)
- `.github/workflows/bordereaux-cleaner.yml` — GitHub Actions workflow that should trigger on push to `input/`, read the CSV/XLSX, run the cleaner, and upload outputs as Artifacts
- `conftest.py` and `pytest.ini` in root with `pythonpath = .`

**The problem:**
The workflow triggers correctly when a file is uploaded to `input/` but crashes with `pandas.errors.EmptyDataError: No columns to parse from file` because the script picks up `.gitkeep` instead of the actual CSV. Attempts to fix the glob filter haven't resolved it.

**What I need:**
1. Fix `.github/workflows/bordereaux-cleaner.yml` so it correctly finds and processes only CSV/XLSX files in `input/`, ignoring `.gitkeep` and any other non-data files
2. The workflow should accept files with any name (not just `bordereaux_input.csv`)
3. On success it should upload 3 artifacts: cleaned Excel, errors-only Excel, text quality report
4. Add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` to suppress Node.js deprecation warnings
5. Also add a `workflow_dispatch` trigger with a `sample_data` input so it can be tested manually without uploading a file

Please clone the repo, inspect the actual current workflow file, fix it, and confirm it works with a test run using the sample data option.
