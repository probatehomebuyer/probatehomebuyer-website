# SEO report storage

Weekly reports and raw Search Console exports are not committed here. The workflow:

- uploads the full output as a private GitHub Actions artifact retained for 35 days;
- places the concise report in the workflow summary; and
- creates or updates one rolling GitHub issue titled **Weekly SEO opportunity report**.

This prevents operational data and an indefinite report history from cluttering the public website repository.
