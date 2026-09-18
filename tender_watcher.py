#!/usr/bin/env python3
"""
Codecool Tender Watcher – weekly run in the cloud.

What a single run does:
  1. Calls the model (Anthropic Claude) through OpenRouter with the
     openrouter:web_search server tool; it combs through the source portals and
     also targets EU corporate pages for relevant, open calls / tenders.
  2. The model returns structured JSON describing the results.
  3. Deduplicates against state/seen.json -> flags the NEW items.
  4. Updates the dashboard data (docs/data.json) and writes a digest (digests/…md).
  5. Sends an e-mail and/or a Slack message if there is anything new.

Environment variables (GitHub Actions secrets):
  OPENROUTER_API_KEY          – required
  SLACK_WEBHOOK_URL           – optional (Slack incoming webhook)
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO – optional (e-mail)
"""

import os
import re
import sys
import time
import json
import ssl
import smtplib
import datetime as dt
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import SplitResult, urlsplit

import requests

import config
import ted_source

ROOT = Path(__file__).parent
STATE_DIR = ROOT / "state"
DOCS_DIR = ROOT / "docs"
DIGEST_DIR = ROOT / "digests"
SEEN_FILE = STATE_DIR / "seen.json"
DATA_FILE = DOCS_DIR / "data.json"
ARCHIVE_FILE = DOCS_DIR / "archive.json"

REL_ORDER = {"high": 0, "med": 1, "low": 2}

# HTTP statuses worth a retry: transient provider / rate-limit hiccups.
# 401/402/403/404 are NOT here – those need a human, retrying only wastes time.
RETRY_STATUSES = {408, 409, 429, 500, 502, 503, 504}
RETRY_ATTEMPTS = 3


# --------------------------------------------------------------------------- #
# 1. Search through OpenRouter (openrouter:web_search server tool)
# --------------------------------------------------------------------------- #
def build_prompt(ted_candidates: list[dict]) -> str:
    """Build the model prompt. Kept in Hungarian on purpose: the company profile
    and the search segments in config.py are written in Hungarian as well.

    `ted_candidates` are open TED notices fetched straight from the API - the
    model does not have to search for them, only to judge their relevance."""
    segments = "\n".join(f"  {n}. {s}" for n, s in enumerate(config.SEARCH_SEGMENTS, 1))
    sources = "\n".join(
        f"  - {s['name']}: {s['url']}\n    → a jelentésbe ez kerüljön: {s['item_hint']}"
        for s in config.MONITORED_SOURCES
    )
    today = dt.date.today().isoformat()
    ted_block = _ted_prompt_block(ted_candidates)
    return f"""Ma {today} van. Te a Codecool pályázat- és tenderfigyelője vagy.

CÉGPROFIL:
{config.COMPANY_PROFILE}

FELADAT: fésüld át a TELJES európai piacot friss (nyitott vagy hamarosan nyíló)
lehetőségekért. NEM csak EU-s pályázatok érdekesek – ugyanolyan súllyal keresd a
közbeszerzéseket (állami, városi/önkormányzati) és a magáncégek beszerzési tendereit is.

Használd a web-search eszközt: összesen kb. {config.MAX_SEARCHES} keresést futtathatsz.
Nyolc szegmens van, ennél kevesebb keresésed – tehát NE oszd el egyenletesen, hanem
prioritás szerint. A keresés az, amit a TED API NEM fed le, ezért:
  - ELŐSZÖR (kb. 5 keresés): céges/magánszektor tenderek (5.) – ez a legnehezebben
    megtalálható, de kiemelten fontos kategória –, valamint EU-s és magyar pályázatok (1., 2.).
  - UTÁNA (kb. 4 keresés): a három új szolgáltatási ág, amire eddig nem kerestünk:
    e-learning tananyagfejlesztés és LMS (6.), készségfelmérés és képzési tanácsadás (7.),
    IT-toborzás és munkaerő-biztosítás (8.). Legalább egy-egy keresés jusson mindháromra.
  - VÉGÜL (a maradék): nemzeti értékhatár alatti portálok (3.) és városi/önkormányzati
    beszerzések (4.).
A zárójeles portálnevek csak PÉLDÁK a kiinduláshoz – NE korlátozd rájuk a keresést,
minden szegmensben derítsd fel magad a további forrásokat:
{segments}

KÖTELEZŐEN FIGYELENDŐ FORRÁSOK – ezeket MINDEN futásban nézd át (pl. site: szűkítéssel):
{sources}
Ezek BELÉPÉSI PONTOK, nem eredmények! Magát a felsorolt listaoldalt / híroldalt SOHA ne add
vissza találatként – mindig az egyes konkrét kiírás saját oldaláig kell lefúrni. Ha egy
listaoldalon vagy hírben több kiírást látsz, mindegyikre futtass külön célzott keresést
(pl. "site:hadea.ec.europa.eu calls-proposals advanced digital skills",
"site:ted.europa.eu notice IT training", "site:ekr.gov.hu EKR képzés eljárás"),
és a megtalált KONKRÉT oldalakat vedd fel külön tételként.

{ted_block}
Keresési tippek:
  - Keress helyi nyelveken is, pl.: "tarjouspyyntö koulutus", "Ausschreibung IT-Schulung",
    "appel d'offres formation numérique", "przetarg szkolenia IT", "διαγωνισμός κατάρτιση",
    "upphandling utbildning", "aanbesteding opleiding", "IT training tender".
  - Céges tenderekhez próbáld: "ajánlattételi felhívás képzés", "ajánlattételi felhívás oktatás",
    "RFP IT training", "request for proposal training services", "invitation to tender training",
    illetve nagyvállalatok "suppliers" / "procurement" / "hirdetmények" / "tenders" aloldalait.
  - Városi és regionális beszerzési oldalak, egyetemek, munkaügyi szervezetek is számítanak.

RELEVANCIA-BESOROLÁS – a "relevance" mezőt EZEK alapján töltsd ki, ne érzésre.
A besorolás indokát írd bele a summary-be is (1 tagmondat elég).

  high – a cégprofil MAGJÁBA talál:
     * IT / digitális / AI / adat / felhő / DevOps / kiberbiztonság / szoftverfejlesztés /
       szoftvertesztelés képzés, át- vagy továbbképzési (reskilling / upskilling) program;
     * e-learning tananyagfejlesztés, digitális tananyaggyártás, illetve olyan LMS- vagy
       oktatásiszoftver-beszerzés, ahol a Codecool a SAJÁT platformját (Journey) vagy a
       tartalmat szállíthatná. NEM high viszont az, ami konkrét idegen terméket nevez meg
       (pl. Moodle, Canvas, Blackboard), vagy tisztán licenc / hosting / üzemeltetés
       tartalomfejlesztési és képzési elem nélkül – az med, jellemzően low;
     * lakossági, közszolgálati vagy vállalati digitális ALAPKÉSZSÉG-program (nem csak
       IT-seknek szóló képzés is ide tartozik);
     * digitális készségfejlesztésre szóló EU-s call, amelyre konzorciumi tagként pályázhat.
     Ha mindezek mellett a kiírás Magyarországon vagy a KKE-régióban van, az a legerősebb
     eset – a hazai piac és a magyar felnőttképzési engedély miatt.

  med – illeszkedik, de nem a mag:
     * általános felnőttképzés / szakképzés (VET), amelyben a digitális tartalom másodlagos;
     * IT-toborzási, szakember-kiválasztási vagy munkaerő-kölcsönzési tender;
     * készségfelmérés, kompetenciamátrix, képzési terv, digitális érettségfelmérés,
       megvalósíthatósági tanulmány mint megrendelés;
     * profilba vágó képzési tender Nyugat- vagy Dél-Európában, ahol jellemzően helyi
       partner vagy konzorcium kellene hozzá.

  low – csak érintőlegesen kapcsolódik:
     * nem digitális képzés: nyelvtanfolyam, jogosítvány és járművezetés, tűz- és
       munkavédelem, egészségügyi, gépkezelői, pedagógus-továbbképzés;
     * tisztán szoftver-, hardver- vagy licencbeszerzés érdemi képzési elem nélkül;
     * olyan akkreditációt vagy szakterületet kíván, amivel a Codecool nem rendelkezik.
     low tételt csak akkor vegyél fel, ha tényleg van benne értékelhető képzési elem –
     egyébként hagyd ki.

Szabályok:
  - Csak VALÓS, ellenőrzött találatokat adj meg valódi, működő linkkel. Ne találj ki kiírást.
  - Csak a cégprofilhoz releváns tételeket tartsd meg, a fenti besorolás szerint.
  - LEJÁRT határidejű kiírást ne vegyél fel – a mai dátumhoz ({today}) képest ellenőrizd.
  - EU-s programok (Digital Europe, Erasmus+, Horizon stb.) call-jainál KÖTELEZŐ a hivatalos
    europa.eu oldal (ec.europa.eu topic-details, hadea.ec.europa.eu/calls-proposals, eacea…).
    Nemzeti kapcsolattartó (pl. ffg.at) vagy tanácsadó összefoglalója NEM elfogadható.
    A call SAJÁT topic-oldalát add meg (…/topic-details/DIGITAL-2026-SKILLS-10), NE a
    munkaprogram PDF-jét – abban több topic is benne van, így két külön tétel ugyanarra a
    linkre mutatna, és a rendszer az egyiket elveszítené.
  - Az "url" mező KÖTELEZŐEN EGYETLEN konkrét kiírás saját oldalára mutasson. A jelentésen
    kívüli, automatikusan ELDOBOTT (tehát felesleges) linkek:
      * pályázatíró / hírportál cikkek, amelyek csak ÍRNAK a kiírásokról, pl.
        https://palyazatmenedzser.hu/digitalizacios-palyazat/
      * EU-s vagy hatósági HÍROLDALAK, amelyek csak bejelentik, hogy megjelentek a call-ok, pl.
        https://hadea.ec.europa.eu/news/new-calls-proposals-under-digital-europe-programme-published-2026-04-10_en
        (ilyenkor a hírben felsorolt EGYES call-ok saját oldalát add meg, a hírt magát ne)
      * ÚTMUTATÓK és szabályozási oldalak, amelyek a közbeszerzés MENETÉT magyarázzák,
        nem egy konkrét lehetőséget kínálnak, pl. Your Europe „közbeszerzési szabályok",
        Közbeszerzési Kisokos, ProcurCompEU, Erasmus+ programme guide
      * portál-főoldalak, kereső-, kategória- és listaoldalak, pl.
        https://ted.europa.eu/hu/, https://ekr.gov.hu/portal/kozbeszerzes/hirdetmenyek,
        https://tendigo.de/ausschreibungen/weiterbildung, https://erasmus-plus.ec.europa.eu/opportunities
    Ha egy kiíráshoz nem találod meg a saját oldalát, inkább HAGYD KI a tételt – a listaoldal
    nem elfogadható pótlék.
  - Törekedj arra, hogy a találatok több országból és több szegmensből (pályázat,
    közbeszerzés, céges tender) származzanak, ne csak egy-két portálról.

A JSON elé LEGFELJEBB 3 mondat összefoglalót írj – a kimeneti kereted véges, és a
JSON a fontos, nem a bevezető próza. Az egyes tételek "summary" mezője is maradjon
1-2 mondat.

A válaszod VÉGÉN adj vissza KIZÁRÓLAG egy JSON-tömböt (```json blokkban), ilyen mezőkkel:
[
  {{
    "title": "…",
    "url": "https://…",
    "category": "eu" | "hu" | "tender" | "company",  // eu = EU-s pályázat, hu = magyar pályázat, tender = közbeszerzés (állami/városi), company = céges/magánszektor tender
    "program": "forrás/program neve",
    "budget": "becsült keret vagy '' ",
    "deadline": "ÉÉÉÉ-HH-NN vagy '' ha nincs pontos",
    "deadline_text": "emberi olvasható határidő",
    "relevance": "high" | "med" | "low",   // a fenti RELEVANCIA-BESOROLÁS szerint
    "summary": "1-2 mondat: miért releváns Codecoolnak, és mi indokolja a besorolást"
  }}
]
Csak a JSON-tömböt add a záró blokkban, más szöveget ne tegyél utána."""


def _ted_prompt_block(candidates: list[dict]) -> str:
    """The TED notices are handed over as data, not as something to search for.
    Empty (API down / nothing open) -> the prompt simply does not mention TED."""
    if not candidates:
        return ""
    listing = ted_source.format_for_prompt(candidates)
    return f"""
NYITOTT TED-KÖZBESZERZÉSEK ({len(candidates)} db) – ezeket KÉSZEN KAPOD a TED hivatalos
API-jából, NEM kell rájuk keresned. Mind nyitott határidejű és ellenőrzött:
{listing}

Mit kezdj velük:
  - Nézd át MINDET, és amelyik a cégprofilhoz releváns (IT-/digitális képzés, e-learning,
    reskilling, tananyagfejlesztés, oktatási szolgáltatás), azt vedd fel a végső JSON-be
    "tender" kategóriával, PONTOSAN a fenti URL-lel és határidővel.
  - A nem relevánsakat (pl. tűzvédelmi oktatás, jogosítvány, nyelvtanfolyam) hagyd ki –
    ne magyarázkodj miattuk.
  - Mivel a TED-et így már lefedtük, a web-search kereséseidet a TÖBBI szegmensre fordítsd:
    EU-s és magyar pályázatok, városi/önkormányzati beszerzések, és kiemelten a
    céges/magánszektor tenderek.

"""


def fetch_opportunities(api_key: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codecool/tender-watcher",
        "X-Title": "Codecool Tender Watcher",
    }
    body = {
        "model": config.MODEL,
        "messages": [{"role": "user", "content": build_prompt(ted_source.fetch_candidates())}],
        "max_tokens": config.MAX_OUTPUT_TOKENS,
        "tools": [{
            "type": "openrouter:web_search",
            "parameters": {
                "max_results": config.MAX_RESULTS_PER_SEARCH,
                "max_uses": config.MAX_SEARCHES,
                "max_total_results": config.MAX_TOTAL_RESULTS,
            },
        }],
    }
    resp = post_with_retry(headers, body)
    if resp.status_code != 200:
        report_api_error(resp, api_key)
        raise SystemExit(f"The OpenRouter call failed: HTTP {resp.status_code} (details above).")
    data = resp.json()
    log_search_debug(data)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"Unexpected OpenRouter response: {json.dumps(data)[:800]}") from exc
    if isinstance(content, list):
        text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        text = content or ""
    return filter_items(parse_json_array(text), "model results")


def post_with_retry(headers: dict, body: dict) -> requests.Response:
    """POST to OpenRouter, retrying only the transient statuses (rate limit,
    provider hiccup). Returns the last response – the caller inspects the code."""
    resp = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        resp = requests.post(
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=body,
            timeout=600,
        )
        if resp.status_code == 200 or resp.status_code not in RETRY_STATUSES:
            return resp
        if attempt == RETRY_ATTEMPTS:
            break
        wait = 30 * attempt
        print(f"OpenRouter HTTP {resp.status_code}: {error_reason(resp)} – "
              f"retry {attempt}/{RETRY_ATTEMPTS - 1} in {wait}s")
        time.sleep(wait)
    return resp


def error_reason(resp: requests.Response) -> str:
    """Pull the human-readable reason out of an OpenRouter error body.
    Shape: {"error": {"code": …, "message": …, "metadata": {…}}}."""
    try:
        err = (resp.json() or {}).get("error") or {}
    except ValueError:
        return resp.text[:600] or "(empty response body)"
    parts = [str(err.get("message") or "(no message)")]
    meta = err.get("metadata") or {}
    if meta.get("reasons"):
        parts.append("moderation reasons: " + ", ".join(str(r) for r in meta["reasons"]))
    if meta.get("flagged_input"):
        parts.append(f"flagged input: {meta['flagged_input']!r}")
    if meta.get("provider_name"):
        parts.append(f"provider: {meta['provider_name']}")
    if meta.get("raw"):
        parts.append(f"raw: {str(meta['raw'])[:400]}")
    return " | ".join(parts)


def describe_key(api_key: str) -> str:
    """Ask OpenRouter about the key AND the account balance behind it.

    Both are needed, and the difference bites: on 2026-09-17 a run died on HTTP
    402 while the key still showed limit_remaining=$44.53. The key's monthly cap
    was fine; the account had $0.01 of credit left. Reporting only the key made
    the run log look like the key was healthy."""
    parts = []
    try:
        resp = requests.get(
            f"{config.OPENROUTER_BASE_URL}/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        if resp.status_code == 200:
            d = (resp.json() or {}).get("data") or {}
            parts.append(f"key: label={d.get('label')!r} usage=${d.get('usage')} "
                         f"monthly_limit={d.get('limit')} limit_remaining={d.get('limit_remaining')} "
                         f"free_tier={d.get('is_free_tier')}")
        else:
            parts.append(f"key lookup returned HTTP {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as exc:
        parts.append(f"key lookup failed: {exc}")
    parts.append(describe_balance(api_key))
    return " | ".join(parts)


def describe_balance(api_key: str) -> str:
    """Account credit left. This – not the key's monthly limit – is what an
    HTTP 402 is actually about."""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
    except requests.RequestException as exc:
        return f"balance lookup failed: {exc}"
    if resp.status_code != 200:
        return f"balance lookup returned HTTP {resp.status_code}"
    d = (resp.json() or {}).get("data") or {}
    total, used = d.get("total_credits") or 0, d.get("total_usage") or 0
    left = total - used
    flag = "  <-- OUT OF CREDIT, top up the account" if left < 2 else ""
    return f"ACCOUNT BALANCE: ${left:.2f} left (${total:.2f} topped up, ${used:.2f} used){flag}"


def report_api_error(resp: requests.Response, api_key: str) -> None:
    """Print everything needed to tell the 4xx cases apart – the bare
    raise_for_status() used to throw the response body away."""
    request_id = resp.headers.get("x-request-id") or resp.headers.get("x-openrouter-id") or "n/a"
    print(f"OpenRouter error: HTTP {resp.status_code} (request id: {request_id})")
    print(f"  reason: {error_reason(resp)}")
    print(f"  model: {config.MODEL}")
    if resp.status_code in (401, 402, 403):
        print(f"  {describe_key(api_key)}")
    if resp.status_code == 402:
        print("  402 = the ACCOUNT ran out of credit. The key's monthly limit can still look")
        print("  healthy – check the ACCOUNT BALANCE line above, and top up at")
        print("  https://openrouter.ai/settings/credits")
    if resp.status_code == 403:
        print("  403 on OpenRouter = insufficient permission, guardrail block or moderation flag.")
        print("  Check in order: spend limit on the key (openrouter.ai/keys), the account's")
        print("  privacy / data policy settings for this model (openrouter.ai/settings/privacy),")
        print("  and the 'reason' line above for a moderation hit.")


def log_search_debug(data: dict) -> None:
    """Saves the raw API response (state/last_response.json) and prints to the run
    log how many web searches happened, which searches the model started (if the
    response contains them), and which sources it cited."""
    STATE_DIR.mkdir(exist_ok=True)
    (STATE_DIR / "last_response.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    usage = data.get("usage") or {}
    server_tools = usage.get("server_tool_use_details") or usage.get("server_tool_use") or {}
    if server_tools:
        print(f"Web searches in this run: {server_tools.get('web_search_requests', '?')}")
    if usage.get("cost") is not None:
        print(f"Run cost: ${usage['cost']:.4f}")

    message = (data.get("choices") or [{}])[0].get("message") or {}
    for call in message.get("tool_calls") or []:
        fn = call.get("function") or {}
        print(f"Tool call: {fn.get('name', '?')} {fn.get('arguments', '')}")

    urls = sorted({
        a.get("url_citation", {}).get("url")
        for a in message.get("annotations") or []
        if isinstance(a, dict) and a.get("url_citation", {}).get("url")
    })
    if urls:
        print(f"Cited sources ({len(urls)}):")
        for u in urls:
            print(f"  - {u}")


def parse_json_array(text: str) -> list[dict]:
    # Look for a ```json … ``` block first, then for the last [...] array.
    fenced = re.findall(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    candidates = fenced[:]
    if not candidates:
        m = re.search(r"(\[.*\])", text, re.DOTALL)
        if m:
            candidates = [m.group(1)]
    for chunk in reversed(candidates):
        try:
            data = json.loads(chunk)
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict) and d.get("url")]
        except json.JSONDecodeError:
            continue
    # Nothing parsed as a whole. The usual cause is the reply hitting max_tokens
    # mid-array, which used to throw away every result in it – so salvage the
    # objects that did come through complete.
    return salvage_objects(text)


def salvage_objects(text: str) -> list[dict]:
    """Pull the complete {...} objects out of a truncated JSON array."""
    start = text.find("[")
    if start < 0:
        return []
    items, depth, obj_start, in_str, escaped = [], 0, None, False, False
    for pos in range(start, len(text)):
        ch = text[pos]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                obj_start = pos
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    obj = json.loads(text[obj_start:pos + 1])
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(obj, dict) and obj.get("url"):
                        items.append(obj)
                obj_start = None
    if items:
        print(f"Truncated model reply – salvaged {len(items)} complete item(s) from it.")
    return items


# --------------------------------------------------------------------------- #
# 1b. Link quality filter
# --------------------------------------------------------------------------- #
# A URL survives only if it identifies a single opportunity. It is dropped when
# it is (a) on a known aggregator domain, (b) a portal homepage, (c) a
# news/press/blog article, or (d) a search/category/listing page with no item
# identifier. The rule tables live in config.py.

HAS_DIGIT_RE = re.compile(r"\d")


def normalized_url(url: str) -> str:
    """Host + path + query, lowercased, without scheme/www/trailing slash – so
    that the same page written two ways compares equal."""
    parts = urlsplit((url or "").strip().lower())
    host = parts.netloc.split("@")[-1].split(":")[0].removeprefix("www.")
    tail = f"?{parts.query}" if parts.query else ""
    return f"{host}{parts.path.rstrip('/')}{tail}"


MONITORED_LANDING_URLS = {normalized_url(s["url"]) for s in config.MONITORED_SOURCES}


def has_identifier(parts: SplitResult) -> bool:
    """True if the URL pins down a single item: either a query string (e.g.
    ?resourceId=8237157, ?callIdentifier=DIGITAL-2026-SKILLS-10) or a path
    segment carrying a number (notice/121172-2026, /Notice/010767-2026)."""
    if parts.query:
        return True
    return any(HAS_DIGIT_RE.search(seg) for seg in parts.path.split("/") if seg)


def reject_reason(url: str) -> str | None:
    """Why this URL must not be reported – or None if it is a concrete
    opportunity page."""
    parts = urlsplit((url or "").strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return "not a valid http(s) link"

    host = parts.netloc.lower().split("@")[-1].split(":")[0].removeprefix("www.")
    for domain in config.AGGREGATOR_DOMAINS:
        if host == domain or host.endswith(f".{domain}"):
            return f"aggregator / news site ({domain}), not the call's own page"

    path = parts.path.lower()
    segments = [s for s in path.split("/") if s]
    if not segments or all(s in config.LANG_SEGMENTS for s in segments):
        return "portal homepage, not a specific call"

    for pattern in config.NEWS_PATH_PATTERNS:
        if pattern in path:
            return f"news / blog article ('{pattern}'), not the call's own page"

    for pattern in config.GUIDE_PATH_PATTERNS:
        if pattern in path:
            return f"guide / rulebook page ('{pattern}'), explains procurement instead of offering one"

    if not has_identifier(parts):
        listing = next((s for s in segments if s in config.LISTING_PATH_KEYWORDS), None)
        if listing:
            return f"search / listing page ('{listing}') without a specific call"
        if normalized_url(url) in MONITORED_LANDING_URLS:
            return "monitored source landing page, not a specific call"
    return None


def host_of(url: str) -> str:
    return urlsplit((url or "").strip()).netloc.lower().split("@")[-1].split(":")[0].removeprefix("www.")


def is_official_eu_host(host: str) -> bool:
    return any(host == d or host.endswith(f".{d}") for d in config.OFFICIAL_EU_DOMAINS)


def is_eu_level_call(item: dict) -> bool:
    """True if the item describes a call of an EU programme – either because it
    carries a programme call identifier (DIGITAL-2026-SKILLS-10), or because the
    model filed it under "eu" and named an EU programme."""
    blob = " ".join(str(item.get(f, "")) for f in ("title", "program", "summary"))
    if any(re.search(p, blob, re.I) for p in config.EU_CALL_ID_PATTERNS):
        return True
    if (item.get("category") or "").strip().lower() != "eu":
        return False
    return any(m in blob.lower() for m in config.EU_PROGRAMME_MARKERS)


def reject_item(item: dict) -> str | None:
    """Why this result must not be reported – URL rules first, then the
    EU-call-from-a-secondary-source rule."""
    url = item.get("url", "")
    reason = reject_reason(url)
    if reason:
        return reason
    if is_eu_level_call(item) and not is_official_eu_host(host_of(url)):
        return ("EU-level call reported from a secondary source – link its own "
                "page on an official EU domain instead")
    return None


def filter_items(items: list[dict], label: str = "results") -> list[dict]:
    """Drop every item that is not a concrete opportunity page from a primary
    source, and print what went and why – that log is how AGGREGATOR_DOMAINS in
    config.py gets extended when a new offender shows up."""
    kept, dropped, seen_urls = [], [], set()
    for it in items:
        reason = reject_item(it)
        if not reason:
            url = normalized_url(it.get("url", ""))
            if url in seen_urls:
                # Two results on one URL: the archive is keyed by URL, so the
                # second would silently overwrite the first. Seen when the model
                # links two DIGITAL-2026-SKILLS-10 topics to the same call PDF.
                reason = "duplicate URL – another result in this run already uses it"
            else:
                seen_urls.add(url)
        (dropped if reason else kept).append((it, reason))
    if dropped:
        print(f"Filtered out {len(dropped)} of {len(items)} {label} (not a specific opportunity):")
        for it, reason in dropped:
            print(f"  - {it.get('url', '')} — {reason}")
    return [it for it, _ in kept]


# --------------------------------------------------------------------------- #
# 2. Dedup
# --------------------------------------------------------------------------- #
def key_of(item: dict) -> str:
    return (item.get("url") or item.get("title", "")).strip().lower().rstrip("/")


def load_seen() -> dict:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    return {}


def save_seen(seen: dict) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_new(items: list[dict], seen: dict) -> list[dict]:
    today = dt.date.today().isoformat()
    for it in items:
        k = key_of(it)
        it["is_new"] = k not in seen
        it["first_seen"] = seen.get(k, today)
        seen[k] = it["first_seen"]
    items.sort(key=lambda x: (not x["is_new"], REL_ORDER.get(x.get("relevance"), 3)))
    return items


# --------------------------------------------------------------------------- #
# 3. Outputs: dashboard data + digest
# --------------------------------------------------------------------------- #
def write_data_json(items: list[dict]) -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    payload = {
        "updated": dt.date.today().isoformat(),
        "items": items,
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def update_archive(items: list[dict]) -> None:
    """Cumulative archive: every item ever found is kept (docs/archive.json) with
    first_seen / last_seen dates. The Archive view of the dashboard reads this."""
    today = dt.date.today().isoformat()
    archive: dict[str, dict] = {}
    if ARCHIVE_FILE.exists():
        stored = json.loads(ARCHIVE_FILE.read_text(encoding="utf-8")).get("items", [])
        for entry in filter_items(stored, "archived items"):
            archive[key_of(entry)] = entry
    for it in items:
        k = key_of(it)
        old = archive.get(k, {})
        entry = {f: it.get(f, "") for f in (
            "title", "url", "category", "program", "budget",
            "deadline", "deadline_text", "relevance", "summary")}
        entry["first_seen"] = old.get("first_seen") or it.get("first_seen") or today
        entry["last_seen"] = today
        archive[k] = entry
    payload = {
        "updated": today,
        "items": sorted(archive.values(), key=lambda e: (e["last_seen"], e["first_seen"]), reverse=True),
    }
    ARCHIVE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_digest(items: list[dict]) -> Path:
    DIGEST_DIR.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    new_items = [i for i in items if i["is_new"]]
    lines = [
        f"# Codecool Tender Watcher – digest ({today})",
        "",
        f"Total results: {len(items)} · New among them: {len(new_items)}",
        "",
    ]
    if new_items:
        lines += ["## New results", ""]
        for i in new_items:
            lines += _digest_block(i)
    lines += ["## All current items", ""]
    for i in items:
        lines += _digest_block(i)
    path = DIGEST_DIR / f"digest-{today}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _digest_block(i: dict) -> list[str]:
    rel = {"high": "High", "med": "Medium", "low": "Low"}.get(i.get("relevance"), "?")
    tag = "🆕 " if i.get("is_new") else ""
    return [
        f"### {tag}{i.get('title', '')}",
        f"- **Source:** {i.get('program', '')} · **Category:** {i.get('category', '')}",
        f"- **Budget:** {i.get('budget') or 'n/a'} · **Deadline:** {i.get('deadline_text') or 'n/a'} · **Relevance:** {rel}",
        f"- {i.get('summary', '')}",
        f"- {i.get('url', '')}",
        "",
    ]


# --------------------------------------------------------------------------- #
# 4. Notifications
# --------------------------------------------------------------------------- #
def notify_slack(new_items: list[dict]) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url or not new_items:
        return
    lines = [f"*Codecool Tender Watcher – {len(new_items)} new result(s)*"]
    for i in new_items:
        lines.append(f"• <{i['url']}|{i.get('title','')}> — {i.get('deadline_text') or 'no deadline'} ({i.get('relevance')})")
    requests.post(url, json={"text": "\n".join(lines)}, timeout=30)


def notify_email(new_items: list[dict], digest_path: Path) -> None:
    host = os.environ.get("SMTP_HOST")
    to = os.environ.get("EMAIL_TO")
    if not host or not to or not new_items:
        return
    body = digest_path.read_text(encoding="utf-8")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Tender Watcher – {len(new_items)} new result(s) ({dt.date.today().isoformat()})"
    msg["From"] = os.environ.get("EMAIL_FROM", os.environ.get("SMTP_USER", ""))
    msg["To"] = to
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.sendmail(msg["From"], [a.strip() for a in to.split(",")], msg.as_string())


# --------------------------------------------------------------------------- #
def prune_stored_items() -> None:
    """Re-run the link filter over everything already stored (dashboard data,
    archive, dedup state) and drop what no longer qualifies. Needed once after a
    filter-rule change, so aggregator pages found by earlier runs disappear from
    the dashboard without waiting for the weekly run. No model call, no cost."""
    for path, key in ((DATA_FILE, "items"), (ARCHIVE_FILE, "items")):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload[key] = filter_items(payload.get(key, []), f"{path.name} entries")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if SEEN_FILE.exists():
        seen = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        kept = {u: d for u, d in seen.items() if not reject_reason(u)}
        if len(kept) != len(seen):
            print(f"seen.json: {len(seen) - len(kept)} rejected URL(s) removed.")
        save_seen(kept)
    print("Pruning done.")


def main() -> None:
    if "--prune" in sys.argv:
        prune_stored_items()
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("The OPENROUTER_API_KEY environment variable is missing.")

    # `python tender_watcher.py --diagnose` only asks about the key – no model
    # call, no cost. Use it when a run dies on 401/402/403.
    if "--diagnose" in sys.argv:
        print(f"Key status: {describe_key(api_key)}")
        print(f"Configured model: {config.MODEL}")
        return

    items = fetch_opportunities(api_key)
    if not items:
        print("No processable results (empty or malformed JSON).")
    seen = load_seen()
    items = mark_new(items, seen)
    save_seen(seen)

    write_data_json(items)
    update_archive(items)
    digest_path = write_digest(items)

    min_rank = REL_ORDER.get(config.MIN_RELEVANCE, 1)
    new_items = [
        i for i in items
        if i["is_new"] and REL_ORDER.get(i.get("relevance"), 3) <= min_rank
    ]
    notify_slack(new_items)
    notify_email(new_items, digest_path)

    print(f"Done. Total: {len(items)}, new (reported): {len(new_items)}. Digest: {digest_path.name}")


if __name__ == "__main__":
    main()
