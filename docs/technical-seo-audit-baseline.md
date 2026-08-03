# Technical SEO audit baseline

Audit date: 3 August 2026. Audited source: `main` commit `08e5c3c`, plus the automation files in this pull request.

The static audit inventoried **51 canonical HTML pages**, including:

- all seven existing blog articles;
- eight detailed probate-guide pages and the guide index;
- the FAQ page;
- three core service/conversion pages;
- twenty location pages;
- legal and supporting pages.

## Validation result

- Errors that fail CI: **0**
- Report-only warnings after the low-risk fix: **3**

The checks cover missing or duplicate titles and descriptions, H1 counts, canonical URLs, internal links, local assets, sitemap consistency, accidental `noindex`, image alt text, JSON-LD syntax, visible article date labels, HTTP links, thin content, blog date order, form actions, the protected Search Console verification tag, operational-file exposure and common committed-secret patterns.

## Low-risk fix included

The blog index placed the article dated 31 May 2026 before the article dated 5 June 2026. The two cards have been reordered in `blog/index.html` and its existing root compatibility copy, `blog.html`. No article wording, metadata, design, tracking, form or navigation was changed.

## Remaining warnings

1. `/free-probate-property-offer/` is absent from `sitemap.xml`. The page intentionally uses `noindex, follow`, so it has not been added automatically.
2. `/probate-guide/how-long-does-probate-take/` has no canonical internal link from another inventoried page.
3. `/probate-guide/what-is-probate/` has no canonical internal link from another inventoried page.

The latter two are possible orphan warnings, not proof that an immediate edit is appropriate. They should be reviewed alongside Search Console data before adding contextual links. The audit intentionally does not rewrite pages in bulk.

`/free-probate-property-offer/` and `/thank-you/` are explicit, documented `noindex` exceptions. Any other canonical page acquiring `noindex` fails the automated check.
