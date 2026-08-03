#!/usr/bin/env python3
"""Inventory and audit the Probate Home Buyer static HTML site."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

SITE_ORIGIN = "https://probatehomebuyer.co.uk"
VERIFICATION_TOKEN = "dNo010XWNI05mGKqiug7c4H5OwOnUiC-Y1PlY07dW8k"
OPERATIONAL_PREFIXES = ("/docs/", "/seo-reports/", "/scripts/", "/.github/")
SKIP_DIRS = {".git", ".github", "docs", "seo-reports", "scripts", "node_modules", "venv"}
INTENTIONAL_NOINDEX = {"/free-probate-property-offer/", "/thank-you/"}


@dataclass
class Page:
    file: str
    url: str
    title: str = ""
    description: str = ""
    h1s: list[str] = field(default_factory=list)
    canonical: str = ""
    page_type: str = "page"
    intent: str = ""
    internal_links: list[str] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    json_ld: list[object] = field(default_factory=list)
    json_ld_errors: list[str] = field(default_factory=list)
    publication_date: str = ""
    visible_text: str = ""
    noindex: bool = False
    verification_present: bool = False


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.h1s: list[str] = []
        self.description = ""
        self.canonical = ""
        self.links: list[str] = []
        self.images: list[dict[str, str]] = []
        self.forms: list[str] = []
        self.json_ld_raw: list[str] = []
        self.text_parts: list[str] = []
        self.noindex = False
        self.verification_present = False
        self._capture: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag in {"title", "h1"}:
            self._capture, self._buffer = tag, []
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._capture, self._buffer = "jsonld", []
        elif tag == "meta":
            name = values.get("name", "").lower()
            if name == "description":
                self.description = values.get("content", "").strip()
            elif name == "robots" and "noindex" in values.get("content", "").lower():
                self.noindex = True
            elif name == "google-site-verification" and values.get("content") == VERIFICATION_TOKEN:
                self.verification_present = True
        elif tag == "link" and "canonical" in values.get("rel", "").lower():
            self.canonical = values.get("href", "").strip()
        elif tag == "a":
            self.links.append(values.get("href", "").strip())
        elif tag == "img":
            self.images.append({"src": values.get("src", "").strip(), "alt": values.get("alt", "").strip()})
        elif tag == "form":
            self.forms.append(values.get("action", "").strip())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture == tag:
            value = normalise_text(" ".join(self._buffer))
            if tag == "title":
                self.title_parts.append(value)
            elif tag == "h1":
                self.h1s.append(value)
            self._capture, self._buffer = None, []
        elif tag == "script" and self._capture == "jsonld":
            self.json_ld_raw.append("".join(self._buffer).strip())
            self._capture, self._buffer = None, []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)
        if self._capture != "jsonld":
            self.text_parts.append(data)


def normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def route_for(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def preferred_html_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.html"):
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        # Sibling .html files duplicate directory index pages and exist for legacy redirects.
        if path.name not in {"index.html", "404.html"} and (path.parent / "index.html").exists():
            continue
        # Root .html files may duplicate canonical directory pages.
        if path.parent == root and path.name not in {"index.html", "404.html"} and (root / path.stem / "index.html").exists():
            continue
        files.append(path)
    return sorted(files)


def page_type_for(url: str) -> str:
    if url == "/": return "home"
    if url.startswith("/blog/") and url != "/blog/": return "blog article"
    if url == "/blog/": return "blog index"
    if url.startswith("/probate-guide/") and url != "/probate-guide/": return "probate guide"
    if url == "/probate-guide/": return "guide index"
    if url.startswith("/areas-we-buy-in/") and url != "/areas-we-buy-in/": return "location page"
    if "faq" in url: return "FAQ"
    if url in {"/sell-inherited-house/", "/sell-probate-property-needing-work/", "/free-probate-property-offer/"}: return "service page"
    if url in {"/privacy-policy/", "/cookie-policy/", "/terms/"}: return "legal"
    return "page"


def intent_for(page: Page) -> str:
    text = f"{page.title} {' '.join(page.h1s)}".lower()
    if page.page_type == "location page": return "commercial seller intent in a named location"
    if page.page_type == "service page": return "commercial seller intent"
    if any(term in text for term in ("sell", "buyer", "offer", "property needing work")):
        return "commercial seller intent"
    if page.page_type in {"blog article", "probate guide", "FAQ"}:
        return "informational executor, administrator or beneficiary intent"
    return "brand or supporting information"


def load_page(path: Path, root: Path) -> Page:
    parser = PageParser()
    content = path.read_text(encoding="utf-8", errors="replace")
    parser.feed(content)
    page = Page(
        file=path.relative_to(root).as_posix(),
        url=route_for(path, root),
        title=" ".join(parser.title_parts).strip(),
        description=parser.description,
        h1s=parser.h1s,
        canonical=parser.canonical,
        page_type=page_type_for(route_for(path, root)),
        internal_links=[link for link in parser.links if link.startswith("/")],
        images=parser.images,
        forms=parser.forms,
        visible_text=normalise_text(" ".join(parser.text_parts)),
        noindex=parser.noindex,
        verification_present=parser.verification_present,
    )
    for index, raw in enumerate(parser.json_ld_raw, 1):
        try:
            value = json.loads(raw)
            page.json_ld.append(value)
            entries = value if isinstance(value, list) else [value]
            for entry in entries:
                if isinstance(entry, dict) and entry.get("@type") == "BlogPosting":
                    page.publication_date = str(entry.get("datePublished", ""))
        except json.JSONDecodeError as exc:
            page.json_ld_errors.append(f"JSON-LD block {index}: {exc.msg}")
    if not page.publication_date and page.page_type == "blog article":
        posted = re.search(r"\bPosted\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b", page.visible_text)
        if posted:
            try:
                page.publication_date = datetime.strptime(posted.group(1), "%d %B %Y").date().isoformat()
            except ValueError:
                pass
    page.intent = intent_for(page)
    return page


def local_target(link: str, root: Path) -> Path | None:
    if not link or link.startswith(("#", "mailto:", "tel:", "javascript:", "//")):
        return None
    parsed = urlparse(link)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"probatehomebuyer.co.uk", "www.probatehomebuyer.co.uk"}:
            return None
        link_path = parsed.path
    elif parsed.scheme:
        return None
    else:
        link_path = parsed.path
    path = unquote(link_path).lstrip("/")
    candidate = root / path
    if link_path.endswith("/") or candidate.is_dir():
        candidate = candidate / "index.html"
    elif not candidate.suffix:
        candidate = candidate / "index.html"
    return candidate


def read_sitemap(root: Path) -> set[str]:
    sitemap = root / "sitemap.xml"
    if not sitemap.exists(): return set()
    tree = ET.parse(sitemap)
    result = set()
    for loc in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if loc.text: result.add(urlparse(loc.text.strip()).path or "/")
    return result


def secret_findings(root: Path) -> list[str]:
    """Catch common committed credential material without printing the secret itself."""
    patterns = (
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
        re.compile(r'"private_key"\s*:\s*"-----BEGIN'),
        re.compile(r"(?m)^(?:OPENAI_API_KEY|GOOGLE_APPLICATION_CREDENTIALS)\s*=\s*\S+"),
    )
    findings = []
    allowed_suffixes = {".html", ".xml", ".txt", ".md", ".py", ".yml", ".yaml", ".json", ".toml", ".env"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes: continue
        if any(part in {".git", "seo-output", ".venv", "node_modules"} for part in path.relative_to(root).parts): continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in patterns):
            findings.append(f"{path.relative_to(root).as_posix()}: possible committed secret material")
    return findings


def audit(root: Path, pages: list[Page]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = defaultdict(list)
    findings["errors"].extend(secret_findings(root))
    by_url = {page.url: page for page in pages}
    titles = Counter(page.title.lower() for page in pages if page.title)
    descriptions = Counter(page.description.lower() for page in pages if page.description)
    incoming = Counter()
    sitemap_paths = read_sitemap(root)

    for page in pages:
        if not page.title: findings["errors"].append(f"{page.url}: missing title")
        if not page.description and page.url != "/404.html": findings["errors"].append(f"{page.url}: missing meta description")
        if len(page.h1s) == 0: findings["errors"].append(f"{page.url}: missing H1")
        if len(page.h1s) > 1: findings["warnings"].append(f"{page.url}: multiple H1 headings ({len(page.h1s)})")
        if not page.canonical: findings["errors"].append(f"{page.url}: missing canonical")
        expected = SITE_ORIGIN + page.url
        if page.canonical and page.canonical != expected:
            findings["warnings"].append(f"{page.url}: canonical is {page.canonical!r}; expected {expected!r}")
        if page.noindex and page.url not in INTENTIONAL_NOINDEX: findings["errors"].append(f"{page.url}: contains unexpected noindex")
        if not page.verification_present and page.url != "/404.html":
            findings["errors"].append(f"{page.url}: protected Search Console verification tag is missing")
        if len(page.visible_text.split()) < 120 and page.page_type not in {"legal", "page"}:
            findings["notes"].append(f"{page.url}: possibly thin content ({len(page.visible_text.split())} words)")
        for error in page.json_ld_errors:
            findings["errors"].append(f"{page.url}: {error}")
        for image in page.images:
            if not image["alt"]: findings["warnings"].append(f"{page.url}: image missing alt text ({image['src']})")
            target = local_target(image["src"], root)
            if target and not target.exists(): findings["errors"].append(f"{page.url}: missing local image {image['src']}")
        for link in page.internal_links:
            target = local_target(link, root)
            if target and not target.exists(): findings["errors"].append(f"{page.url}: broken internal link {link}")
            link_path = urlparse(link).path
            if target and target.exists() and target.suffix.lower() == ".html":
                target_route = route_for(target, root)
                target_page = next((candidate for candidate in pages if candidate.file == target.relative_to(root).as_posix()), None)
                if target_page and target_page.canonical:
                    target_route = urlparse(target_page.canonical).path or "/"
                if target_route in by_url: incoming[target_route] += 1
            if any(link_path.startswith(prefix) for prefix in OPERATIONAL_PREFIXES):
                findings["errors"].append(f"{page.url}: public link to operational path {link}")
            if link.startswith("http://"):
                findings["warnings"].append(f"{page.url}: HTTP link should be reviewed ({link})")
        for action in page.forms:
            target = local_target(action, root)
            if action.startswith("/") and target and not target.exists():
                findings["errors"].append(f"{page.url}: broken form action {action}")
        if page.url.startswith("/blog/") and page.url != "/blog/":
            if re.search(r"\bUpdated\s+(?:\d{1,2}|[A-Z][a-z]+)", page.visible_text):
                findings["errors"].append(f"{page.url}: article displays 'Updated'; visible dates must use 'Posted' only")

    for value, count in titles.items():
        if count > 1: findings["warnings"].append(f"duplicate title used {count} times: {value}")
    for value, count in descriptions.items():
        if count > 1: findings["warnings"].append(f"duplicate meta description used {count} times: {value}")
    for page in pages:
        if page.url not in {"/", "/404.html", "/thank-you/"} and incoming[page.url] == 0:
            findings["warnings"].append(f"{page.url}: possible orphan (no canonical internal links found)")
        if page.url not in {"/404.html", "/thank-you/"} and page.url not in sitemap_paths:
            findings["warnings"].append(f"{page.url}: absent from sitemap")
    for path in sorted(sitemap_paths - set(by_url)):
        findings["errors"].append(f"sitemap URL has no canonical page: {path}")
    for path in sitemap_paths:
        if any(path.startswith(prefix) for prefix in OPERATIONAL_PREFIXES):
            findings["errors"].append(f"operational URL appears in sitemap: {path}")

    blog_index = by_url.get("/blog/")
    if blog_index:
        article_dates = {p.url: p.publication_date for p in pages if p.page_type == "blog article"}
        ordered = []
        for link in blog_index.internal_links:
            target = local_target(link, root)
            if target and target.exists():
                route = route_for(target, root)
                if route in article_dates and route not in ordered: ordered.append(route)
        dates = [article_dates[url] for url in ordered]
        if dates != sorted(dates, reverse=True):
            findings["warnings"].append("/blog/: article cards are not in strict reverse chronological order")
    return findings


def markdown_inventory(pages: list[Page]) -> str:
    lines = ["# Website content inventory", "", f"Generated from {len(pages)} canonical HTML pages.", "", "| URL | Type | Title | H1 | Intent | Published | Internal links |", "|---|---|---|---|---|---|---:|"]
    for page in pages:
        clean = lambda value: value.replace("|", "\\|")
        lines.append(f"| `{page.url}` | {clean(page.page_type)} | {clean(page.title)} | {clean(page.h1s[0] if page.h1s else '')} | {clean(page.intent)} | {page.publication_date or '—'} | {len(page.internal_links)} |")
    return "\n".join(lines) + "\n"


def markdown_audit(findings: dict[str, list[str]]) -> str:
    labels = (("errors", "Errors"), ("warnings", "Warnings"), ("notes", "Notes"))
    lines = ["# Static technical SEO audit", ""]
    for key, label in labels:
        items = sorted(set(findings.get(key, [])))
        lines.extend([f"## {label} ({len(items)})", ""])
        lines.extend([f"- {item}" for item in items] or ["- None."])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("seo-output"))
    parser.add_argument("--fail-on", choices=("none", "errors"), default="none")
    args = parser.parse_args()
    root = args.root.resolve()
    loaded = [load_page(path, root) for path in preferred_html_files(root)]
    # Keep one canonical representative when legacy aliases contain a full HTML copy.
    canonical_pages: dict[str, Page] = {}
    for page in loaded:
        key = page.canonical or (SITE_ORIGIN + page.url)
        expected_path = urlparse(key).path or "/"
        existing = canonical_pages.get(key)
        if existing is None or page.url == expected_path:
            canonical_pages[key] = page
    pages = sorted(canonical_pages.values(), key=lambda page: page.url)
    findings = audit(root, pages)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "content-inventory.json").write_text(json.dumps([asdict(p) for p in pages], indent=2), encoding="utf-8")
    (args.output_dir / "content-inventory.md").write_text(markdown_inventory(pages), encoding="utf-8")
    (args.output_dir / "technical-seo-audit.md").write_text(markdown_audit(findings), encoding="utf-8")
    print(f"Inventoried {len(pages)} pages: {len(set(findings.get('errors', [])))} errors, {len(set(findings.get('warnings', [])))} warnings")
    if args.fail_on == "errors" and findings.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
