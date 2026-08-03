#!/usr/bin/env python3
"""Combine weekly SEO outputs into one issue-friendly Markdown report."""

from pathlib import Path

OUTPUT = Path("seo-output")
sections = []
for name in ("weekly-seo-report.md", "competitor-research.md", "technical-seo-audit.md"):
    path = OUTPUT / name
    if path.exists():
        sections.append(path.read_text(encoding="utf-8").strip())
(OUTPUT / "combined-weekly-report.md").write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
print(f"Combined {len(sections)} report sections")
