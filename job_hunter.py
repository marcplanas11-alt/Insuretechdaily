name: EU Insurtech Job Monitor

on:
  schedule:
    - cron: '0 8 * * *'
    - cron: '0 8 * * 1'
  workflow_dispatch:

jobs:

  check-jobs:
    name: Run AI Job Hunter
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/cache@v3
        with:
          path: |
            seen_jobs.json
            job_tracker.csv
          key: job-data-${{ runner.os }}
          restore-keys: job-data-
      - run: pip install requests reportlab
      - name: Run job hunter
        env:
          ANTHROPIC_API_KEY:  ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:         ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python job_hunter.py
      - uses: actions/cache@v3
        with:
          path: |
            seen_jobs.json
            job_tracker.csv
          key: job-data-${{ runner.os }}-${{ github.run_id }}

  scan-companies:
    name: New Insurtech Company Scanner
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/cache@v3
        with:
          path: seen_companies.json
          key: company-data-${{ runner.os }}
          restore-keys: company-data-
      - run: pip install requests beautifulsoup4
      - name: Run company scanner
        env:
          ANTHROPIC_API_KEY:  ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:         ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python company_scanner.py
      - uses: actions/cache@v3
        with:
          path: seen_companies.json
          key: company-data-${{ runner.os }}-${{ github.run_id }}

  scan-eu-expansion:
    name: EU Expansion Tracker
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/cache@v3
        with:
          path: |
            seen_expansions.json
            expansion_tracker.csv
            expansion_weekly.json
          key: expansion-data-${{ runner.os }}
          restore-keys: expansion-data-
      - run: pip install requests
      - name: Run EU expansion scanner
        env:
          ANTHROPIC_API_KEY:  ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:         ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python eu_expansion_scanner.py
      - uses: actions/cache@v3
        with:
          path: |
            seen_expansions.json
            expansion_tracker.csv
            expansion_weekly.json
          key: expansion-data-${{ runner.os }}-${{ github.run_id }}

  weekly-digest:
    name: Weekly Intelligence Digest
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 8 * * 1' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/cache@v3
        with:
          path: |
            job_tracker.csv
            expansion_weekly.json
          key: job-data-${{ runner.os }}
          restore-keys: |
            job-data-
            expansion-data-
      - run: pip install requests
      - name: Send weekly digest
        env:
          GMAIL_USER:         ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python weekly_digest.py
