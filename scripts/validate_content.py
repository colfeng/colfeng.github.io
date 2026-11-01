#!/usr/bin/env python3
"""Check editable content and, when available, the generated site's local links."""
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

import yaml

from refresh_citations import ROOT, front_matter


def validate():
    profile = yaml.safe_load((ROOT / "_data/profile.yml").read_text(encoding="utf-8"))
    groups = yaml.safe_load((ROOT / "_data/publication_groups.yml").read_text(encoding="utf-8"))
    keys = set()
    count = 0
    for path in sorted((ROOT / "_publications").glob("*.md")):
        paper = front_matter(path)
        for required in ("key", "title", "authors", "year", "category", "paper_url", "abbr", "venue", "sort_order"):
            assert paper.get(required) is not None, f"{path.name}: missing {required}"
        assert paper["key"] not in keys, f"Duplicate paper key: {paper['key']}"
        keys.add(paper["key"])
        assert paper["category"] in {group["key"] for group in groups}, f"{path.name}: unknown category"
        assert profile["name"] in paper["authors"], f"{path.name}: owner absent from authors"
        for mark in ("equal", "corresponding"):
            assert set(paper.get(mark, [])).issubset(paper["authors"]), f"{path.name}: invalid {mark} author"
        assert urlparse(paper["paper_url"]).scheme == "https", f"{path.name}: PAPER link needs https"
        for resource in paper.get("resources", []):
            assert resource["label"].upper() not in ("PAPER", "PDF"), f"{path.name}: duplicate primary paper button"
            assert urlparse(resource["url"]).scheme == "https", f"{path.name}: invalid resource URL"
        count += 1
    assert set(profile["selected_papers"]).issubset(keys), "Homepage selects an unknown paper key"
    cache = yaml.safe_load((ROOT / "_data/citations.yml").read_text(encoding="utf-8"))
    for key, citation in (cache.get("papers") or {}).items():
        assert type(citation["count"]) is int and citation["count"] >= 0, f"{key}: invalid citation count"
        assert urlparse(citation["url"]).netloc == "scholar.google.com", f"{key}: invalid Scholar URL"
    print(f"Content valid: {count} papers, {len(groups)} categories, {len(profile['selected_papers'])} selected papers.")

    if (ROOT / "_site/index.html").exists():
        from html.parser import HTMLParser

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []

            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key in ("href", "src") and value and value.startswith("/") and not value.startswith("//"):
                        self.links.append(value)

        generated = ROOT / "_site"
        pages = [generated / route for route in ("index.html", "publications/index.html", "cv/index.html", "services/index.html")]
        pages += list((generated / "publications").rglob("*.html"))
        for page in pages:
            assert page.exists(), f"Missing page: {page.relative_to(generated)}"
            text = page.read_text(encoding="utf-8")
            assert "{{" not in text and "{%" not in text, f"Unrendered Liquid: {page.name}"
            parser = Links()
            parser.feed(text)
            for link in parser.links:
                target = generated / unquote(urlparse(link).path).lstrip("/")
                assert target.is_file() or (target / "index.html").is_file(), f"Broken local link: {link}"
        print(f"Generated site valid: {len(set(pages))} pages checked for local links and template rendering.")


if __name__ == "__main__":
    try:
        validate()
    except (AssertionError, KeyError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
