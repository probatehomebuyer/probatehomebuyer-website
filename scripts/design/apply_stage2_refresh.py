"""Apply the approved Stage 2 presentation hooks to duplicated static pages.

The site intentionally remains static. This script makes only mechanical,
SEO-neutral changes: shared body hooks, the optimised logo, versioned CSS,
complete mobile navigation and clearer footer labels.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", "docs", "node_modules"}


def page_kind(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel in {"index.html"}:
        return "stage2-home"
    if rel.startswith("areas-we-buy-in/") and rel not in {
        "areas-we-buy-in/index.html",
        "areas-we-buy-in.html",
    }:
        return "stage2-location"
    if rel.startswith("blog/") and rel not in {"blog/index.html", "blog.html"}:
        return "stage2-article"
    if rel.startswith("probate-guide/") and rel not in {
        "probate-guide/index.html",
        "probate-guide.html",
    }:
        return "stage2-article"
    if rel in {
        "blog.html", "blog/index.html", "probate-guide.html",
        "probate-guide/index.html", "areas-we-buy-in.html",
        "areas-we-buy-in/index.html", "probate-faqs/index.html",
    }:
        return "stage2-hub"
    if rel in {
        "contact.html", "contact/index.html", "free-probate-property-offer.html",
        "free-probate-property-offer/index.html", "thank-you.html",
        "thank-you/index.html",
    }:
        return "stage2-form"
    if rel in {
        "privacy-policy.html", "privacy-policy/index.html", "cookie-policy.html",
        "cookie-policy/index.html", "terms.html", "terms/index.html",
        "404.html",
    }:
        return "stage2-legal"
    return "stage2-service"


def add_body_classes(text: str, kind: str) -> str:
    match = re.search(r"<body(?: class=\"([^\"]*)\")?>", text)
    if not match:
        return text
    classes = (match.group(1) or "").split()
    for name in ("stage1-page", "stage2-page", kind):
        if name not in classes:
            classes.append(name)
    return text[: match.start()] + f'<body class="{" ".join(classes)}">' + text[match.end() :]


def update(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original
    text = re.sub(r'href="/style\.css(?:\?[^\"]*)?"', 'href="/style.css?v=20260803-stage2"', text)
    text = add_body_classes(text, page_kind(path))
    text = re.sub(
        r'<img alt="Probate Home Buyer" class="logo-img"(?: height="517")? src="/(?:logo\.png|logo-stage1\.webp)"(?: width="629")?/>',
        '<img alt="Probate Home Buyer" class="logo-img" height="517" src="/logo-stage1.webp" width="629"/>',
        text,
    )
    text = text.replace(
        '<a class="call" href="tel:02071128874">Call 0207 112 8874</a>',
        '<a class="mobile-offer-link" href="/free-probate-property-offer/">Get an offer</a><a class="call" href="tel:02071128874">Call 0207 112 8874</a>',
    )
    text = text.replace(
        '<div class="footer-brand">\n<strong>Probate Home Buyer</strong>',
        '<div class="footer-brand">\n<h3 class="company-details-title">Company details</h3>\n<strong>Probate Home Buyer</strong>',
    )
    text = text.replace(
        '<nav aria-label="Company links" class="footer-column">\n<h3>Company</h3>',
        '<nav aria-label="Explore website links" class="footer-column">\n<h3>Explore</h3>',
    )
    if text != original:
        path.write_text(text, encoding="utf-8", newline="")
        return True
    return False


def main() -> None:
    changed = []
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if update(path):
            changed.append(path.relative_to(ROOT).as_posix())
    print(f"Updated {len(changed)} public HTML files")
    for name in changed:
        print(name)


if __name__ == "__main__":
    main()
