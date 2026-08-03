# Weekly SEO and competitor-research system

## What the system does

Every Monday the `Weekly SEO opportunity report` GitHub Actions workflow:

1. inventories every canonical HTML page in the repository;
2. runs a non-destructive technical SEO audit;
3. downloads the latest complete 28 days of Google Search Console performance data;
4. compares it with the preceding 28 days;
5. separates commercial seller intent from general informational searches and excludes obvious buyer, investor, solicitor, employment and unrelated traffic;
6. checks opportunities against the existing content inventory;
7. optionally reviews public competitor sitemap metadata when competitor domains are configured;
8. selects one primary recommendation rather than forcing a new article;
9. uploads the detailed data as a short-retention Actions artifact;
10. updates one rolling GitHub issue and writes the main report to the workflow summary.

It never edits website pages, commits changes, opens content pull requests, merges branches or publishes the website.

## Schedule and British daylight-saving time

GitHub Actions schedules use UTC and do not support an IANA timezone. The workflow runs at `07:30 UTC` every Monday.

- During British Summer Time (BST, UTC+1), that is **08:30 UK time**.
- During Greenwich Mean Time (GMT, UTC), that is **07:30 UK time**.

This intentionally meets the requested 08:30 time during BST. To use 08:30 during winter instead, change the cron expression to `30 8 * * 1` after the clocks change. GitHub may start scheduled workflows a few minutes late during periods of high load.

## Required GitHub secrets

Open the repository on GitHub and select **Settings → Secrets and variables → Actions → New repository secret**.

Add:

| Secret | Value |
|---|---|
| `GSC_SERVICE_ACCOUNT_JSON` | The complete downloaded Google service-account JSON object. Paste it as one secret; never add the file to Git. |
| `GSC_SITE_URL` | The exact Search Console property identifier. For the domain property use `sc-domain:probatehomebuyer.co.uk`. |

The script fails with a clear error if either value is absent, invalid or lacks Search Console access. Secret values are not printed or included in artifacts.

### Optional competitor configuration

Under **Settings → Secrets and variables → Actions → Variables**, add `SEO_COMPETITOR_URLS` as a comma-separated list of HTTPS website origins, for example:

```text
https://example-one.co.uk/,https://example-two.co.uk/
```

This is a normal Actions variable because competitor website addresses are not credentials. If it is omitted, competitor research is safely skipped. The scan is deliberately bounded to 100 sitemap URLs per domain, reads only public metadata, does not scrape Google results and does not copy competitor text.

## Google Search Console setup

### 1. Create or select a Google Cloud project

1. Sign in to [Google Cloud Console](https://console.cloud.google.com/).
2. Use the project selector at the top and choose **New project**.
3. Give it a clear name such as `Probate Home Buyer SEO Reporting`.
4. Select the new project.

### 2. Enable the official Search Console API

1. Open **APIs & Services → Library**.
2. Search for **Google Search Console API**.
3. Select it and choose **Enable**.

The workflow uses the official `searchconsole` API with the read-only `webmasters.readonly` scope.

### 3. Create a service account

1. Open **IAM & Admin → Service Accounts**.
2. Choose **Create service account**.
3. Name it `probate-home-buyer-seo-reporting`.
4. No Google Cloud project role is required for this read-only Search Console use; finish creating the account.
5. Open the account, then **Keys → Add key → Create new key → JSON**.
6. Download the JSON once and store it securely.

The private key in that file is a credential. Do not email it, paste it into an issue or commit it.

### 4. Grant Search Console property access

1. Copy the service account's email address, ending in `iam.gserviceaccount.com`.
2. Open [Google Search Console](https://search.google.com/search-console/).
3. Select the exact Probate Home Buyer property.
4. Open **Settings → Users and permissions → Add user**.
5. Add the service-account email. Restricted access is normally sufficient for performance reporting; Full access also works.
6. Set `GSC_SITE_URL` to the exact property identifier. Domain properties use `sc-domain:probatehomebuyer.co.uk`, not the public homepage URL.

### OAuth alternative

The implemented workflow uses a service account because it is stable for unattended, read-only reporting. OAuth would require securely storing and refreshing a user refresh token and is not implemented. Do not substitute an OAuth client JSON for the service-account secret.

## Run a manual test

1. Add the two required secrets.
2. Open the repository's **Actions** tab.
3. Select **Weekly SEO opportunity report**.
4. Choose **Run workflow**, select the feature/default branch containing the workflow and confirm.
5. Open the run and read its summary.
6. Download the `weekly-seo-report-...` artifact if the detailed inventory or raw API rows are needed.
7. Check the repository Issues tab for the rolling **Weekly SEO opportunity report** issue.

The latest three days are excluded. For example, a run on Monday uses data through the preceding Friday and compares two complete 28-day windows.

## Reading the report

The report starts with exactly one primary recommendation:

- Create a new article.
- Improve an existing article or service page.
- Add internal links.
- Fix metadata.
- Fix a technical SEO problem.
- Take no content action that week.

Average position is impression-weighted; a lower number is better. Percentage changes compare the current 28-day period with the immediately preceding 28 days. A new-article recommendation is provisional until a person reviews the inventory and confirms that no existing page serves the same intent.

## Data retention and privacy

- Raw Search Console data is uploaded as an Actions artifact for 35 days.
- Only a concise rolling report is placed in an issue and workflow summary.
- No reports are deployed as public website pages or added to `sitemap.xml`.
- GitHub automatically masks exact secret values in logs, and the scripts never print credentials.
- Search query data may still be commercially sensitive; restrict repository and Actions access appropriately.

## Disable or change the schedule

To pause scheduled reporting without removing the scripts:

1. Open **Actions → Weekly SEO opportunity report**.
2. Use the workflow menu to disable the workflow.

Alternatively, remove or comment out the `schedule` block in `.github/workflows/weekly-seo.yml` in a reviewed pull request. Manual `workflow_dispatch` runs can remain available.

## Rotate or revoke credentials

1. In Google Cloud, open the service account's **Keys** tab.
2. Create a replacement JSON key.
3. replace the `GSC_SERVICE_ACCOUNT_JSON` GitHub secret.
4. Run the workflow manually and confirm it succeeds.
5. Delete the old key in Google Cloud.

To revoke all access, remove the service-account user from Search Console and delete its keys. Also remove the GitHub secret.

## Run locally

Python 3.11 or later is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r scripts\seo\requirements.txt
python scripts\seo\site_audit.py --root . --output-dir seo-output
$env:GSC_SITE_URL = 'sc-domain:probatehomebuyer.co.uk'
$env:GSC_SERVICE_ACCOUNT_JSON = Get-Content -Raw 'C:\secure\service-account.json'
python scripts\seo\gsc_weekly_report.py --inventory seo-output\content-inventory.json --output-dir seo-output
python scripts\seo\competitor_research.py --inventory seo-output\content-inventory.json --output seo-output\competitor-research.md
python scripts\seo\combine_reports.py
```

Do not place the service-account file inside the repository. Clear the environment variable when finished:

```powershell
Remove-Item Env:GSC_SERVICE_ACCOUNT_JSON
```

## Troubleshooting

- **Property not found or permission denied:** confirm the exact `GSC_SITE_URL` format and add the service-account email to that Search Console property.
- **Missing credentials:** confirm the Actions secret names exactly match the documented names.
- **No data:** verify the property has search traffic in the chosen periods. A valid empty response is not a failure.
- **Competitor scan warning:** a website may lack a sitemap, block automated requests or time out. The Search Console report remains usable.
- **Issue step fails:** repository Actions must be allowed to create issues. The workflow requests only `contents: read` and `issues: write`.

## Costs

The Search Console API and Google service account do not normally add a usage charge for this reporting volume. GitHub Actions usage and artifact storage are subject to the repository account's GitHub plan. Competitor scanning uses public web requests and no paid service. Phase 1 does not call an AI API.

## Limitations

- Search Console data is sampled/aggregated according to Google's API behaviour and does not expose every private or very-low-volume query.
- Keyword relevance and content overlap use explainable rules, not legal or editorial judgement.
- Competitor sitemap metadata cannot show rankings, traffic or content quality.
- The workflow recommends actions but does not prove causation.
- Human review remains mandatory before any website change.

See [seo-drafting.md](seo-drafting.md) for the deliberately non-operational Phase 2 design.
