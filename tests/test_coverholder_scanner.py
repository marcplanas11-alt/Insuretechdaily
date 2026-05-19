"""
Tests for coverholder_scanner.py

Coverage areas:
- Pure logic: has_keywords, sig_id, filter_new
- Filesystem I/O: load_seen, save_seen
- HTTP: fetch
- Scraper: scan_rss_for_coverholders
"""
import json
import pytest
from unittest.mock import MagicMock

import coverholder_scanner


# ─────────────────────────────────────────────────────────────
# has_keywords
# ─────────────────────────────────────────────────────────────

class TestHasKeywords:
    def test_matches_single_keyword(self):
        assert coverholder_scanner.has_keywords(
            "Lloyd's coverholder approved",
            ["coverholder"]
        )

    def test_no_match(self):
        assert not coverholder_scanner.has_keywords(
            "Software company raises funding",
            ["coverholder"]
        )

    def test_case_insensitive(self):
        assert coverholder_scanner.has_keywords(
            "COVERHOLDER STATUS GRANTED",
            ["coverholder"]
        )

    def test_matches_any_keyword_in_list(self):
        assert coverholder_scanner.has_keywords(
            "New MGA launches specialty lines",
            ["coverholder", "mga"]
        )

    def test_partial_substring_match(self):
        # "mga" as substring of "managemental" should NOT match if not in text,
        # but "mga" should match inside "tmga" (substring)
        assert coverholder_scanner.has_keywords("New mga product", ["mga"])

    def test_empty_text(self):
        assert not coverholder_scanner.has_keywords("", ["coverholder"])

    def test_empty_keywords_list(self):
        assert not coverholder_scanner.has_keywords("Some coverholder text", [])

    def test_both_empty(self):
        assert not coverholder_scanner.has_keywords("", [])

    def test_matches_multi_word_keyword(self):
        assert coverholder_scanner.has_keywords(
            "binding authority granted to new MGA",
            ["binding authority"]
        )


# ─────────────────────────────────────────────────────────────
# sig_id
# ─────────────────────────────────────────────────────────────

class TestSigId:
    def test_returns_12_chars(self):
        assert len(coverholder_scanner.sig_id("New Coverholder Approval", "Insurance Edge")) == 12

    def test_deterministic(self):
        id1 = coverholder_scanner.sig_id("New Coverholder Approval", "Insurance Edge")
        id2 = coverholder_scanner.sig_id("New Coverholder Approval", "Insurance Edge")
        assert id1 == id2

    def test_case_insensitive(self):
        id_lower = coverholder_scanner.sig_id("new coverholder approval", "insurance edge")
        id_upper = coverholder_scanner.sig_id("NEW COVERHOLDER APPROVAL", "INSURANCE EDGE")
        assert id_lower == id_upper

    def test_different_title_produces_different_id(self):
        id1 = coverholder_scanner.sig_id("Coverholder A approved", "Insurance Edge")
        id2 = coverholder_scanner.sig_id("Coverholder B approved", "Insurance Edge")
        assert id1 != id2

    def test_different_source_produces_different_id(self):
        id1 = coverholder_scanner.sig_id("Coverholder approved", "Insurance Edge")
        id2 = coverholder_scanner.sig_id("Coverholder approved", "InsTech London")
        assert id1 != id2

    def test_returns_hex_string(self):
        result = coverholder_scanner.sig_id("Some title", "Some source")
        assert all(c in "0123456789abcdef" for c in result)

    def test_separator_prevents_collision(self):
        id1 = coverholder_scanner.sig_id("foo", "bar")
        id2 = coverholder_scanner.sig_id("foob", "ar")
        assert id1 != id2


# ─────────────────────────────────────────────────────────────
# filter_new
# ─────────────────────────────────────────────────────────────

class TestFilterNew:
    def _signal(self, title, source="Insurance Edge"):
        return {
            "title": title,
            "source": source,
            "url": "https://example.com",
            "snippet": "Some snippet text here",
            "type": "coverholder",
            "has_eu": True,
        }

    def test_returns_new_signals(self):
        signals = [self._signal("New Lloyd's coverholder approval announced today")]
        result = coverholder_scanner.filter_new(signals, set())
        assert len(result) == 1
        assert result[0]["title"] == "New Lloyd's coverholder approval announced today"

    def test_filters_already_seen_signals(self):
        signal = self._signal("New Lloyd's coverholder approval announced today")
        sid = coverholder_scanner.sig_id(signal["title"], signal["source"])
        result = coverholder_scanner.filter_new([signal], {sid})
        assert result == []

    def test_mutates_seen_set_with_new_ids(self):
        signal = self._signal("New Lloyd's coverholder approval announced today")
        seen = set()
        coverholder_scanner.filter_new([signal], seen)
        expected_sid = coverholder_scanner.sig_id(signal["title"], signal["source"])
        assert expected_sid in seen

    def test_deduplicates_near_duplicate_titles(self):
        # Both titles share the same first 60 characters
        base = "Lloyd's Coverholder Aspect MGA Approved for EU Expansion In"  # 60 chars
        signals = [
            self._signal(base + " Q1", "Insurance Edge"),
            self._signal(base + " Q2", "InsTech London"),
        ]
        result = coverholder_scanner.filter_new(signals, set())
        assert len(result) == 1

    def test_allows_distinct_titles(self):
        signals = [
            self._signal("New Lloyd's coverholder Aspect MGA gets EU approval"),
            self._signal("Loadsure receives Lloyd's binding authority for EU cargo"),
        ]
        result = coverholder_scanner.filter_new(signals, set())
        assert len(result) == 2

    def test_empty_signals_list(self):
        assert coverholder_scanner.filter_new([], set()) == []

    def test_does_not_return_already_seen_on_second_call(self):
        signal = self._signal("New Lloyd's coverholder approval announced today")
        seen = set()
        first = coverholder_scanner.filter_new([signal], seen)
        second = coverholder_scanner.filter_new([signal], seen)
        assert len(first) == 1
        assert len(second) == 0

    def test_preserves_signal_fields(self):
        signal = self._signal("New Lloyd's coverholder approval announced today")
        signal["has_eu"] = True
        signal["type"] = "coverholder"
        result = coverholder_scanner.filter_new([signal], set())
        assert result[0]["has_eu"] is True
        assert result[0]["type"] == "coverholder"


# ─────────────────────────────────────────────────────────────
# load_seen / save_seen (filesystem I/O)
# ─────────────────────────────────────────────────────────────

class TestLoadSeen:
    def test_returns_empty_set_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(tmp_path / "nonexistent.json"))
        assert coverholder_scanner.load_seen() == set()

    def test_returns_correct_set_from_file(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        f.write_text(json.dumps(["id1", "id2"]))
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(f))
        assert coverholder_scanner.load_seen() == {"id1", "id2"}

    def test_returns_empty_set_on_malformed_json(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        f.write_text("{bad json}")
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(f))
        assert coverholder_scanner.load_seen() == set()


class TestSaveSeen:
    def test_writes_valid_json(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(f))
        coverholder_scanner.save_seen({"id1", "id2"})
        data = json.loads(f.read_text())
        assert set(data) == {"id1", "id2"}

    def test_creates_file_if_not_exists(self, tmp_path, monkeypatch):
        f = tmp_path / "new_seen.json"
        assert not f.exists()
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(f))
        coverholder_scanner.save_seen({"a"})
        assert f.exists()

    def test_saves_empty_set(self, tmp_path, monkeypatch):
        f = tmp_path / "seen.json"
        monkeypatch.setattr(coverholder_scanner, "SEEN_FILE", str(f))
        coverholder_scanner.save_seen(set())
        assert json.loads(f.read_text()) == []


# ─────────────────────────────────────────────────────────────
# fetch (HTTP)
# ─────────────────────────────────────────────────────────────

class TestFetch:
    def test_returns_response_on_200(self, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mocker.patch("coverholder_scanner.requests.get", return_value=mock_resp)
        assert coverholder_scanner.fetch("https://example.com") is mock_resp

    def test_returns_none_on_404(self, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mocker.patch("coverholder_scanner.requests.get", return_value=mock_resp)
        assert coverholder_scanner.fetch("https://example.com") is None

    def test_returns_none_on_exception(self, mocker):
        mocker.patch("coverholder_scanner.requests.get", side_effect=Exception("timeout"))
        assert coverholder_scanner.fetch("https://example.com") is None


# ─────────────────────────────────────────────────────────────
# scan_rss_for_coverholders
# ─────────────────────────────────────────────────────────────

class TestScanRssForCoverholders:
    def _make_rss(self, title, description):
        xml = (
            '<?xml version="1.0"?>'
            '<rss><channel>'
            f'<item><title>{title}</title>'
            f'<description>{description}</description>'
            '<link>https://example.com/article</link>'
            '</item></channel></rss>'
        ).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.content = xml
        return mock_resp

    def test_detects_coverholder_signal(self, mocker):
        mock_resp = self._make_rss(
            "New Lloyd's coverholder granted binding authority",
            "A new managing general agent receives delegated authority approval"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert len(results) > 0
        assert any(r["type"] == "coverholder" for r in results)

    def test_detects_mga_eu_expansion_signal(self, mocker):
        mock_resp = self._make_rss(
            "Insurtech MGA announces EU expansion plans",
            "Managing general agent expanding to Spain and Netherlands operations"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert len(results) > 0
        assert any(r["type"] == "mga_eu_expansion" for r in results)

    def test_excludes_irrelevant_articles(self, mocker):
        mock_resp = self._make_rss(
            "Tech company raises Series B round",
            "A software startup raises funding for product development"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert results == []

    def test_excludes_mga_without_eu_signal(self, mocker):
        mock_resp = self._make_rss(
            "New MGA launches specialty lines in US market",
            "Managing general agent focused on domestic US operations"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert results == []

    def test_handles_feed_failure_gracefully(self, mocker):
        mocker.patch("coverholder_scanner.fetch", return_value=None)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert results == []

    def test_handles_malformed_xml_gracefully(self, mocker):
        mock_resp = MagicMock()
        mock_resp.content = b"<not valid xml <<<"
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert results == []

    def test_returned_signal_has_required_fields(self, mocker):
        mock_resp = self._make_rss(
            "New Lloyd's coverholder gets binding authority",
            "A coverholder expansion into the EU market announced"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert len(results) > 0
        signal = results[0]
        for field in ("title", "source", "url", "snippet", "type", "has_eu"):
            assert field in signal

    def test_sets_has_eu_flag(self, mocker):
        mock_resp = self._make_rss(
            "New Lloyd's coverholder gets binding authority in Netherlands",
            "A coverholder expanding to Netherlands and Spain market"
        )
        mocker.patch("coverholder_scanner.fetch", return_value=mock_resp)
        results = coverholder_scanner.scan_rss_for_coverholders()
        assert len(results) > 0
        assert results[0]["has_eu"] is True
