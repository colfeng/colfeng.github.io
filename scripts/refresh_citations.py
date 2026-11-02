#!/usr/bin/env python3
"""Refresh a Google Scholar cache; leave the file intact on fetch/parse failure."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]


def front_matter(path: Path) -> dict:
    parts = path.read_text(encoding="utf-8").split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"Missing YAML front matter: {path.name}")
    return yaml.safe_load(parts[1])


def normalized_title(title: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", title).casefold() if c.isalnum())


class ScholarRows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.field = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "tr" and "gsc_a_tr" in classes:
            self.row = {"title": "", "count": "", "paper_url": "", "citation_url": ""}
        if self.row is not None and tag == "a":
            if "gsc_a_at" in classes:
                self.field = "title"
                self.row["paper_url"] = attrs.get("href", "")
            elif "gsc_a_ac" in classes:
                self.field = "count"
                self.row["citation_url"] = attrs.get("href", "")

    def handle_data(self, data):
        if self.row is not None and self.field:
            self.row[self.field] += data

    def handle_endtag(self, tag):
        if tag == "a":
            self.field = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
            self.field = None


def parsed_rows(html: str) -> list[dict]:
    if any(marker in html.casefold() for marker in ("unusual traffic", "recaptcha", "not a robot")):
        raise ValueError("Google Scholar returned a verification page; cache kept.")
    parser = ScholarRows()
    parser.feed(html)
    if not parser.rows:
        raise ValueError("No recognizable Scholar publication rows; cache kept.")
    rows = []
    for row in parser.rows:
        raw_count = row["count"].strip().replace(",", "").replace("\u00a0", "")
        if not re.fullmatch(r"\d+", raw_count):
            continue
        url = urljoin("https://scholar.google.com", row["citation_url"])
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "scholar.google.com" or not parsed.query:
            continue
        scholar_id = parse_qs(urlparse(row["paper_url"]).query).get("citation_for_view", [None])[0]
        rows.append({"title": row["title"].strip(), "scholar_id": scholar_id,
                     "count": int(raw_count), "url": url})
    if not rows:
        raise ValueError("No verified citation counts in Scholar response; cache kept.")
    return rows


def refreshed_cache(old: dict, papers: list[dict], rows: list[dict], timestamp: str) -> tuple[dict, int]:
    cached = dict(old.get("papers") or {})
    matched = 0
    for paper in papers:
        scholar_id = paper.get("scholar_id")
        matches = [row for row in rows if
                   (row["scholar_id"] == scholar_id if scholar_id else
                    normalized_title(row["title"]) == normalized_title(paper["title"]))]
        if len(matches) != 1:
            continue
        row = matches[0]
        cached[paper["key"]] = {"count": row["count"], "url": row["url"], "updated_at": timestamp}
        matched += 1
    if not matched:
        raise ValueError("Scholar response matched no local papers; cache kept.")
    return {"source": "Google Scholar", "last_updated": timestamp, "papers": cached}, matched


def fetch_serpapi_rows(scholar_user_id: str, api_key: str) -> list[dict]:
    """Get Google Scholar author citation counts through SerpApi.

    Counts are from Google Scholar, not SerpApi's own bibliometric index.
    """
    rows = []
    for start in range(0, 300, 100):
        params = urlencode({
            "engine": "google_scholar_author",
            "author_id": scholar_user_id,
            "hl": "en",
            "num": 100,
            "start": start,
            "api_key": api_key,
        })
        request = Request(
            "https://serpapi.com/search.json?" + params,
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise ValueError("Invalid SerpApi Google Scholar response.")
        if data.get("error"):
            raise ValueError("SerpApi Google Scholar error: " + str(data["error"]))
        articles = data.get("articles") or []
        if not isinstance(articles, list):
            raise ValueError("Invalid Google Scholar article list.")
        for article in articles:
            if not isinstance(article, dict):
                continue
            scholar_id = article.get("citation_id")
            title = article.get("title")
            cited_by = article.get("cited_by") or {}
            count = cited_by.get("value") if isinstance(cited_by, dict) else None
            if not (isinstance(scholar_id, str)
                    and scholar_id.startswith(scholar_user_id + ":")
                    and re.fullmatch(r"[A-Za-z0-9_-]+", scholar_id.split(":", 1)[1])
                    and isinstance(title, str)
                    and type(count) is int and count >= 0):
                continue
            citation_url = cited_by.get("link") or article.get("link")
            if not isinstance(citation_url, str) or (
                urlparse(citation_url).scheme != "https"
                or urlparse(citation_url).netloc != "scholar.google.com"
            ):
                citation_url = "https://scholar.google.com/citations?" + urlencode({
                    "view_op": "view_citation",
                    "user": scholar_user_id,
                    "citation_for_view": scholar_id,
                })
            rows.append({
                "title": title,
                "scholar_id": scholar_id,
                "count": count,
                "url": citation_url,
            })
        if len(articles) < 100:
            break
    if not rows:
        raise ValueError("SerpApi returned no verified Google Scholar citation counts.")
    return rows


def fetch_scholarly_rows(scholar_user_id: str) -> list[dict]:
    """Read publication counts from the owner's Google Scholar profile."""
    from scholarly import scholarly

    scholarly.set_timeout(15)
    scholarly.set_retries(2)
    author = scholarly.search_author_id(scholar_user_id)
    author = scholarly.fill(author, sections=["publications"])
    results = []
    for publication in author.get("publications", []):
        title = (publication.get("bib") or {}).get("title")
        count = publication.get("num_citations")
        pub_id = publication.get("pub_id") or publication.get("author_pub_id")
        if not isinstance(title, str) or type(count) is not int or count < 0:
            continue
        if not isinstance(pub_id, str):
            continue
        article_id = pub_id.rsplit(":", 1)[-1]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", article_id):
            continue
        full_id = f"{scholar_user_id}:{article_id}"
        url = "https://scholar.google.com/citations?" + urlencode({
            "view_op": "view_citation", "hl": "en",
            "user": scholar_user_id, "citation_for_view": full_id,
        })
        results.append({
            "title": title, "scholar_id": full_id, "count": count, "url": url,
        })
    if not results:
        raise ValueError("No usable Google Scholar publication counts from scholarly.")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, help="Read a saved Scholar HTML response for validation")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without writing the cache")
    args = parser.parse_args()
    profile = yaml.safe_load((ROOT / "_data/profile.yml").read_text(encoding="utf-8"))
    cache_path = ROOT / "_data/citations.yml"
    old = yaml.safe_load(cache_path.read_text(encoding="utf-8")) or {}
    papers = [front_matter(path) for path in sorted((ROOT / "_publications").glob("*.md"))]
    if args.fixture:
        rows = parsed_rows(args.fixture.read_text(encoding="utf-8"))
    else:
        rows = None
        api_key = os.environ.get("SERPAPI_KEY", "").strip()
        if api_key:
            try:
                rows = fetch_serpapi_rows(profile["scholar_user_id"], api_key)
                print(f"SerpApi retrieved {len(rows)} Google Scholar records.")
            except Exception as api_error:
                print(f"SerpApi Google Scholar request failed: {api_error}", file=sys.stderr)
        if rows is None:
            try:
                rows = fetch_scholarly_rows(profile["scholar_user_id"])
                print(f"scholarly retrieved {len(rows)} Google Scholar records.")
            except Exception as scholar_error:
                print(f"scholarly could not read Google Scholar: {scholar_error}", file=sys.stderr)
                print("Trying the original Google Scholar HTML parser.", file=sys.stderr)
                query = urlencode({"user": profile["scholar_user_id"], "hl": "en", "cstart": 0, "pagesize": 100})
                request = Request("https://scholar.google.com/citations?" + query,
                                  headers={"User-Agent": "Academic-Homepage-Citations/1.0", "Accept-Language": "en"})
                with urlopen(request, timeout=30) as response:
                    rows = parsed_rows(response.read().decode("utf-8", errors="replace"))
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new, matched = refreshed_cache(old, papers, rows, timestamp)
    if not args.dry_run:
        # Write beside the cache, then replace atomically only after full validation.
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=cache_path.parent, delete=False) as tmp:
            yaml.safe_dump(new, tmp, allow_unicode=True, sort_keys=False)
            temporary_path = Path(tmp.name)
        temporary_path.replace(cache_path)
    print(f"Validated {matched}/{len(papers)} papers; unmatched papers retain their previous counts."
          + (" Dry run: cache unchanged." if args.dry_run else " Cache refreshed."))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Citation refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
