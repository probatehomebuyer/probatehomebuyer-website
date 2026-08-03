#!/usr/bin/env python3
"""Optional, transparent competitor content scan using public pages and sitemaps."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

USER_AGENT = "ProbateHomeBuyer-SEO-Research/1.0 (+https://probatehomebuyer.co.uk/)"
MAX_URLS_PER_DOMAIN = 100
RELEVANT_TERMS = ("probate", "inherited", "executor", "empty house", "house clearance", "needs work", "cash buyer", "sell house")


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title, self.description, self.h1 = "", "", ""
        self._capture = ""
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag in {"title", "h1"} and not getattr(self, tag):
            self._capture, self._buffer = tag, []
        if tag == "meta" and values.get("name", "").lower() == "description":
            self.description = values.get("content", "").strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == self._capture:
            setattr(self, tag, re.sub(r"\s+", " ", " ".join(self._buffer)).strip())
            self._capture, self._buffer = "", []

    def handle_data(self, data: str) -> None:
        if self._capture: self._buffer.append(data)


def fetch(url: str, timeout: int = 15) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(2_000_000).decode("utf-8", errors="replace"), content_type


def sitemap_urls(base_url: str) -> list[str]:
    sitemap_url = urljoin(base_url.rstrip("/") + "/", "sitemap.xml")
    xml, _ = fetch(sitemap_url)
    root = ET.fromstring(xml)
    urls = [node.text.strip() for node in root.findall(".//{*}loc") if node.text]
    # Do not recursively crawl sitemap indexes; this is intentionally bounded and polite.
    return [url for url in urls if url.lower().endswith(".xml") is False][:MAX_URLS_PER_DOMAIN]


def scan_domain(base_url: str) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    try:
        urls = sitemap_urls(base_url)
    except Exception as exc:
        warnings.append(f"Could not read sitemap for {base_url}: {exc}")
        urls = [base_url]
    pages = []
    for url in urls:
        try:
            html, content_type = fetch(url)
            if "html" not in content_type.lower() and "<html" not in html[:1000].lower(): continue
            parsed = MetadataParser(); parsed.feed(html)
            haystack = f"{parsed.title} {parsed.description} {parsed.h1}".lower()
            if any(term in haystack for term in RELEVANT_TERMS):
                pages.append({"url": url, "title": parsed.title, "description": parsed.description, "h1": parsed.h1})
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            warnings.append(f"Skipped {url}: {exc}")
    return pages, warnings


def tokens(text: str) -> set[str]:
    stop = {"and", "the", "for", "with", "your", "you", "how", "can", "house", "property", "probate"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 3 and word not in stop}


def render(results: dict[str, list[dict[str, str]]], warnings: list[str], inventory: list[dict]) -> str:
    own_topics = [(page["url"], tokens(f"{page.get('title','')} {page.get('description','')} {' '.join(page.get('h1s', []))}")) for page in inventory]
    lines = ["# Competitor content research", "", "This bounded scan reads only publicly available competitor sitemaps and page metadata. It does not scrape search-result pages and does not copy competitor content.", "", "Competitor coverage is a research signal only. Search Console evidence and genuine user usefulness remain the basis for recommendations.", ""]
    for domain, pages in results.items():
        lines.extend([f"## {domain}", "", "| Page | Title | Closest existing PHB page |", "|---|---|---|"])
        for page in pages:
            topic = tokens(f"{page['title']} {page['description']} {page['h1']}")
            matches = sorted(((len(topic & own) / max(len(topic), 1), url) for url, own in own_topics), reverse=True)
            score, closest = matches[0] if matches else (0, "—")
            decision = f"`{closest}` ({score:.0%} metadata-term overlap)" if score else "No clear match; manual review required"
            safe_title = page["title"].replace("|", "\\|")
            lines.append(f"| {page['url']} | {safe_title} | {decision} |")
        if not pages: lines.append("| — | No relevant public pages found | — |")
        lines.append("")
    lines.extend(["## Safeguards", "", "- Never create content solely because a competitor has a page.", "- Never copy wording, structure, examples or claims.", "- Prefer improving an existing PHB URL when its intent overlaps.", "- A human must approve any resulting content work in a separate pull request.", ""])
    if warnings:
        lines.extend(["## Scan warnings", ""] + [f"- {warning}" for warning in warnings] + [""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("seo-output/competitor-research.md"))
    args = parser.parse_args()
    configured = os.environ.get("SEO_COMPETITOR_URLS", "").strip()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    if not configured:
        text = "# Competitor content research\n\nCompetitor scanning is disabled. Add the optional `SEO_COMPETITOR_URLS` Actions variable as a comma-separated list of HTTPS website origins to enable it.\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print("Competitor scan skipped: SEO_COMPETITOR_URLS is not configured")
        return 0
    urls = [value.strip().rstrip("/") + "/" for value in configured.split(",") if value.strip()]
    if len(urls) > 10:
        print("ERROR: configure no more than 10 competitor domains per run", file=sys.stderr)
        return 2
    invalid = [url for url in urls if urlparse(url).scheme != "https" or not urlparse(url).netloc]
    if invalid:
        print(f"ERROR: competitor URLs must be HTTPS origins: {', '.join(invalid)}", file=sys.stderr)
        return 2
    results, warnings = {}, []
    for url in urls:
        pages, domain_warnings = scan_domain(url)
        results[urlparse(url).netloc] = pages
        warnings.extend(domain_warnings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(results, warnings, inventory), encoding="utf-8")
    print(f"Scanned {len(urls)} configured competitor domains")
    return 0


if __name__ == "__main__":
    sys.exit(main())
