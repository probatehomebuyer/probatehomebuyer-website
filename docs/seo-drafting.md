# Phase 2: human-approved SEO drafting design

Phase 2 is intentionally documented but not enabled. The current repository has no approved external AI API credential, and a reliable drafting system must not pretend that a ChatGPT subscription is an API integration.

## Safe proposed process

1. The weekly report selects one primary opportunity.
2. A human confirms whether the action should be a new article, an existing-page improvement, internal links, metadata or no action.
3. A manually dispatched drafting workflow receives the approved issue number, target URL and action type.
4. It creates a new `agent/seo-...` branch from the latest `main`.
5. It prepares only the approved change and runs `scripts/seo/site_audit.py`.
6. It opens a draft pull request.
7. A human reviews accuracy, legal phrasing, originality, links, dates, structured data and the complete diff.
8. Only a human may merge. Cloudflare Pages may publish after a merge to `main`.

The future workflow must have `contents: write` and `pull-requests: write`, but no ability to approve or merge pull requests. Branch protection should require review and prevent direct pushes to `main`.

## AI API requirements

A ChatGPT Plus subscription does **not** include OpenAI API usage or API credits. If OpenAI API drafting is later approved, create a separate API project and key, store it only in a GitHub Actions secret named `OPENAI_API_KEY`, set a project budget/usage alert, and restrict access to trusted repository maintainers.

API use is billed separately according to model and token usage. Cost depends on article length, context size, retries and the chosen model. The workflow should enforce a per-run token limit and process only one approved opportunity at a time.

To disable AI drafting, disable its workflow or remove `OPENAI_API_KEY`. Phase 1 remains fully operational in report-only mode without any AI API.

## Required drafting controls

Before opening a pull request, a future implementation must:

- load `seo-output/content-inventory.json` and reject high-overlap new topics;
- use British English and serve executors, administrators and beneficiaries;
- exclude property-buyer, investor, solicitor, employment and unrelated intent;
- distinguish general information from legal advice and avoid unsupported guarantees;
- preserve the verification meta tag, analytics, form actions, GDPR wording, canonical and trailing-slash conventions, navigation, branding and mobile flow;
- avoid generic filler, keyword stuffing and copied competitor wording;
- include natural service-page links and a relevant call to action;
- run the static SEO audit and link checks;
- show every changed file in an unmerged draft pull request.

For a new article it must create `blog/<slug>/index.html`, add a card to `blog/index.html` in strict reverse chronological order, update `sitemap.xml`, add only necessary `_redirects` rules and add useful internal links. Visible dates must say only `Posted`; `dateModified` may exist only in JSON-LD. No article should be generated merely because another website covers the topic.

## Report-only mode

Report-only mode is the default and current state. It requires only Search Console credentials. A person can use the weekly report to prepare changes locally without connecting any AI service.
