"""
Tests for company_scanner.py

Coverage areas:
- Pure logic: is_relevant, has_eu_signal, find_new
- Filesystem I/O: load_seen, save_seen
- HTTP: fetch
- Scraper: scan_rss_feeds
"""
import json
import pytest
from unittest.mock import MagicMock

import company_scanner


# ─────────────────────────────────────────────────────────────
# is_relevant
# ─────────────────────────────────────────────────────────────

class TestIsRelevant:
    def test_insurtech_keyword(self):
        assert company_scanner.is_relevant("New insurtech startup raises €10M")

    def test_insuretech_variant(self):
        assert company_scanner.is_relevant("Insuretech platform launches in EU")

    def test_insurance_tech_keyword(self):
        assert company_scanner.is_relevant("Insurance tech company announces expansion")

    def test_insurance_technology_keyword(self):
        assert company_scanner.is_relevant("Insurance technology platform for brokers")

    def test_parametric_insurance(self):
        assert company_scanner.is_relevant("Parametric insurance startup raises funding")

    def test_embedded_insurance(self):
        assert company_scanner.is_relevant("Embedded insurance API for e-commerce")

    def test_digital_insurance(self):
        assert company_scanner.is_relevant("Digital insurance marketplace launches")

    def test_insurance_platform(self):
        assert company_scanner.is_relevant("Insurance platform secures Series B")

    def test_insurance_startup(self):
        assert company_scanner.is_relevant("Insurance startup exits stealth mode")

    def test_mga_keyword_with_space(self):
        # INSURTECH_KEYWORDS contains "mga " (with trailing space)
        assert company_scanner.is_relevant("New mga  specialising in cyber launches")

    def test_managing_general_agent(self):
        assert company_scanner.is_relevant("Managing general agent raises Series A")

    def test_coverholder_keyword(self):
        assert company_scanner.is_relevant("Lloyd's coverholder approval granted")

    def test_delegated_underwriting(self):
        assert company_scanner.is_relevant("Delegated underwriting programme announced")

    def test_insurance_api(self):
        assert company_scanner.is_relevant("Insurance API platform secures €5M")

    def test_case_insensitive(self):
        assert company_scanner.is_relevant("INSURTECH STARTUP RAISES FUNDING")

    def test_no_match_general_fintech(self):
        assert not company_scanner.is_relevant("New fintech app for payments")

    def test_no_match_unrelated(self):
        assert not company_scanner.is_relevant("Machine learning model for image recognition")

    def test_empty_string(self):
        assert not company_scanner.is_relevant("")


# ─────────────────────────────────────────────────────────────
# has_eu_signal
# ─────────────────────────────────────────────────────────────

class TestHasEuSignal:
    def test_eu_keyword(self):
        assert company_scanner.has_eu_signal("The company is expanding to the eu market")

    def test_europe_keyword(self):
        assert company_scanner.has_eu_signal("Expanding to Europe this year")

    def test_european_keyword(self):
        assert company_scanner.has_eu_signal("European operations launched")

    def test_city_dublin(self):
        assert company_scanner.has_eu_signal("New office opening in Dublin")

    def test_city_amsterdam(self):
        assert company_scanner.has_eu_signal("Headquarters in Amsterdam")

    def test_city_paris(self):
        assert company_scanner.has_eu_signal("Paris office announced")

    def test_city_berlin(self):
        assert company_scanner.has_eu_signal("Berlin hub opening this quarter")

    def test_city_madrid(self):
        assert company_scanner.has_eu_signal("Madrid operations centre")

    def test_city_barcelona(self):
        assert company_scanner.has_eu_signal("Barcelona engineering hub")

    def test_city_london(self):
        assert company_scanner.has_eu_signal("London headquarters established")

    def test_solvency_ii(self):
        assert company_scanner.has_eu_signal("Solvency II compliant operations")

    def test_eiopa(self):
        assert company_scanner.has_eu_signal("EIOPA regulatory alignment")

    def test_pan_european(self):
        assert company_scanner.has_eu_signal("Pan-European expansion strategy")

    def test_dach(self):
        assert company_scanner.has_eu_signal("DACH market entry announced")

    def test_benelux(self):
        assert company_scanner.has_eu_signal("Benelux operations launched")

    def test_nordics(self):
        assert company_scanner.has_eu_signal("Nordics market entry planned")

    def test_case_insensitive(self):
        assert company_scanner.has_eu_signal("EUROPE expansion planned")

    def test_no_eu_signal_us_only(self):
        assert not company_scanner.has_eu_signal("US market focus, California operations")

    def test_no_eu_signal_asia(self):
        assert not company_scanner.has_eu_signal("Asia Pacific expansion, Singapore hub")

    def test_empty_string(self):
        assert not company_scanner.has_eu_signal("")


# ─────────────────────────────────────────────────────────────
# find_new
# ─────────────────────────────────────────────────────────────

class TestFindNew:
    def _article(self, title, source="InsTech London"):
        return {"source": source, "title": title, "url": "https://example.com", "snippet": ""}

    def test_returns_new_articles(self):
        articles = [self._article("New Insurtech Funding Round Announced Today")]
        result = company_scanner.find_new(articles, set())
        assert len(result) == 1

    def test_filters_already_seen_articles(self):
        article = self._article("New Insurtech Funding Round Announced Today")
        key = "InsTech London|New Insurtech Funding Round Announced Today"
        result = company_scanner.find_new([article], {key})
        assert result == []

    def test_filters_titles_15_chars_or_fewer(self):
        # Titles must be >15 chars to be included
        result = company_scanner.find_new([self._article("Short title")], set())
        assert result == []

    def test_includes_titles_16_chars_or_more(self):
        result = company_scanner.find_new([self._article("1234567890123456")], set())
        assert len(result) == 1

    def test_title_exactly_15_chars_is_excluded(self):
        result = company_scanner.find_new([self._article("123456789012345")], set())
        assert result == []

    def test_deduplicates_articles_with_same_60char_prefix(self):
        # Both titles share the same first 60 characters
        base = "Lloyd's Coverholder MGA Secures EU Expansion Approval This Q"  # 60 chars
        title_a = base + "1"
        title_b = base + "2"
        articles = [self._article(title_a, "InsTech"), self._article(title_b, "Sifted")]
        result = company_scanner.find_new(articles, set())
        assert len(result) == 1

    def test_does_not_deduplicate_distinct_titles(self):
        articles = [
            self._article("Insurtech Alpha Raises €10M for European Launch"),
            self._article("Insurtech Beta Raises €20M for US Launch"),
        ]
        result = company_scanner.find_new(articles, set())
        assert len(result) == 2

    def test_returns_key_and_article_tuples(self):
        article = self._article("New Insurtech Funding Round Announced Today")
        result = company_scanner.find_new([article], set())
        key, returned_article = result[0]
        assert key == "InsTech London|New Insurtech Funding Round Announced Today"
        assert returned_article["title"] == "New Insurtech Funding Round Announced Today"

    def test_empty_articles_list(self):
        assert company_scanner.find_new([], set()) == []


# ─────────────────────────────────────────────────────────────
# load_seen / save_seen (filesystem I/O)
# ─────────────────────────────────────────────────────────────

class TestLoadSeen:
    def test_returns_empty_set_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(tmp_path / "nonexistent.json"))
        assert company_scanner.load_seen() == set()

    def test_returns_correct_set_from_file(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        f.write_text(json.dumps(["key1", "key2"]))
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(f))
        assert company_scanner.load_seen() == {"key1", "key2"}

    def test_returns_empty_set_on_malformed_json(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        f.write_text("{{bad json")
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(f))
        assert company_scanner.load_seen() == set()


class TestSaveSeen:
    def test_writes_valid_json(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(f))
        company_scanner.save_seen({"key1", "key2"})
        data = json.loads(f.read_text())
        assert set(data) == {"key1", "key2"}

    def test_creates_file_if_not_exists(self, tmp_path, monkeypatch):
        f = tmp_path / "new_seen.json"
        assert not f.exists()
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(f))
        company_scanner.save_seen({"a"})
        assert f.exists()

    def test_overwrites_existing_content(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        f.write_text(json.dumps(["old"]))
        monkeypatch.setattr(company_scanner, "SEEN_FILE", str(f))
        company_scanner.save_seen({"new"})
        assert json.loads(f.read_text()) == ["new"]


# ─────────────────────────────────────────────────────────────
# fetch (HTTP)
# ─────────────────────────────────────────────────────────────

class TestFetch:
    def test_returns_response_on_200(self, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mocker.patch("company_scanner.requests.get", return_value=mock_resp)
        assert company_scanner.fetch("https://example.com") is mock_resp

    def test_returns_none_on_non_200(self, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mocker.patch("company_scanner.requests.get", return_value=mock_resp)
        assert company_scanner.fetch("https://example.com") is None

    def test_returns_none_on_exception(self, mocker):
        mocker.patch("company_scanner.requests.get", side_effect=ConnectionError("refused"))
        assert company_scanner.fetch("https://example.com") is None


# ─────────────────────────────────────────────────────────────
# scan_rss_feeds
# ─────────────────────────────────────────────────────────────

class TestScanRssFeeds:
    def _make_rss_response(self, title, description, link="https://example.com/article"):
        xml = (
            '<?xml version="1.0"?>'
            '<rss version="2.0"><channel>'
            f'<item><title>{title}</title>'
            f'<description>{description}</description>'
            f'<link>{link}</link>'
            '<pubDate>Mon, 05 Apr 2026 10:00:00 +0000</pubDate>'
            '</item></channel></rss>'
        ).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.content = xml
        return mock_resp

    def test_returns_articles_matching_both_filters(self, mocker):
        mock_resp = self._make_rss_response(
            "New insurtech startup launches in Amsterdam",
            "A digital insurance platform raises funding for European expansion"
        )
        mocker.patch("company_scanner.fetch", return_value=mock_resp)
        results = company_scanner.scan_rss_feeds()
        assert len(results) > 0

    def test_returned_article_has_required_fields(self, mocker):
        mock_resp = self._make_rss_response(
            "Insurtech platform raises €15M for EU expansion",
            "EU insurtech raises funding for Amsterdam and Dublin offices"
        )
        mocker.patch("company_scanner.fetch", return_value=mock_resp)
        results = company_scanner.scan_rss_feeds()
        assert len(results) > 0
        article = results[0]
        for field in ("title", "source", "url", "snippet", "date"):
            assert field in article

    def test_excludes_non_insurtech_articles(self, mocker):
        mock_resp = self._make_rss_response(
            "Traditional bank launches savings account in New York",
            "A major US bank launches a new savings product"
        )
        mocker.patch("company_scanner.fetch", return_value=mock_resp)
        results = company_scanner.scan_rss_feeds()
        assert results == []

    def test_excludes_insurtech_without_eu_signal(self, mocker):
        mock_resp = self._make_rss_response(
            "Insurtech startup raises Series A in New York",
            "A digital insurance platform focused on the US market"
        )
        mocker.patch("company_scanner.fetch", return_value=mock_resp)
        results = company_scanner.scan_rss_feeds()
        assert results == []

    def test_handles_feed_failure_gracefully(self, mocker):
        mocker.patch("company_scanner.fetch", return_value=None)
        results = company_scanner.scan_rss_feeds()
        assert results == []

    def test_handles_malformed_xml_gracefully(self, mocker):
        mock_resp = MagicMock()
        mock_resp.content = b"not xml at all {{{{"
        mocker.patch("company_scanner.fetch", return_value=mock_resp)
        results = company_scanner.scan_rss_feeds()
        assert results == []
