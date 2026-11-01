"""Regression checks for citation data integrity and failed network refreshes."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import yaml

import refresh_citations as refresh


def row(title, count, paper_id="user:paper"):
    return (f'<tr class="gsc_a_tr"><td><a class="gsc_a_at" '
            f'href="/citations?citation_for_view={paper_id}">{title}</a></td>'
            f'<td><a class="gsc_a_ac gs_ibl" '
            f'href="https://scholar.google.com/scholar?cites=123">{count}</a></td></tr>')


class CitationIntegrity(unittest.TestCase):
    def test_verified_counts_include_zero_but_omit_blank_counts(self):
        rows = refresh.parsed_rows(row("Cited work", "1,234") + row("New work", "0") + row("Missing", ""))
        self.assertEqual([(r["title"], r["count"]) for r in rows], [("Cited work", 1234), ("New work", 0)])

    def test_verification_and_unrecognized_pages_are_rejected(self):
        for html in ("<h1>Unusual traffic</h1>", "<html>Sign in</html>", row("Unknown", "")):
            with self.subTest(html=html), self.assertRaises(ValueError):
                refresh.parsed_rows(html)

    def test_unmatched_existing_papers_keep_counts_and_original_timestamp(self):
        existing = {"count": 27, "url": "https://scholar.google.com/scholar?cites=456", "updated_at": "old"}
        old = {"papers": {"missing": existing}}
        papers = [{"key": "match", "title": "Cited work"}, {"key": "missing", "title": "Other work"}]
        new, matched = refresh.refreshed_cache(old, papers, refresh.parsed_rows(row("Cited work", "9")), "today")
        self.assertEqual(matched, 1)
        self.assertEqual(new["papers"]["missing"], existing)
        self.assertEqual(new["papers"]["match"]["count"], 9)
        self.assertEqual(old, {"papers": {"missing": existing}})

    def test_explicit_id_can_match_a_changed_scholar_title(self):
        paper = {"key": "match", "title": "Local title", "scholar_id": "user:paper"}
        new, _ = refresh.refreshed_cache({}, [paper], refresh.parsed_rows(row("Scholar title", "4")), "today")
        self.assertEqual(new["papers"]["match"]["count"], 4)

    def test_duplicate_or_mismatched_titles_cannot_replace_the_cache(self):
        for html in (row("Other work", "7"), row("Cited work", "7") + row("Cited work", "8")):
            with self.subTest(html=html), self.assertRaises(ValueError):
                refresh.refreshed_cache({}, [{"key": "match", "title": "Cited work"}], refresh.parsed_rows(html), "today")

    def test_http_429_keeps_cache_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "_data").mkdir()
            (root / "_publications").mkdir()
            (root / "_data/profile.yml").write_text("scholar_user_id: user\n")
            cache = root / "_data/citations.yml"
            before = "source: Google Scholar\nlast_updated: yesterday\npapers: {}\n"
            cache.write_text(before)
            (root / "_publications/work.md").write_text("---\nkey: work\ntitle: Cited work\n---\n")
            error = HTTPError("https://scholar.google.com/citations", 429, "Too Many Requests", {}, None)
            with patch.object(refresh, "ROOT", root), patch.object(refresh, "urlopen", side_effect=error), patch("sys.argv", ["refresh_citations.py"]):
                with self.assertRaises(HTTPError):
                    refresh.main()
            self.assertEqual(cache.read_text(), before)

    def test_successful_fixture_refresh_updates_cache_and_dry_run_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "_data").mkdir()
            (root / "_publications").mkdir()
            (root / "_data/profile.yml").write_text("scholar_user_id: user\n")
            cache = root / "_data/citations.yml"
            cache.write_text("papers: {}\n")
            (root / "_publications/work.md").write_text("---\nkey: work\ntitle: Cited work\n---\n")
            fixture = root / "scholar.html"
            fixture.write_text(row("Cited work", "23"))
            argv = ["refresh_citations.py", "--fixture", str(fixture)]
            with patch.object(refresh, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                with patch("sys.argv", argv + ["--dry-run"]):
                    refresh.main()
                self.assertEqual(cache.read_text(), "papers: {}\n")
                with patch("sys.argv", argv):
                    refresh.main()
            self.assertEqual(yaml.safe_load(cache.read_text())["papers"]["work"]["count"], 23)


if __name__ == "__main__":
    unittest.main()
