#!/usr/bin/env python3
"""Create a weekly SEO opportunity report from the official Search Console API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

COMMERCIAL_TERMS = (
    "sell", "buyer", "cash buyer", "cash offer", "inherited house", "inherited property",
    "probate property", "needs work", "need work", "renovation", "empty house", "direct sale",
    "quick sale", "fast sale", "house clearance", "executor sell",
)
EXCLUDED_TERMS = (
    "for sale", "buy probate", "probate houses to buy", "investment", "investor leads",
    "solicitor", "lawyer", "jobs", "career", "salary", "training", "course",
)
STOPWORDS = {"a", "an", "and", "are", "can", "do", "for", "how", "in", "is", "it", "of", "on", "the", "to", "uk", "what", "when", "with"}


@dataclass
class Period:
    start: date
    end: date

    def label(self) -> str:
        return f"{self.start.isoformat()} to {self.end.isoformat()}"


def complete_periods(today: date) -> tuple[Period, Period]:
    current_end = today - timedelta(days=3)
    current_start = current_end - timedelta(days=27)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=27)
    return Period(current_start, current_end), Period(previous_start, previous_end)


def credentials_from_env() -> Any:
    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("GSC_SERVICE_ACCOUNT_JSON is missing. Add the service-account JSON as a GitHub Actions secret.")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GSC_SERVICE_ACCOUNT_JSON is not valid JSON: {exc.msg}") from exc
    try:
        from google.oauth2 import service_account
    except ImportError as exc:
        raise RuntimeError("Google API dependencies are missing. Install scripts/seo/requirements.txt.") from exc
    try:
        return service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
    except Exception as exc:
        raise RuntimeError(f"Could not initialise Search Console credentials: {exc}") from exc


def service_from_env() -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Google API dependencies are missing. Install scripts/seo/requirements.txt.") from exc
    return build("searchconsole", "v1", credentials=credentials_from_env(), cache_discovery=False)


def fetch_rows(service: Any, site_url: str, period: Period, dimensions: list[str], row_limit: int = 25000) -> list[dict[str, Any]]:
    body = {
        "startDate": period.start.isoformat(),
        "endDate": period.end.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "dataState": "final",
    }
    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    except Exception as exc:
        raise RuntimeError(
            f"Search Console API request failed for {site_url!r}. Confirm GSC_SITE_URL exactly matches the property "
            f"(for example sc-domain:probatehomebuyer.co.uk) and that the service account has Full or Restricted access. Details: {exc}"
        ) from exc
    return response.get("rows", [])


def normalise(rows: list[dict[str, Any]], dimensions: list[str]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        entry = {name: value for name, value in zip(dimensions, row.get("keys", []))}
        entry.update({key: float(row.get(key, 0)) for key in ("clicks", "impressions", "ctr", "position")})
        result.append(entry)
    return result


def aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    clicks = sum(row["clicks"] for row in rows)
    impressions = sum(row["impressions"] for row in rows)
    ctr = clicks / impressions if impressions else 0.0
    weighted_position = sum(row["position"] * row["impressions"] for row in rows)
    position = weighted_position / impressions if impressions else 0.0
    return {"clicks": clicks, "impressions": impressions, "ctr": ctr, "position": position}


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0: return None
    return ((current - previous) / previous) * 100


def fmt_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:+.1f}%"


def keyed(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows}


def terms(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token not in STOPWORDS and len(token) > 2}


def intent(query: str) -> str:
    q = query.lower()
    if any(term in q for term in EXCLUDED_TERMS): return "excluded/non-seller"
    if any(term in q for term in COMMERCIAL_TERMS): return "commercial seller"
    if any(term in q for term in ("executor", "administrator", "beneficiary", "probate", "inherited")):
        return "informational probate"
    return "general informational"


def best_content_match(query: str, inventory: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    query_terms = terms(query)
    if not query_terms: return None, 0.0
    best, score = None, 0.0
    for page in inventory:
        haystack = " ".join((page.get("title", ""), page.get("description", ""), " ".join(page.get("h1s", [])), page.get("intent", "")))
        page_terms = terms(haystack)
        overlap = len(query_terms & page_terms) / len(query_terms)
        if overlap > score:
            best, score = page, overlap
    return best, score


def opportunity_rows(current: list[dict[str, Any]], previous: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previous_by_query = keyed(previous, "query")
    opportunities = []
    for row in current:
        query = row["query"]
        category = intent(query)
        if category == "excluded/non-seller" or row["impressions"] < 20: continue
        old = previous_by_query.get(query, {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0})
        match, overlap = best_content_match(query, inventory)
        reasons = []
        if row["impressions"] >= 50 and row["ctr"] < 0.03: reasons.append("high impressions / low CTR")
        if 5 <= row["position"] <= 20: reasons.append("ranking position 5–20")
        if 20 < row["position"] <= 40 and category == "commercial seller": reasons.append("commercial query at position 20–40")
        if row["impressions"] > old["impressions"] * 1.25 and row["impressions"] - old["impressions"] >= 10: reasons.append("growing query")
        if not reasons: continue
        action = "improve existing page" if match and overlap >= 0.55 else "consider new content after manual overlap review"
        priority = row["impressions"] * (1.2 if category == "commercial seller" else 1.0) / max(row["position"], 1)
        opportunities.append({
            **row, "intent": category, "reasons": ", ".join(reasons), "match": match, "overlap": overlap,
            "action": action, "priority": priority, "impression_change": row["impressions"] - old["impressions"],
        })
    return sorted(opportunities, key=lambda item: item["priority"], reverse=True)


def page_losses(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_map, previous_map = keyed(current, "page"), keyed(previous, "page")
    losses = []
    for page, old in previous_map.items():
        now = current_map.get(page, {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0})
        click_change, impression_change = now["clicks"] - old["clicks"], now["impressions"] - old["impressions"]
        if click_change < 0 or impression_change <= -20:
            losses.append({"page": page, "click_change": click_change, "impression_change": impression_change, **now})
    return sorted(losses, key=lambda item: (item["click_change"], item["impression_change"]))


def primary_recommendation(opportunities: list[dict[str, Any]], losses: list[dict[str, Any]]) -> tuple[str, str]:
    if losses and (not opportunities or losses[0]["click_change"] <= -5):
        return "Improve an existing page", f"Review visibility losses on {losses[0]['page']} before creating another URL."
    if opportunities:
        top = opportunities[0]
        match = top.get("match")
        if match and top["overlap"] >= 0.55:
            return "Improve an existing article or service page", f"Strengthen {match['url']} for the query “{top['query']}”."
        return "Create a new article", f"Investigate “{top['query']}” after a human confirms it does not overlap existing content."
    return "Take no content action this week", "No sufficiently strong, relevant Search Console opportunity passed the thresholds."


def internal_link_suggestions(opportunities: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    suggestions: list[tuple[str, str, str]] = []
    for opportunity in opportunities[:10]:
        target = opportunity.get("match")
        if not target or opportunity["overlap"] < 0.55: continue
        target_url, query_terms = target["url"], terms(opportunity["query"])
        candidates = []
        for page in inventory:
            if page["url"] == target_url or target_url in page.get("internal_links", []): continue
            source_terms = terms(f"{page.get('title','')} {page.get('description','')} {' '.join(page.get('h1s', []))}")
            score = len(query_terms & source_terms)
            if score: candidates.append((score, page["url"]))
        for _, source in sorted(candidates, reverse=True)[:2]:
            item = (source, target_url, opportunity["query"])
            if item not in suggestions: suggestions.append(item)
    return suggestions[:8]


def report_markdown(site_url: str, current_period: Period, previous_period: Period, datasets: dict[str, list[dict[str, Any]]], inventory: list[dict[str, Any]]) -> str:
    current_total, previous_total = aggregate(datasets["totals_current"]), aggregate(datasets["totals_previous"])
    opportunities = opportunity_rows(datasets["queries_current"], datasets["queries_previous"], inventory)
    losses = page_losses(datasets["pages_current"], datasets["pages_previous"])
    recommendation, rationale = primary_recommendation(opportunities, losses)
    best_pages = sorted(datasets["pages_current"], key=lambda row: row["clicks"], reverse=True)[:5]
    device_rows = sorted(datasets["devices_current"], key=lambda row: row["clicks"], reverse=True)
    lines = [
        "# Weekly SEO opportunity report", "", f"**Search Console property:** `{site_url}`  ",
        f"**Current period:** {current_period.label()} (latest three days excluded)  ",
        f"**Comparison period:** {previous_period.label()}", "", "## Primary recommendation", "",
        f"**{recommendation}.** {rationale}", "", "## Executive summary", "",
        "| Metric | Current | Previous | Change |", "|---|---:|---:|---:|",
        f"| Clicks | {current_total['clicks']:.0f} | {previous_total['clicks']:.0f} | {fmt_pct(pct_change(current_total['clicks'], previous_total['clicks']))} |",
        f"| Impressions | {current_total['impressions']:.0f} | {previous_total['impressions']:.0f} | {fmt_pct(pct_change(current_total['impressions'], previous_total['impressions']))} |",
        f"| Average CTR | {current_total['ctr']:.2%} | {previous_total['ctr']:.2%} | {(current_total['ctr']-previous_total['ctr'])*100:+.2f} pp |",
        f"| Average position | {current_total['position']:.1f} | {previous_total['position']:.1f} | {current_total['position']-previous_total['position']:+.1f} |",
        "", "Lower average-position values are better.", "", "### Best-performing pages", "",
        "| Page | Clicks | Impressions | CTR | Position |", "|---|---:|---:|---:|---:|",
    ]
    lines.extend(f"| {row['page']} | {row['clicks']:.0f} | {row['impressions']:.0f} | {row['ctr']:.1%} | {row['position']:.1f} |" for row in best_pages)
    lines.extend(["", "### Pages losing visibility", "", "| Page | Click change | Impression change | Current position |", "|---|---:|---:|---:|"])
    lines.extend(f"| {row['page']} | {row['click_change']:+.0f} | {row['impression_change']:+.0f} | {row['position']:.1f} |" for row in losses[:10])
    if not losses: lines.append("| — | 0 | 0 | — |")
    lines.extend(["", "## Priority opportunities", "", "Commercial seller intent is prioritised. Searches suggesting buyers, investors, solicitors, jobs or unrelated research are excluded.", "", "| Query | Intent | Clicks | Impressions | CTR | Position | Why | Existing-content decision |", "|---|---|---:|---:|---:|---:|---|---|"])
    for row in opportunities[:15]:
        match = row.get("match")
        decision = f"Improve `{match['url']}` ({row['overlap']:.0%} term overlap)" if match and row["overlap"] >= 0.55 else "Manual overlap review before any new URL"
        lines.append(f"| {row['query']} | {row['intent']} | {row['clicks']:.0f} | {row['impressions']:.0f} | {row['ctr']:.1%} | {row['position']:.1f} | {row['reasons']} | {decision} |")
    if not opportunities: lines.append("| — | — | 0 | 0 | — | — | No qualifying opportunity | Take no content action |")
    lines.extend(["", "### Title and meta-description candidates", "", "| Existing page | Trigger query | Current title | Current meta description |", "|---|---|---|---|"])
    metadata_rows = []
    for row in opportunities:
        match = row.get("match")
        if match and row["overlap"] >= 0.55 and "low CTR" in row["reasons"]:
            metadata_rows.append((match, row["query"]))
    seen_urls = set()
    for match, query in metadata_rows:
        if match["url"] in seen_urls: continue
        seen_urls.add(match["url"])
        safe_title = match.get("title", "").replace("|", "\\|")
        safe_description = match.get("description", "").replace("|", "\\|")
        lines.append(f"| `{match['url']}` | {query} | {safe_title} | {safe_description} |")
    if not seen_urls: lines.append("| — | — | No qualifying low-CTR match | — |")
    lines.extend(["", "Review these manually; the workflow does not rewrite metadata.", "", "### Internal-linking opportunities", "", "| Potential source | Target page | Search topic |", "|---|---|---|"])
    link_suggestions = internal_link_suggestions(opportunities, inventory)
    lines.extend(f"| `{source}` | `{target}` | {query} |" for source, target, query in link_suggestions)
    if not link_suggestions: lines.append("| — | — | No sufficiently relevant missing link identified |")
    lines.extend(["", "Add a link only where it genuinely helps the reader; do not create sitewide or keyword-stuffed links.", "", "A proposed new topic must pass the content-inventory overlap check and human review."])
    lines.extend(["", "### Device breakdown", "", "| Device | Clicks | Impressions | CTR | Position |", "|---|---:|---:|---:|---:|"])
    lines.extend(f"| {row['device']} | {row['clicks']:.0f} | {row['impressions']:.0f} | {row['ctr']:.1%} | {row['position']:.1f} |" for row in device_rows)
    lines.extend(["", "## Safeguards", "", "- This report does not edit, publish or merge website content.", "- Search Console rows are retained only as a workflow artifact under the configured retention period.", "- Any content recommendation requires human review and a separate pull request.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("seo-output"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    site_url = os.environ.get("GSC_SITE_URL", "").strip()
    if not site_url:
        print("ERROR: GSC_SITE_URL is missing. Use the exact property value, for example sc-domain:probatehomebuyer.co.uk.", file=sys.stderr)
        return 2
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        service = service_from_env()
        current, previous = complete_periods(args.today)
        datasets = {}
        for name, dimensions, period in (
            ("totals_current", [], current), ("totals_previous", [], previous),
            ("queries_current", ["query"], current), ("queries_previous", ["query"], previous),
            ("pages_current", ["page"], current), ("pages_previous", ["page"], previous),
            ("devices_current", ["device"], current), ("devices_previous", ["device"], previous),
        ):
            datasets[name] = normalise(fetch_rows(service, site_url, period, dimensions), dimensions)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        report = report_markdown(site_url, current, previous, datasets, inventory)
        (args.output_dir / "weekly-seo-report.md").write_text(report, encoding="utf-8")
        (args.output_dir / "raw-search-console.json").write_text(json.dumps({"periods": {"current": current.label(), "previous": previous.label()}, "datasets": datasets}, indent=2), encoding="utf-8")
        print(f"Created weekly report for {current.label()}")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
