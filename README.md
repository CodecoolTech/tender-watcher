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
tender_watcher.py           # the weekly run logic + link quality filter
ted_source.py               # TED notices straight from the official API (not web search)
config.py                   # company profile + monitored sources + filter rules + model/settings
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

## Where the opportunities come from

Two official APIs are queried directly, and the model's web searches cover what
has no API:

| Source | Module | What it adds |
|---|---|---|
| TED | `ted_source.py` | EU-wide procurement above the EU threshold |
| e-Zamówienia (PL) | `ezamowienia_source.py` | Polish procurement, mostly **below** the EU threshold — invisible to TED |
| everything else | web search | grants, corporate RFPs, below-threshold notices elsewhere |

Poland gets its own module because it is a real market for Codecool and
practically every open Polish training notice is below the EU threshold, so TED
never carries it. Measured on 2026-09-18, it added 5 results in one run, 3 of
them graded `high` — regional cybersecurity training for public officials,
citizen digital-literacy workshops, IT security training for government staff.

Two other Polish portals were asked for and **not** built on:

- **Baza Konkurencyjności** — unique content (EU-funded beneficiaries publish
  procurements there that reach no other portal), but every `/api/` endpoint
  answers 401 behind Keycloak and the swagger URL just serves the SPA shell.
  There is no public interface to build on, so it is a web-search entry point.
- **platformazakupowa.pl** — no API, and its `robots.txt` asks for a 900-second
  crawl delay. Its notices also largely reappear in the BZP feed that
  `ezamowienia_source.py` already reads. Web-search entry point as well.

## How TED is covered

TED is **queried, not searched**. `ted_source.py` calls the official TED API
(`api.ted.europa.eu`, no key needed), asks for open notices under the training
CPV codes, and hands the model a ready list; the model only judges which ones
fit Codecool. Its web searches then go to the segments that have no API.

This replaced web search because web search kept missing TED. Measured on
2026-09-16: a run with 16 searches returned **zero** TED results while the API
showed 66 IT-training notices from the previous 21 days, 7 still open – among
them a Hungarian e-learning tender (585619-2026) and a Norwegian developer
security training (599109-2026). After the switch the same day returned **17**
verified open TED tenders.

Candidates are fetched per **service line**, each with its own quota
(`TED_GROUPS`), because training notices outnumber everything else by an order
of magnitude — a single deadline-ordered list would never reach an e-learning
platform tender. Current split of the 40 slots: IT/digital training 22, general
training with digital content 8, educational software / LMS / course material 10.

Three details worth knowing before you touch `config.py`:

- Ranking uses the **notice title**, not the CPV. TED titles read
  `Country – <main CPV label> – <buyer's title>`, and a training CPV such as
  80533100 is routinely bolted onto hardware purchases (medical equipment,
  spectrometers). The middle label is what says the notice is really about
  training. See `TED_TRAINING_TITLE_WORDS`.
- **A CPV group is only worth a quota if it pays for itself.** IT recruitment was
  tried and withdrawn on 2026-09-18: across two live runs its candidates were
  generic HR and staffing work and the model kept none of them, so the slots
  were pure loss. That service line is covered by a web-search segment instead.
  The block is kept commented out in `config.py` with the numbers, so it can go
  back if a later review disagrees.
- **EKR cannot be covered this way.** Its notice pages are a JavaScript app that
  returns an empty shell to any fetch or crawler, which is why the watcher never
  produced a concrete EKR link. Hungarian above-threshold procedures are
  published on TED as well, so they arrive through the API instead.

## What counts as a result

Only a page describing **one concrete opportunity** is reported. Aggregator and
news pages are dropped by the link filter (`tender_watcher.py` →
`reject_reason`), because they only write *about* calls:

| Dropped | Example |
|---|---|
| Grant-consultant / tender-news sites | `palyazatmenedzser.hu/digitalizacios-palyazat/` |
| News / press posts, even on official EU domains | `hadea.ec.europa.eu/news/new-calls-proposals-…` |
| Portal homepages | `ted.europa.eu/hu/` |
| Search / category / listing pages | `tendigo.de/ausschreibungen/weiterbildung` |
| Guides / rulebooks explaining how procurement works | `europa.eu/youreurope/…/public-tendering-rules/` |
| An EU call linked from a secondary source | `ffg.at/en/europe/dep/calls/SO4_2026_2` |

`config.py` lists the sources that were evaluated and deliberately left out –
the Közbeszerzési Értesítő (its `robots.txt` disallows the notice paths), BOAMP,
Bundesanzeiger and the various guide portals – with the reason for each, so the
question does not need re-researching.

The filter runs both on fresh model output and on the stored archive, so a rule
change cleans up the dashboard on the next run. Every dropped link is printed in
the run log with its reason – that log is how you find new offender domains to
add to `AGGREGATOR_DOMAINS`.

To clean the stored files immediately, without a model call (and without cost):

```bash
python tender_watcher.py --prune
```

## Customization

- **Focus / keywords / target countries:** `config.py` → `COMPANY_PROFILE`.
- **Monitored sources:** `config.py` → `MONITORED_SOURCES` – portals that must be
  checked on *every* run (EKR, TED, tendigo Weiterbildung, HADEA Digital Europe
  call announcements). These are entry points, not results: the watcher drills
  down from them to the individual call, and the landing pages themselves are
  rejected by the link filter.
- **Search segments:** `config.py` → `SEARCH_SEGMENTS` (extendable; corporate
  page discovery works without it too).
- **Link filter rules:** `config.py` → `AGGREGATOR_DOMAINS`, `NEWS_PATH_PATTERNS`,
  `LISTING_PATH_KEYWORDS`.
- **Schedule:** `.github/workflows/tender-watcher.yml` → `cron`. The cron is in UTC!
  Monday 08:00 Budapest ≈ `0 6 * * 1` (summer time). For a daily run: `0 6 * * *`.
- **What gets reported in notifications:** `config.py` → `MIN_RELEVANCE`
  (`high` = only the best ones).
- **Model:** `config.py` → `MODEL`. An OpenRouter slug; Anthropic models need the
  `anthropic/` prefix (e.g. `anthropic/claude-sonnet-5`, or
  `anthropic/claude-opus-4.5` for something stronger).
- **Web search / cost:** `config.py` → `MAX_RESULTS_PER_SEARCH`, `MAX_TOTAL_RESULTS`.

## Cost
Charged against the OpenRouter balance. Measured on real runs, **~$0.67 per run**
at the default `MAX_SEARCHES = 12`, i.e. roughly $35 / year on the weekly
schedule. GitHub Actions and Pages are free at this level of usage.

The web search itself is cheap (Exa engine, ~$4 / 1000 results ≈ $0.02 per run);
almost all of the cost is **tokens**, because every search result is pushed into
the model's context. That makes the cost grow faster than the search count:

| `MAX_SEARCHES` | prompt tokens | cost / run |
|---|---|---|
| 12 | 204k | $0.67 |
| 16 | 389k | $1.05 |

A 33% increase in searches cost 57% more and did **not** produce more results –
measure the item count before raising it.

The TED candidate list adds roughly $0.30 to a run (it rides along in the
context of every tool round-trip), taking a run to **~$0.98**. It is worth it:
the same run went from 3–7 usable items to 19. If that matters, the lever to
pull is `MAX_SEARCHES`, not the TED list – TED no longer needs to be searched
for, so fewer searches may now be enough.

## Limitations, honestly
- Coverage of the official portals is reliable; corporate page discovery is
  "best effort", not exhaustive.
- The model can be wrong (deadline, eligibility) – always verify a result via the
  official link.
- This is an initial version: before relying on it, it is worth reviewing one or
  two runs with human eyes.
