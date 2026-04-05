"""
Tests for job_hunter.py

Coverage areas:
- Pure logic: is_insurance_relevant, is_eu_eligible, job_id
- Filesystem I/O: load_seen, save_seen, log_to_tracker
- HTTP: fetch
- Scrapers: scrape_ashby, scrape_greenhouse, scrape_lever
"""
import csv
import json
import pytest
from unittest.mock import MagicMock

import job_hunter


# ─────────────────────────────────────────────────────────────
# is_insurance_relevant
# ─────────────────────────────────────────────────────────────

class TestIsInsuranceRelevant:
    def test_insurance_keyword(self):
        assert job_hunter.is_insurance_relevant("Looking for an insurance operations manager")

    def test_insurtech_keyword(self):
        assert job_hunter.is_insurance_relevant("Join our fast-growing insurtech startup")

    def test_reinsurance_keyword(self):
        assert job_hunter.is_insurance_relevant("Senior reinsurance analyst role")

    def test_underwriting_keyword(self):
        assert job_hunter.is_insurance_relevant("Underwriting operations specialist needed")

    def test_mga_keyword(self):
        assert job_hunter.is_insurance_relevant("Role at a leading mga  in London")

    def test_managing_general_keyword(self):
        assert job_hunter.is_insurance_relevant("Join our managing general underwriting team")

    def test_coverholder_keyword(self):
        assert job_hunter.is_insurance_relevant("Lloyd's coverholder seeks ops lead")

    def test_lloyds_keyword(self):
        assert job_hunter.is_insurance_relevant("Position within the lloyd's market")

    def test_actuar_keyword(self):
        assert job_hunter.is_insurance_relevant("Actuarial support role available")

    def test_claims_keyword(self):
        assert job_hunter.is_insurance_relevant("Claims processing manager required")

    def test_broker_keyword(self):
        assert job_hunter.is_insurance_relevant("Insurance broker seeks operations lead")

    def test_solvency_keyword(self):
        assert job_hunter.is_insurance_relevant("Solvency II compliance manager")

    def test_dua_keyword(self):
        assert job_hunter.is_insurance_relevant("DUA operations and reporting role")

    def test_delegated_underwriting_keyword(self):
        assert job_hunter.is_insurance_relevant("Delegated underwriting authority position")

    def test_case_insensitive_upper(self):
        assert job_hunter.is_insurance_relevant("INSURANCE OPERATIONS MANAGER")

    def test_case_insensitive_mixed(self):
        assert job_hunter.is_insurance_relevant("InsurTech Product Manager Role")

    def test_no_match_software(self):
        assert not job_hunter.is_insurance_relevant("Software engineer Python Django")

    def test_no_match_unrelated(self):
        assert not job_hunter.is_insurance_relevant("Frontend developer React TypeScript")

    def test_empty_string(self):
        assert not job_hunter.is_insurance_relevant("")

    def test_whitespace_only(self):
        assert not job_hunter.is_insurance_relevant("   ")


# ─────────────────────────────────────────────────────────────
# is_eu_eligible
# ─────────────────────────────────────────────────────────────

class TestIsEuEligible:
    def test_remote_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Remote")
        assert eligible is True
        assert loc_type == "remote"

    def test_fully_remote_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Fully Remote")
        assert eligible is True
        assert loc_type == "remote"

    def test_remote_eu_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Remote EU")
        assert eligible is True
        assert loc_type == "remote"

    def test_remote_europe_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Remote Europe")
        assert eligible is True
        assert loc_type == "remote"

    def test_remote_emea_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Remote EMEA")
        assert eligible is True
        assert loc_type == "remote"

    def test_wfa_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("WFA - Work From Anywhere")
        assert eligible is True
        assert loc_type == "remote"

    def test_distributed_keyword(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Distributed team worldwide")
        assert eligible is True
        assert loc_type == "remote"

    def test_eu_city_barcelona(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Barcelona, Spain")
        assert eligible is True
        assert "eu_city" in loc_type

    def test_eu_city_amsterdam(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Amsterdam, Netherlands")
        assert eligible is True
        assert "eu_city" in loc_type

    def test_eu_city_london(self):
        eligible, loc_type = job_hunter.is_eu_eligible("London, UK")
        assert eligible is True
        assert "eu_city" in loc_type

    def test_eu_city_berlin(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Berlin, Germany")
        assert eligible is True
        assert "eu_city" in loc_type

    def test_eu_city_paris(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Paris, France")
        assert eligible is True
        assert "eu_city" in loc_type

    def test_non_eu_new_york(self):
        eligible, loc_type = job_hunter.is_eu_eligible("New York, USA")
        assert eligible is False
        assert loc_type == "not_eu"

    def test_non_eu_san_francisco(self):
        eligible, loc_type = job_hunter.is_eu_eligible("San Francisco, CA")
        assert eligible is False
        assert loc_type == "not_eu"

    def test_non_eu_toronto(self):
        eligible, loc_type = job_hunter.is_eu_eligible("Toronto, Canada")
        assert eligible is False
        assert loc_type == "not_eu"

    def test_remote_in_description_only(self):
        eligible, loc_type = job_hunter.is_eu_eligible("", "This is a fully remote position")
        assert eligible is True
        assert loc_type == "remote"

    def test_empty_strings(self):
        eligible, loc_type = job_hunter.is_eu_eligible("", "")
        assert eligible is False
        assert loc_type == "not_eu"

    def test_remote_keyword_case_insensitive(self):
        eligible, loc_type = job_hunter.is_eu_eligible("REMOTE EU")
        assert eligible is True
        assert loc_type == "remote"


# ─────────────────────────────────────────────────────────────
# job_id
# ─────────────────────────────────────────────────────────────

class TestJobId:
    def test_returns_12_chars(self):
        assert len(job_hunter.job_id("Operations Manager", "Acme Insurance")) == 12

    def test_deterministic(self):
        id1 = job_hunter.job_id("Operations Manager", "Acme Insurance")
        id2 = job_hunter.job_id("Operations Manager", "Acme Insurance")
        assert id1 == id2

    def test_case_insensitive(self):
        id_lower = job_hunter.job_id("operations manager", "acme insurance")
        id_upper = job_hunter.job_id("OPERATIONS MANAGER", "ACME INSURANCE")
        assert id_lower == id_upper

    def test_different_title_produces_different_id(self):
        id1 = job_hunter.job_id("Operations Manager", "Acme Insurance")
        id2 = job_hunter.job_id("Claims Manager", "Acme Insurance")
        assert id1 != id2

    def test_different_company_produces_different_id(self):
        id1 = job_hunter.job_id("Operations Manager", "Acme Insurance")
        id2 = job_hunter.job_id("Operations Manager", "Beta Insurance")
        assert id1 != id2

    def test_separator_prevents_collision(self):
        # "foo|bar" vs "foob|ar" — different despite same concat length
        id1 = job_hunter.job_id("foo", "bar")
        id2 = job_hunter.job_id("foob", "ar")
        assert id1 != id2

    def test_returns_hex_string(self):
        result = job_hunter.job_id("Operations Manager", "Acme Insurance")
        assert all(c in "0123456789abcdef" for c in result)


# ─────────────────────────────────────────────────────────────
# load_seen / save_seen (filesystem I/O)
# ─────────────────────────────────────────────────────────────

class TestLoadSeen:
    def test_returns_empty_set_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(tmp_path / "nonexistent.json"))
        assert job_hunter.load_seen() == set()

    def test_returns_correct_set_from_file(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        seen_file.write_text(json.dumps(["abc123", "def456"]))
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        assert job_hunter.load_seen() == {"abc123", "def456"}

    def test_returns_empty_set_on_malformed_json(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        seen_file.write_text("not valid json {{{")
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        assert job_hunter.load_seen() == set()

    def test_returns_empty_set_on_empty_file(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        seen_file.write_text("")
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        assert job_hunter.load_seen() == set()


class TestSaveSeen:
    def test_writes_json_file(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        job_hunter.save_seen({"abc123", "def456"})
        data = json.loads(seen_file.read_text())
        assert set(data) == {"abc123", "def456"}

    def test_creates_file_if_not_exists(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "new_seen.json"
        assert not seen_file.exists()
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        job_hunter.save_seen({"xyz"})
        assert seen_file.exists()

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        seen_file.write_text(json.dumps(["old_entry"]))
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        job_hunter.save_seen({"new_entry"})
        data = json.loads(seen_file.read_text())
        assert data == ["new_entry"]

    def test_saves_empty_set(self, tmp_path, monkeypatch):
        seen_file = tmp_path / "seen_jobs.json"
        monkeypatch.setattr(job_hunter, "SEEN_FILE", str(seen_file))
        job_hunter.save_seen(set())
        data = json.loads(seen_file.read_text())
        assert data == []


# ─────────────────────────────────────────────────────────────
# log_to_tracker (filesystem I/O)
# ─────────────────────────────────────────────────────────────

class TestLogToTracker:
    def _job(self, title="Ops Manager", company="Acme", source="Ashby", link="https://a.com"):
        return {"title": title, "company": company, "source": source, "link": link}

    def _ai(self, score=85, location_type="remote", salary_info="€70K", reason="Good match"):
        return {"score": score, "location_type": location_type,
                "salary_info": salary_info, "reason": reason}

    def test_creates_header_on_first_write(self, tmp_path, monkeypatch):
        tracker_file = tmp_path / "tracker.csv"
        monkeypatch.setattr(job_hunter, "TRACKER_FILE", str(tracker_file))
        job_hunter.log_to_tracker(self._job(), self._ai())
        rows = list(csv.DictReader(tracker_file.open()))
        assert len(rows) == 1
        assert set(rows[0].keys()) >= {"Date", "Title", "Company", "Source",
                                        "Score", "Location", "Salary", "Reason", "Link", "Status"}

    def test_writes_correct_field_values(self, tmp_path, monkeypatch):
        tracker_file = tmp_path / "tracker.csv"
        monkeypatch.setattr(job_hunter, "TRACKER_FILE", str(tracker_file))
        job_hunter.log_to_tracker(
            self._job(title="Claims Lead", company="Beta Corp"),
            self._ai(score=78, salary_info="€65K")
        )
        rows = list(csv.DictReader(tracker_file.open()))
        assert rows[0]["Title"] == "Claims Lead"
        assert rows[0]["Company"] == "Beta Corp"
        assert rows[0]["Score"] == "78"
        assert rows[0]["Salary"] == "€65K"
        assert rows[0]["Status"] == "New"

    def test_appends_on_subsequent_calls(self, tmp_path, monkeypatch):
        tracker_file = tmp_path / "tracker.csv"
        monkeypatch.setattr(job_hunter, "TRACKER_FILE", str(tracker_file))
        job_hunter.log_to_tracker(self._job(title="Ops Manager"), self._ai())
        job_hunter.log_to_tracker(self._job(title="Claims Lead"), self._ai())
        rows = list(csv.DictReader(tracker_file.open()))
        assert len(rows) == 2
        assert rows[0]["Title"] == "Ops Manager"
        assert rows[1]["Title"] == "Claims Lead"

    def test_no_duplicate_header_on_second_write(self, tmp_path, monkeypatch):
        tracker_file = tmp_path / "tracker.csv"
        monkeypatch.setattr(job_hunter, "TRACKER_FILE", str(tracker_file))
        for _ in range(3):
            job_hunter.log_to_tracker(self._job(), self._ai())
        rows = list(csv.DictReader(tracker_file.open()))
        # DictReader skips the header row; remaining rows should all be data
        assert len(rows) == 3
        for row in rows:
            assert row["Title"] == "Ops Manager"


# ─────────────────────────────────────────────────────────────
# fetch (HTTP)
# ─────────────────────────────────────────────────────────────

class TestFetch:
    def test_returns_response_on_200(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mocker.patch("job_hunter.requests.get", return_value=mock_response)
        assert job_hunter.fetch("https://example.com") is mock_response

    def test_returns_none_on_404(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mocker.patch("job_hunter.requests.get", return_value=mock_response)
        assert job_hunter.fetch("https://example.com") is None

    def test_returns_none_on_500(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mocker.patch("job_hunter.requests.get", return_value=mock_response)
        assert job_hunter.fetch("https://example.com") is None

    def test_returns_none_on_connection_error(self, mocker):
        mocker.patch("job_hunter.requests.get", side_effect=ConnectionError("refused"))
        assert job_hunter.fetch("https://example.com") is None

    def test_returns_none_on_timeout(self, mocker):
        mocker.patch("job_hunter.requests.get", side_effect=Exception("timed out"))
        assert job_hunter.fetch("https://example.com") is None

    def test_sends_user_agent_header(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get = mocker.patch("job_hunter.requests.get", return_value=mock_response)
        job_hunter.fetch("https://example.com")
        _, kwargs = mock_get.call_args
        assert "User-Agent" in kwargs["headers"]


# ─────────────────────────────────────────────────────────────
# scrape_ashby
# ─────────────────────────────────────────────────────────────

class TestScrapeAshby:
    def _resp(self, jobs_data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobs": jobs_data}
        return mock_resp

    def _eu_job(self, title="Operations Manager", location="Remote EU",
                workplace="remote", desc="Insurance operations role"):
        return {
            "title": title,
            "isListed": True,
            "location": location,
            "workplaceType": workplace,
            "descriptionPlain": desc,
            "jobUrl": "https://example.com/job/1",
            "compensation": {},
        }

    def test_returns_eu_eligible_jobs(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([self._eu_job()]))
        jobs = job_hunter.scrape_ashby()
        assert len(jobs) >= 1
        assert jobs[0]["title"] == "Operations Manager"
        assert jobs[0]["source"] == "Ashby"

    def test_skips_non_eu_jobs(self, mocker):
        non_eu = self._eu_job(location="New York, USA", workplace="onsite",
                              desc="Operations role in NYC")
        mocker.patch("job_hunter.fetch", return_value=self._resp([non_eu]))
        assert job_hunter.scrape_ashby() == []

    def test_skips_unlisted_jobs(self, mocker):
        unlisted = {**self._eu_job(), "isListed": False}
        mocker.patch("job_hunter.fetch", return_value=self._resp([unlisted]))
        assert job_hunter.scrape_ashby() == []

    def test_continues_gracefully_on_fetch_failure(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=None)
        assert job_hunter.scrape_ashby() == []

    def test_extracts_salary_from_compensation_tier(self, mocker):
        job = {**self._eu_job(location="Amsterdam"), "compensation": {"compensationTierSummary": "€60K–€80K"}}
        mocker.patch("job_hunter.fetch", return_value=self._resp([job]))
        jobs = job_hunter.scrape_ashby()
        assert len(jobs) >= 1
        assert jobs[0]["salary"] == "€60K–€80K"

    def test_returns_required_fields(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([self._eu_job()]))
        jobs = job_hunter.scrape_ashby()
        assert len(jobs) >= 1
        for field in ("title", "company", "link", "description", "location",
                      "location_type", "salary", "source"):
            assert field in jobs[0]


# ─────────────────────────────────────────────────────────────
# scrape_greenhouse
# ─────────────────────────────────────────────────────────────

class TestScrapeGreenhouse:
    def _resp(self, jobs_data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobs": jobs_data}
        return mock_resp

    def test_returns_eu_eligible_jobs(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([{
            "title": "Underwriting Ops Manager",
            "location": {"name": "London"},
            "content": "Underwriting operations role in London",
            "absolute_url": "https://example.com/gh/1",
        }]))
        jobs = job_hunter.scrape_greenhouse()
        assert len(jobs) >= 1
        assert jobs[0]["source"] == "Greenhouse"

    def test_skips_non_eu_jobs(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([{
            "title": "Data Analyst",
            "location": {"name": "Austin, TX"},
            "content": "Analytics role",
            "absolute_url": "https://example.com/gh/2",
        }]))
        assert job_hunter.scrape_greenhouse() == []

    def test_continues_gracefully_on_fetch_failure(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=None)
        assert job_hunter.scrape_greenhouse() == []


# ─────────────────────────────────────────────────────────────
# scrape_lever
# ─────────────────────────────────────────────────────────────

class TestScrapeLever:
    def _resp(self, postings):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = postings
        return mock_resp

    def test_returns_eu_eligible_jobs(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([{
            "text": "Insurance Operations Manager",
            "categories": {"location": "Remote Europe"},
            "descriptionPlain": "Remote insurance ops role",
            "hostedUrl": "https://jobs.lever.co/company/abc",
        }]))
        jobs = job_hunter.scrape_lever()
        assert len(jobs) >= 1
        assert jobs[0]["source"] == "Lever"

    def test_skips_non_eu_jobs(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=self._resp([{
            "text": "Software Engineer",
            "categories": {"location": "San Francisco"},
            "descriptionPlain": "",
            "hostedUrl": "https://jobs.lever.co/company/xyz",
        }]))
        assert job_hunter.scrape_lever() == []

    def test_continues_gracefully_on_fetch_failure(self, mocker):
        mocker.patch("job_hunter.fetch", return_value=None)
        assert job_hunter.scrape_lever() == []
