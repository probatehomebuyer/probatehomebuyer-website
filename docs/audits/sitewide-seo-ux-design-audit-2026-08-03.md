# Probate Home Buyer: sitewide SEO, UX and design audit

Date: 3 August 2026  
Scope: 51 canonical public pages, current repository, live representative pages and Search Console periods 4–31 July 2026 versus 6 June–3 July 2026.  
Safeguard: this is an audit only. No live page, URL, form, redirect, tracking code or design component is changed.

## Executive view

The site has a sound specialist proposition, clear navy-and-gold identity and a strong postcode-first homepage. Its best near-term growth route is not a large redesign or rapid article production. It is to strengthen a small number of pages already earning impressions, clarify the information-versus-commercial architecture, improve internal journeys and reduce template repetition.

The largest risks are thin overlapping probate-guide pages, highly similar location pages, inconsistent metadata and structured data, and visual repetition that makes important reassurance feel generic. The largest opportunities are the empty-house article, commercial probate-sale intent, the service-page pathway and selective location pages with real evidence.

## Priorities

### P0 — protect and measure

1. Preserve every URL, canonical, redirect, GA4 tag, Search Console verification token, form action and legal page during later work.
2. Extend the weekly report to retain query-to-page evidence and monitor the updated needs-work article for at least two complete reporting periods.
3. Resolve slash/non-slash reporting fragmentation by verifying redirects return one hop to the trailing-slash canonical. Search Console currently reports both variants for some pages.
4. Define one page owner for each search intent before editing content. Do not create another article until the map is approved.

### P1 — highest SEO and conversion return

1. Improve `/blog/empty-house-during-probate/`: 370 impressions, zero clicks, average position 24.0. Rework its title/snippet, satisfy insurance/security/council-tax intent earlier and strengthen the natural route to an appraisal.
2. Strengthen `/sell-inherited-house/`: 69 impressions, zero clicks, average position 52.8. Make it the definitive commercial page for selling an inherited house, while guides explain process and articles answer narrow questions.
3. Make `/probate-guide/selling-a-house-in-probate/` the authoritative process guide. Fold or differentiate overlapping “before probate” material rather than letting the guide, article and FAQ compete.
4. Improve homepage relevance for genuine probate-sale searches through body copy and internal links before changing its title. The homepage had 991 impressions and two clicks, but disclosed query-page data was mostly broad or irrelevant and incomplete because of Search Console privacy thresholds.
5. Add contextual calls to action based on reader state: “secure an empty house”, “compare sale routes”, “get a condition-based offer” and “ask a probate timing question”. Avoid repeating the same generic offer block.

### P2 — architecture and quality

1. Consolidate or substantially deepen the seven short probate-guide detail pages (roughly 309–325 visible words including shared chrome). Several descriptions are only 55–83 characters and the audit finds two possible orphans.
2. Rebuild location-page content standards. Pairwise vocabulary similarity reaches 80–86%, which risks doorway-like presentation. Keep only places supported by genuine service coverage and add local market context, transaction evidence, logistics and non-boilerplate FAQs.
3. Standardise structured data by template: `Organization`/`LocalBusiness` at site level, `Service` on commercial pages, `BlogPosting` on articles, `FAQPage` only where visible FAQs qualify, and `BreadcrumbList` consistently.
4. Create reusable source components or a safe build step for header, navigation, footer, trust evidence, CTA and metadata. The current duplicated HTML makes drift likely.

### P3 — design evolution

1. Reduce the number of cream panels, trust strips and repeated link blocks. One strong proof section is more credible than repeated generic reassurance.
2. Establish page-family layouts: commercial service, editorial article, reference guide, location and conversion form.
3. Improve typography with a restrained display/body scale, shorter measures for editorial text and consistent heading rhythm.
4. Use real transaction/property imagery selectively. Avoid decorative stock imagery and avoid adding icons where a heading and sentence communicate more clearly.

## Search performance findings

| Opportunity | Current evidence | Recommended owner | Action |
|---|---:|---|---|
| Inherited house needs work | 165 impressions, position 7.8, no clicks for exact query | Updated needs-work article | Monitor the merged title/content before further change |
| Empty house during probate | 370 page impressions, position 24.0, no clicks | Empty-house article | Improve snippet and answer insurance/security/holding-cost questions earlier |
| Sell probate property | 46 query impressions, position 13.2, no clicks | Homepage plus selling-in-probate guide | Clarify hierarchy and link to the definitive process guide |
| Reputable as-is probate buyer | 72 query impressions, position 10.5, no clicks | Needing-work service page | Add transparent buyer-selection and offer-checking proof |
| Sell house quickly probate | 14 impressions, position 12.0 | Homepage/service pages | Support carefully without unverifiable speed promises |
| As-is/renovation variants | Positions 7.4–10.5 | Needs-work article and service page | Keep informational and transactional roles distinct |
| Essex/Kent local intent | Small samples around positions 5.3–5.4 | Relevant location pages | Improve only with genuine local evidence; do not extrapolate from tiny samples |

Pages between positions 5 and 30 with meaningful evidence include the homepage, needs-work article, empty-house article, no-clearance article, executor checklist, needing-work service, blog index, case studies and selected location pages. Low-volume rows should be treated directionally, not as proof.

## Cannibalisation and content quality

- “Before probate” appears in `/blog/can-executors-sell-before-probate/`, `/probate-guide/can-you-sell-before-probate/`, the FAQ hub and the selling-in-probate guide. Assign the full procedural explanation to the guide and use the article only if it serves a distinct executor question.
- Empty-property intent is split across `/blog/empty-house-during-probate/` and `/probate-guide/empty-inherited-property/`. The article should own the comprehensive informational query; the guide page should become a concise task checklist or be consolidated.
- Clearance intent appears in the clearance guide and no-clearance article. Keep the guide about responsible clearance steps and the article about sale-route feasibility.
- The needs-work article and service page now have a healthy split: balanced comparison versus commercial direct-offer route.
- `/probate-faqs/` should summarise and link, not reproduce full answers already owned by guides.
- Missing commercially useful subjects are not necessarily new articles: seller due diligence, how an offer is calculated, evidence of funds, fees/deductions, complaint process and a transparent direct-buyer comparison belong first on service/trust pages.

## Internal linking

Quick wins:

- Add contextual links to the two possible orphan guides: `/probate-guide/what-is-probate/` and `/probate-guide/how-long-does-probate-take/`, or consolidate them if they cannot earn a distinct role.
- Link the empty-house article to the insurance/security checklist, holding-cost explanation and the most relevant service route.
- Link case studies from service and location pages by matching circumstance or area, not from generic repeated blocks.
- On informational pages, introduce one useful next step mid-article and one end-of-article choice. Do not add sitewide exact-match links.
- Use descriptive but varied anchors; reserve primary exact-match language for the page that owns the intent.

## User journey and conversion

What works:

- The homepage immediately states the service and presents a postcode field above the fold.
- Mobile has no horizontal overflow at a 390px test viewport.
- Phone, offer route, company identity and direct-buyer disclosure are visible.

What weakens the journey:

- The desktop navigation has nine primary items plus the phone action, creating scanning load.
- The mobile hero is clear, but the cookie banner occupies a large part of the first two viewports and competes with the offer journey.
- Many pages repeat trust strips and generic CTAs, making them feel like template furniture rather than evidence.
- Articles jump quickly from advice to “get an offer” without always matching the reader’s stage.
- Trust depends heavily on claims. Stronger proof would include named process standards, evidence-of-funds explanation, solicitor workflow, review provenance and richer anonymised transactions.
- The postcode-first step is low friction, but users should see what happens next, what data is required and that submission is not an acceptance or valuation.

## Design and presentation

The navy (`#102f4a`/`#0a2238`) and gold (`#d4a64f`) palette is distinctive and should remain. The current homepage hero is confident, but very heavy display typography, large rounded cards and repeated cream/navy panels make page families feel similar.

Recommended design system:

- **Type:** one confident display face or existing bold system treatment for H1/H2; Inter/system sans for body; editorial measure 68–74 characters.
- **Scale:** 56/60 desktop H1, 38/42 mobile H1, 40/46 H2, 28/34 H3, 18/30 lead, 16/27 body.
- **Spacing:** 8px base; section bands of 72–96px desktop and 48–64px mobile.
- **Colour roles:** navy for authority, warm white for reading, gold for primary action, muted blue-grey for supporting text; keep cyan as a limited informational accent.
- **Components:** compact header, postcode module, proof bar, process timeline, comparison table, editorial callout, case-evidence card, FAQ accordion, contextual CTA and restrained footer.
- **Page families:** homepage; service; article; guide/hub; location; form. Each gets a distinct content rhythm while sharing tokens.
- **Motion:** none required beyond accessible hover/focus states and optional accordion disclosure.

## Technical architecture

- Header, mobile menu, footer, WhatsApp button, analytics and metadata are copied across static files. This creates high maintenance and consistency risk.
- Introduce a conservative static build layer (for example, data plus templates rendered to the existing paths). Commit generated HTML so hosting remains static and rollback remains simple.
- Create page data for title, description, canonical, H1, schema, breadcrumbs and related links. Validate uniqueness and trailing-slash rules in CI.
- Preserve all existing output URLs and `_redirects`. Do not change form endpoints, field names, analytics IDs or verification meta.
- Image use is light, which helps speed, but audit dimensions, compression and preload priority for hero assets. Add explicit width/height to prevent layout shift where missing.
- Accessibility work: visible keyboard focus, skip link, menu semantics, input labels, colour contrast, 44px touch targets and reduced-motion compatibility.
- The current audit reports zero technical errors. Existing warnings: offer page absent from the sitemap and two possible orphan guide pages.

## Competitor observations

- [GoodMove](https://www.goodmove.co.uk/) leads with national coverage and regulatory/trade trust, then a three-step process and clear comparisons.
- [We Buy Any House](https://www.webuyanyhouse.co.uk/) uses a strong immediate promise, condition/coverage reassurance and situation-led journeys including inherited property.
- [House Buyer Bureau](https://www.housebuyerbureau.co.uk/) makes postcode entry and a three-step explanation central to the first viewport.
- [Eddisons’ probate auction guide](https://www.eddisons.com/insights/selling-probate-property-at-auction) separates benefits, authority, process and timing cleanly.
- [Property Saviour’s probate guide](https://propertysaviour.co.uk/how-to-sell-probate-property/) covers route comparison and executor questions, but Probate Home Buyer should retain its calmer, more balanced voice.

The proposed direction borrows no wording or visual treatment. Its differentiator is specialist probate understanding, evidence-led transparency and a calmer executor-first experience.

## Quick wins

1. Improve descriptions on the seven probate-guide detail pages.
2. Add or consolidate links for the two possible orphan guides.
3. Add the offer page to the sitemap if it is intended to rank; otherwise document why it is excluded.
4. Audit slash redirects for Search Console URL fragmentation.
5. Improve empty-house article snippet and opening.
6. Reduce primary navigation to grouped “Sell”, “Probate help”, “Areas”, “About” and “Contact”.
7. Reduce cookie-banner mobile height while retaining consent clarity.
8. Replace generic repeated trust strips with one evidence-led proof module per journey.

## Deeper improvements

1. Rebuild the guide/article architecture around assigned search intents.
2. Introduce reusable static templates without changing generated URLs.
3. Rework location pages from boilerplate to evidence-led local landing pages, or reduce the set.
4. Create a coherent proof system: process standards, review source, real anonymised transactions and transparent offer terms.
5. Apply the proposed page-family design system after the standalone direction is approved.

## Recommended sequence

1. Approve the page map and visual direction.
2. Make measurement, redirect, sitemap and schema fixes in one low-risk technical PR.
3. Improve the empty-house article and commercial inherited-house page in separate evidence-led PRs.
4. Pilot reusable templates on one article and one service page without changing their URLs.
5. Test the location-page standard on one strong location before broader rollout.

