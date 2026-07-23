# Codecool Pályázatfigyelő (felhős, GitHub Actions)

Heti automata, ami az interneten releváns pályázatokat, támogatásokat, közbeszerzéseket
és tendereket keres a Codecool számára (EU + magyar források + EU-s cégoldalak, pl. finn),
majd e-mailben és/vagy Slackben értesít, és egy webes dashboardon is megjeleníti a találatokat.

Nem kell felconfigurálni a figyelt honlapokat – a Claude API a cégprofil és a forrásportálok
alapján magától keres, és célzottan felderít cégoldalakat is.

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
| `ANTHROPIC_API_KEY` | Anthropic API-kulcs (console.anthropic.com) |

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
- **Modell/költség:** `config.py` → `MODEL`, `MAX_WEB_SEARCHES`.

## Költség
Futásonként pár száz forintnyi API- és web-search-díj (a keresések számától függ).
A GitHub Actions és a Pages a szokásos használatnál ingyenes.

## Korlátok, őszintén
- A hivatalos portálok lefedettsége megbízható; a cégoldal-felderítés „best effort", nem teljes.
- A modell tévedhet (határidő, jogosultság) – a találatokat mindig ellenőrizd a hivatalos linken.
- Ez kiinduló verzió: éles használat előtt érdemes 1-2 futást emberi szemmel átnézni.
