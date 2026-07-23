# Codecool Pályázatfigyelő (felhős, GitHub Actions)

Heti automata, ami az interneten releváns pályázatokat, támogatásokat, közbeszerzéseket
és tendereket keres a Codecool számára (EU + magyar források + EU-s cégoldalak, pl. finn),
majd e-mailben és/vagy Slackben értesít, és egy webes dashboardon is megjeleníti a találatokat.

Nem kell felconfigurálni a figyelt honlapokat – a modell a cégprofil és a forrásportálok
alapján magától keres, és célzottan felderít cégoldalakat is.

Az AI-hívás **OpenRouteren** keresztül megy, Anthropic
Claude modellel. A web-keresést az OpenRouter `openrouter:web_search` szervertoolja végzi.

## Mit tartalmaz

```
palyazatfigyelo.py          # a heti futás logikája
config.py                   # cégprofil + forráslista + modell/beállítások
requirements.txt            # Python függőségek
.github/workflows/palyazatfigyelo.yml   # heti ütemezés (hétfő 06:00 UTC = 08:00 Budapest)
docs/index.html             # dashboard (GitHub Pages)
docs/data.json              # a dashboard adata (futásonként frissül)
state/seen.json             # deduplikáció (mit láttunk már) – futásonként frissül
digests/                    # heti digest .md fájlok
```

## Beállítás lépésről lépésre

### 1. Repo létrehozása
Töltsd fel ezt a mappát egy (privát) GitHub repóba.

### 2. Secrets megadása
GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.
Kötelező:

| Secret neve | Érték |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API-kulcs (openrouter.ai/keys) |

Slack értesítéshez:

| Secret neve | Érték |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL (api.slack.com/messaging/webhooks) |

E-mail értesítéshez (pl. Gmail app password vagy céges SMTP):

| Secret neve | Példa |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `figyelo@codecool.com` |
| `SMTP_PASS` | app-jelszó / SMTP-jelszó |
| `EMAIL_FROM` | `figyelo@codecool.com` |
| `EMAIL_TO` | `felelos1@codecool.com, felelos2@codecool.com` |

Az e-mail és a Slack is opcionális: amelyikhez nincs secret, azt a script kihagyja.

### 3. GitHub Pages bekapcsolása (dashboard)
Repo → **Settings → Pages** → *Source: Deploy from a branch* → branch `main`, mappa `/docs`.
A dashboard ezután a `https://<felhasznalo>.github.io/<repo>/` címen lesz elérhető.

### 4. Első futás kézzel
Repo → **Actions → Palyazatfigyelo → Run workflow**.
Ez lefuttatja a keresést, feltölti a `docs/data.json`-t, ír egy digestet, és kiküldi az értesítéseket.

Ezután minden **hétfő reggel** magától fut.

## Testreszabás

- **Fókusz / kulcsszavak / célországok:** `config.py` → `COMPANY_PROFILE`.
- **Figyelt források:** `config.py` → `SOURCES` (bővíthető; a cégoldal-felderítés e nélkül is megy).
- **Ütemezés:** `.github/workflows/palyazatfigyelo.yml` → `cron`. A cron UTC-ben van!
  Hétfő 08:00 Budapest ≈ `0 6 * * 1` (nyári idő). Napi futáshoz: `0 6 * * *`.
- **Mit jelentsen push-ban:** `config.py` → `MIN_RELEVANCE` (`high` = csak a legjobbak).
- **Modell:** `config.py` → `MODEL`. OpenRouter-slug, Anthropic modellhez `anthropic/` prefix
  (pl. `anthropic/claude-sonnet-5`, erősebbhez `anthropic/claude-opus-4.5`).
- **Web-keresés / költség:** `config.py` → `MAX_RESULTS_PER_SEARCH`, `MAX_TOTAL_RESULTS`.

## Költség
A díj az OpenRouter-egyenlegből megy: a modell token-díja + a web-keresés
(Exa-motor kb. $4 / 1000 találat, azaz alapból max. ~$0,02 keresésenként).
Futásonként jellemzően pár száz forint. A GitHub Actions és a Pages a szokásos használatnál ingyenes.

## Korlátok, őszintén
- A hivatalos portálok lefedettsége megbízható; a cégoldal-felderítés „best effort", nem teljes.
- A modell tévedhet (határidő, jogosultság) – a találatokat mindig ellenőrizd a hivatalos linken.
- Ez kiinduló verzió: éles használat előtt érdemes 1-2 futást emberi szemmel átnézni.
