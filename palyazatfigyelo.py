#!/usr/bin/env python3
"""
Codecool Pályázatfigyelő – felhős heti futás.

Mit csinál egy futáskor:
  1. A Claude API-t hívja beépített web-search eszközzel; átfésüli a forrásportálokat
     és célzottan felderít EU-s cégoldalakat releváns, nyitott pályázatokért/tenderekért.
  2. A modell strukturált JSON-t ad vissza a találatokról.
  3. Deduplikál a state/seen.json alapján -> megjelöli az ÚJ tételeket.
  4. Frissíti a dashboard adatát (docs/data.json) és ír egy digestet (digests/…md).
  5. E-mailt és/vagy Slack-üzenetet küld, ha van új találat.

Környezeti változók (GitHub Actions secrets):
  ANTHROPIC_API_KEY            – kötelező
  SLACK_WEBHOOK_URL            – opcionális (Slack incoming webhook)
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO – opcionális (e-mail)
"""

import os
import re
import json
import ssl
import smtplib
import datetime as dt
from email.mime.text import MIMEText
from pathlib import Path

import requests
import anthropic

import config

ROOT = Path(__file__).parent
STATE_DIR = ROOT / "state"
DOCS_DIR = ROOT / "docs"
DIGEST_DIR = ROOT / "digests"
SEEN_FILE = STATE_DIR / "seen.json"
DATA_FILE = DOCS_DIR / "data.json"

REL_ORDER = {"high": 0, "med": 1, "low": 2}


# --------------------------------------------------------------------------- #
# 1. Keresés a Claude API-val (web search eszközzel)
# --------------------------------------------------------------------------- #
def build_prompt() -> str:
    sources = "\n".join(f"  - {s}" for s in config.SOURCES)
    today = dt.date.today().isoformat()
    return f"""Ma {today} van. Te a Codecool pályázatfigyelője vagy.

CÉGPROFIL:
{config.COMPANY_PROFILE}

Használd a web_search eszközt, és fésüld át a következő megbízható forrásokat friss
(nyitott vagy hamarosan nyíló) kiírásokért – pályázatok, támogatások, közbeszerzések, tenderek:
{sources}

Ezen felül végezz CÉLZOTT felderítést EU-s cégek / ügynökségek saját tender-, "procurement"-,
"hankinnat"-oldalain (nem kell előre megadott lista – keresd meg magad, kiemelten a finn / északi piacon).

Szabályok:
  - Csak VALÓS, ellenőrzött találatokat adj meg valódi, működő linkkel. Ne találj ki kiírást.
  - Csak a cégprofilhoz releváns tételeket tartsd meg.
  - Legfeljebb {config.MAX_WEB_SEARCHES} keresést végezz.

A válaszod VÉGÉN adj vissza KIZÁRÓLAG egy JSON-tömböt (```json blokkban), ilyen mezőkkel:
[
  {{
    "title": "…",
    "url": "https://…",
    "category": "eu" | "hu" | "tender" | "company",
    "program": "forrás/program neve",
    "budget": "becsült keret vagy '' ",
    "deadline": "ÉÉÉÉ-HH-NN vagy '' ha nincs pontos",
    "deadline_text": "emberi olvasható határidő",
    "relevance": "high" | "med" | "low",
    "summary": "1-2 mondat, miért releváns Codecoolnak"
  }}
]
Csak a JSON-tömböt add a záró blokkban, más szöveget ne tegyél utána."""


def fetch_opportunities(client: anthropic.Anthropic) -> list[dict]:
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=8000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": config.MAX_WEB_SEARCHES,
        }],
        messages=[{"role": "user", "content": build_prompt()}],
    )
    # Összefűzzük a szöveges blokkokat, kinyerjük az utolsó JSON-tömböt.
    text = "".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    )
    return parse_json_array(text)


def parse_json_array(text: str) -> list[dict]:
    # Először ```json … ``` blokkot keresünk, aztán az utolsó [...]-tömböt.
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
    return []


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
# 3. Kimenetek: dashboard adat + digest
# --------------------------------------------------------------------------- #
def write_data_json(items: list[dict]) -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    payload = {
        "updated": dt.date.today().isoformat(),
        "items": items,
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_digest(items: list[dict]) -> Path:
    DIGEST_DIR.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    new_items = [i for i in items if i["is_new"]]
    lines = [
        f"# Codecool Pályázatfigyelő – digest ({today})",
        "",
        f"Összes találat: {len(items)} · Ebből új: {len(new_items)}",
        "",
    ]
    if new_items:
        lines += ["## Új találatok", ""]
        for i in new_items:
            lines += _digest_block(i)
    lines += ["## Összes aktuális tétel", ""]
    for i in items:
        lines += _digest_block(i)
    path = DIGEST_DIR / f"digest-{today}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _digest_block(i: dict) -> list[str]:
    rel = {"high": "Magas", "med": "Közepes", "low": "Alacsony"}.get(i.get("relevance"), "?")
    tag = "🆕 " if i.get("is_new") else ""
    return [
        f"### {tag}{i.get('title', '')}",
        f"- **Forrás:** {i.get('program', '')} · **Kategória:** {i.get('category', '')}",
        f"- **Keret:** {i.get('budget') or 'n/a'} · **Határidő:** {i.get('deadline_text') or 'n/a'} · **Relevancia:** {rel}",
        f"- {i.get('summary', '')}",
        f"- {i.get('url', '')}",
        "",
    ]


# --------------------------------------------------------------------------- #
# 4. Értesítések
# --------------------------------------------------------------------------- #
def notify_slack(new_items: list[dict]) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url or not new_items:
        return
    lines = [f"*Codecool Pályázatfigyelő – {len(new_items)} új találat*"]
    for i in new_items:
        lines.append(f"• <{i['url']}|{i.get('title','')}> — {i.get('deadline_text') or 'nincs határidő'} ({i.get('relevance')})")
    requests.post(url, json={"text": "\n".join(lines)}, timeout=30)


def notify_email(new_items: list[dict], digest_path: Path) -> None:
    host = os.environ.get("SMTP_HOST")
    to = os.environ.get("EMAIL_TO")
    if not host or not to or not new_items:
        return
    body = digest_path.read_text(encoding="utf-8")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Pályázatfigyelő – {len(new_items)} új találat ({dt.date.today().isoformat()})"
    msg["From"] = os.environ.get("EMAIL_FROM", os.environ.get("SMTP_USER", ""))
    msg["To"] = to
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.sendmail(msg["From"], [a.strip() for a in to.split(",")], msg.as_string())


# --------------------------------------------------------------------------- #
def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Hiányzik az ANTHROPIC_API_KEY környezeti változó.")
    client = anthropic.Anthropic(api_key=api_key)

    items = fetch_opportunities(client)
    if not items:
        print("Nincs feldolgozható találat (üres vagy hibás JSON).")
    seen = load_seen()
    items = mark_new(items, seen)
    save_seen(seen)

    write_data_json(items)
    digest_path = write_digest(items)

    min_rank = REL_ORDER.get(config.MIN_RELEVANCE, 1)
    new_items = [
        i for i in items
        if i["is_new"] and REL_ORDER.get(i.get("relevance"), 3) <= min_rank
    ]
    notify_slack(new_items)
    notify_email(new_items, digest_path)

    print(f"Kész. Összes: {len(items)}, új (jelentett): {len(new_items)}. Digest: {digest_path.name}")


if __name__ == "__main__":
    main()
