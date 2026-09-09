# Codecool Tender Watcher (cloud-based, GitHub Actions)

A weekly automation that searches the web for funding calls, grants, public
procurements and tenders relevant to Codecool (EU + Hungarian sources + EU
corporate procurement pages, e.g. Finnish ones), then notifies via e-mail and/or
Slack and also presents the results on a web dashboard.

You do not have to configure the websites to monitor – based on the company
profile and the source portals the model searches on its own, and also
specifically discovers corporate pages.

The AI call goes through **OpenRouter**, using an Anthropic Claude model. The web
search is performed by OpenRouter's `openrouter:web_search` server tool.

## What's in here

```
tender_watcher.py           # the weekly run logic
config.py                   # company profile + source list + model/settings
requirements.txt            # Python dependencies
.github/workflows/tender-watcher.yml   # weekly schedule (Monday 06:00 UTC = 08:00 Budapest)
docs/index.html             # dashboard (GitHub Pages)
docs/data.json              # the dashboard data (refreshed on every run)
docs/archive.json           # cumulative archive of every item ever found
state/seen.json             # deduplication (what we have already seen) – refreshed on every run
digests/                    # weekly digest .md files
```

Note: the model prompt (`config.py` → `COMPANY_PROFILE`, `SEARCH_SEGMENTS`, and
`build_prompt()` in `tender_watcher.py`) is intentionally written in Hungarian,
since the target market and the search terms are largely Hungarian. Everything
else – code, comments, dashboard, digests – is in English.

## Setup, step by step

### 1. Create the repository
Push this folder to a (private) GitHub repository.

### 2. Add the secrets
GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.

Required:

| Secret name | Value |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key (openrouter.ai/keys) |

For Slack notifications:

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL (api.slack.com/messaging/webhooks) |

For e-mail notifications (e.g. a Gmail app password or a corporate SMTP server):

| Secret name | Example |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `tenders@codecool.com` |
| `SMTP_PASS` | app password / SMTP password |
| `EMAIL_FROM` | `tenders@codecool.com` |
| `EMAIL_TO` | `owner1@codecool.com, owner2@codecool.com` |

Both e-mail and Slack are optional: whichever has no secret configured is
skipped by the script.

### 3. Enable GitHub Pages (dashboard)
Repo → **Settings → Pages** → *Source: Deploy from a branch* → branch `main`,
folder `/docs`. The dashboard will then be available at
`https://<org-or-user>.github.io/tender-watcher/`.

### 4. First run, manually
Repo → **Actions → Tender Watcher → Run workflow**.
This runs the search, populates `docs/data.json`, writes a digest and sends out
the notifications.

After that it runs by itself every **Monday morning**.

## Customization

- **Focus / keywords / target countries:** `config.py` → `COMPANY_PROFILE`.
- **Monitored sources:** `config.py` → `SEARCH_SEGMENTS` (extendable; corporate
  page discovery works without it too).
- **Schedule:** `.github/workflows/tender-watcher.yml` → `cron`. The cron is in UTC!
  Monday 08:00 Budapest ≈ `0 6 * * 1` (summer time). For a daily run: `0 6 * * *`.
- **What gets reported in notifications:** `config.py` → `MIN_RELEVANCE`
  (`high` = only the best ones).
- **Model:** `config.py` → `MODEL`. An OpenRouter slug; Anthropic models need the
  `anthropic/` prefix (e.g. `anthropic/claude-sonnet-5`, or
  `anthropic/claude-opus-4.5` for something stronger).
- **Web search / cost:** `config.py` → `MAX_RESULTS_PER_SEARCH`, `MAX_TOTAL_RESULTS`.

## Cost
The fee is charged against the OpenRouter balance: the model's token cost plus
the web search (Exa engine, roughly $4 / 1000 results, i.e. at most ~$0.02 per
search with the default settings). Typically a few hundred forints per run.
GitHub Actions and Pages are free at this level of usage.

## Limitations, honestly
- Coverage of the official portals is reliable; corporate page discovery is
  "best effort", not exhaustive.
- The model can be wrong (deadline, eligibility) – always verify a result via the
  official link.
- This is an initial version: before relying on it, it is worth reviewing one or
  two runs with human eyes.
