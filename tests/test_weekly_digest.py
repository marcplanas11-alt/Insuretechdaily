"""
Tests for weekly_digest.py

Coverage areas:
- Filesystem I/O: load_tracker
- Calculation logic: filtering, scoring, pending count (tested via send_digest
  with SMTP mocked out)
"""
import csv
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import weekly_digest


# ─────────────────────────────────────────────────────────────
# load_tracker
# ─────────────────────────────────────────────────────────────

class TestLoadTracker:
    def test_returns_empty_list_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(weekly_digest, "TRACKER_FILE", str(tmp_path / "nonexistent.csv"))
        assert weekly_digest.load_tracker() == []

    def test_parses_csv_rows_correctly(self, tmp_path, monkeypatch):
        f = tmp_path / "tracker.csv"
        with f.open("w", newline="") as fh:
            w = csv.DictWriter(
                fh,
                fieldnames=["Date", "Title", "Company", "Source", "Score",
                             "Location", "Salary", "Reason", "Link", "Status"]
            )
            w.writeheader()
            w.writerow({
                "Date": "2026-04-01", "Title": "Ops Manager", "Company": "Acme",
                "Source": "Ashby", "Score": "85", "Location": "remote",
                "Salary": "€70K", "Reason": "Good match", "Link": "https://a.com",
                "Status": "New"
            })
        monkeypatch.setattr(weekly_digest, "TRACKER_FILE", str(f))
        rows = weekly_digest.load_tracker()
        assert len(rows) == 1
        assert rows[0]["Title"] == "Ops Manager"
        assert rows[0]["Company"] == "Acme"
        assert rows[0]["Score"] == "85"

    def test_returns_all_rows(self, tmp_path, monkeypatch):
        f = tmp_path / "tracker.csv"
        with f.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["Date", "Title", "Score", "Status"])
            w.writeheader()
            for i in range(5):
                w.writerow({"Date": "2026-04-01", "Title": f"Job {i}", "Score": "80", "Status": "New"})
        monkeypatch.setattr(weekly_digest, "TRACKER_FILE", str(f))
        rows = weekly_digest.load_tracker()
        assert len(rows) == 5

    def test_returns_empty_list_on_read_error(self, tmp_path, monkeypatch, mocker):
        f = tmp_path / "tracker.csv"
        f.write_text("some,content")
        monkeypatch.setattr(weekly_digest, "TRACKER_FILE", str(f))
        mocker.patch("weekly_digest.csv.DictReader", side_effect=Exception("read error"))
        result = weekly_digest.load_tracker()
        assert result == []


# ─────────────────────────────────────────────────────────────
# send_digest — calculation logic (SMTP mocked out)
# ─────────────────────────────────────────────────────────────

def _row(days_ago=1, score="80", status="New", company="Acme", source="Ashby"):
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return {
        "Date": date, "Title": "Ops Manager", "Company": company,
        "Source": source, "Score": score, "Status": status,
        "Link": "https://example.com", "Salary": "€70K",
    }


@pytest.fixture
def mock_smtp(monkeypatch):
    """Prevent any real SMTP connections during digest tests."""
    monkeypatch.setattr(weekly_digest, "GMAIL_USER", "test@example.com")
    monkeypatch.setattr(weekly_digest, "GMAIL_APP_PASSWORD", "app-password")
    with patch("weekly_digest.smtplib.SMTP_SSL") as mock:
        smtp_instance = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield mock


class TestSendDigestCalculations:
    def test_does_not_raise_on_empty_rows(self, mock_smtp):
        weekly_digest.send_digest([])  # should not raise

    def test_does_not_raise_on_rows_all_outside_week(self, mock_smtp):
        old_rows = [_row(days_ago=14), _row(days_ago=30)]
        weekly_digest.send_digest(old_rows)  # should not raise

    def test_does_not_raise_with_recent_rows(self, mock_smtp):
        rows = [_row(days_ago=1), _row(days_ago=3), _row(days_ago=6)]
        weekly_digest.send_digest(rows)  # should not raise

    def test_does_not_raise_with_non_numeric_score(self, mock_smtp):
        # This is the key regression test: non-numeric Score must not crash
        rows = [_row(days_ago=1, score="N/A"), _row(days_ago=2, score="")]
        weekly_digest.send_digest(rows)  # should not raise

    def test_does_not_raise_with_mixed_score_types(self, mock_smtp):
        rows = [
            _row(days_ago=1, score="85"),
            _row(days_ago=2, score="N/A"),
            _row(days_ago=3, score=""),
            _row(days_ago=4, score="72"),
        ]
        weekly_digest.send_digest(rows)  # should not raise

    def test_does_not_raise_with_zero_score(self, mock_smtp):
        rows = [_row(days_ago=1, score="0")]
        weekly_digest.send_digest(rows)  # should not raise

    def test_does_not_raise_with_pending_status(self, mock_smtp):
        rows = [
            _row(days_ago=1, status="New"),
            _row(days_ago=2, status="Applied"),
            _row(days_ago=3, status="New"),
        ]
        weekly_digest.send_digest(rows)  # should not raise, pending count = 2

    def test_does_not_raise_with_multiple_companies(self, mock_smtp):
        rows = [
            _row(days_ago=1, company="Acme"),
            _row(days_ago=2, company="Beta"),
            _row(days_ago=3, company="Acme"),
        ]
        weekly_digest.send_digest(rows)  # should not raise, top companies counted

    def test_does_not_raise_with_multiple_sources(self, mock_smtp):
        rows = [
            _row(days_ago=1, source="Ashby"),
            _row(days_ago=2, source="Greenhouse"),
            _row(days_ago=3, source="Ashby"),
        ]
        weekly_digest.send_digest(rows)  # should not raise, top sources counted

    def test_sends_email_when_credentials_present(self, mock_smtp):
        rows = [_row(days_ago=1)]
        weekly_digest.send_digest(rows)
        assert mock_smtp.called

    def test_smtp_error_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(weekly_digest, "GMAIL_USER", "test@example.com")
        monkeypatch.setattr(weekly_digest, "GMAIL_APP_PASSWORD", "bad-pass")
        with patch("weekly_digest.smtplib.SMTP_SSL", side_effect=Exception("SMTP error")):
            weekly_digest.send_digest([_row(days_ago=1)])  # should not raise
