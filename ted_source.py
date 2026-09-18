"""
TED (Tenders Electronic Daily) – direct API access.

Why this module exists: the watcher used to reach TED only through the model's
web search, and it kept missing open notices. On 2026-09-16 a run with 16
searches returned zero TED results while the API showed 66 IT-training notices
published in the previous 21 days, 7 of them still open – including
585619-2026 (Hungarian e-learning course material, deadline 2026-09-28) and
599109-2026 (Norwegian computer security training, deadline 2026-09-28).

So TED is no longer searched, it is queried. This module pulls the open notices
deterministically; the model then only has to judge which ones fit Codecool.
The same is not possible for EKR: its notice pages are a JavaScript app that
neither a search engine nor an HTTP fetch can read. Hungarian above-threshold
procedures do reach TED, so they come in through here.

API docs: https://api.ted.europa.eu/ (no API key needed for search).
"""

import datetime as dt
import time

import requests

import config

# Preferred languages for the multilingual title / description / buyer fields.
LANG_PREFERENCE = ("hun", "eng", "deu", "fra")


def fetch_candidates() -> list[dict]:
    """Open, relevant TED notices – each service line with its own quota.

    Quotas matter: training notices outnumber the rest by an order of magnitude,
    so a single deadline-ordered list would never reach an e-learning platform
    or an IT recruitment tender. Each group is filled independently.

    Never raises: TED being slow or down must not kill the weekly run – the
    watcher then falls back to web search alone, with a line in the log.
    """
    picked: dict[str, dict] = {}
    for group in config.TED_GROUPS:
        try:
            found = _search(group["cpv"], digital_only=group["digital_only"],
                            title_only=group.get("digital_in_title_only", False))
        except (requests.RequestException, ValueError) as exc:
            print(f"TED group '{group['key']}' unavailable ({exc}) – skipped.")
            continue
        fresh = [n for n in sorted(found, key=_ranking_key)
                 if n["publication_number"] not in picked]
        for notice in fresh[:group["quota"]]:
            notice["group"] = group["label"]
            notice["cpv_label"] = ", ".join(matched_cpvs(notice))
            picked[notice["publication_number"]] = notice
        print(f"TED · {group['label']}: {len(found)} open, "
              f"{min(len(fresh), group['quota'])} handed over (quota {group['quota']}).")

    if not picked:
        print("TED: no open notice found – this run relies on web search alone.")
        return []
    candidates = sorted(picked.values(), key=_ranking_key)
    print(f"TED: {len(candidates)} notice(s) handed to the model.")
    return candidates


def _search(cpv_codes: list[str], digital_only: bool, title_only: bool = False) -> list[dict]:
    """One paged query for a CPV group. `digital_only` keeps the broad training
    codes usable: a fire-safety or driving course is dropped, an IT one is not."""
    query = (
        f"classification-cpv IN ({' '.join(cpv_codes)}) "
        f"AND publication-date >= today(-{config.TED_LOOKBACK_DAYS}) "
        f"AND notice-type IN ({' '.join(config.TED_NOTICE_TYPES)})"
    )
    out, page = [], 1
    while page <= config.TED_MAX_PAGES:
        payload = {
            "query": query,
            "fields": ["publication-number", "notice-title", "description-lot",
                       "buyer-name", "buyer-country", "classification-cpv",
                       "deadline-receipt-tender-date-lot", "publication-date"],
            "limit": 100,
            "page": page,
        }
        data = _post(payload)
        notices = data.get("notices") or []
        for raw in notices:
            item = _normalize(raw)
            if item and _is_open(item) and (not digital_only or _mentions_digital(item, title_only)):
                out.append(item)
        if len(notices) < 100:
            break
        page += 1
    return out


def _post(payload: dict) -> dict:
    """POST with a couple of retries – TED returns 429/5xx under load."""
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(config.TED_API_URL, json=payload, timeout=90)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise ValueError(f"TED API HTTP {resp.status_code}: {resp.text[:200]}")
            last_exc = ValueError(f"TED API HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(10 * attempt)
    raise last_exc or ValueError("TED API: no response")


def _normalize(raw: dict) -> dict | None:
    number = raw.get("publication-number")
    if not number:
        return None
    return {
        "publication_number": number,
        "title": _pick_lang(raw.get("notice-title")),
        "description": _pick_lang(raw.get("description-lot"))[:400],
        "buyer": _pick_lang(raw.get("buyer-name")),
        "country": (raw.get("buyer-country") or [""])[0],
        "cpv": sorted(set(raw.get("classification-cpv") or [])),
        "cpv_label": "",   # filled in once the group's CPVs are known
        "deadline": _first_date(raw.get("deadline-receipt-tender-date-lot")),
        "published": _first_date([raw.get("publication-date")]),
        # The human-readable notice page. It renders in a browser; the /pdf
        # variant is the machine-readable one.
        "url": f"https://ted.europa.eu/en/notice/-/detail/{number}",
    }


def _pick_lang(value) -> str:
    """The multilingual fields come back as {lang: str} or {lang: [str, …]}."""
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    for lang in (*LANG_PREFERENCE, *value.keys()):
        got = value.get(lang)
        if isinstance(got, list):
            got = " ".join(str(g) for g in got)
        if got:
            return str(got).strip()
    return ""


def _first_date(values) -> str:
    for v in values or []:
        if v:
            return str(v)[:10]
    return ""


def _is_open(item: dict) -> bool:
    """Keep a notice with a future deadline, and one with no deadline at all
    (prior information notices – an early signal worth seeing)."""
    if not item["deadline"]:
        return True
    return item["deadline"] >= dt.date.today().isoformat()


def _mentions_digital(item: dict, title_only: bool = False) -> bool:
    blob = item["title"] if title_only else f"{item['title']} {item['description']}"
    return any(k in blob.lower() for k in config.TED_DIGITAL_KEYWORDS)


def matched_cpvs(item: dict) -> list[str]:
    """The CPV codes that actually made this notice a candidate. A notice can
    carry a dozen codes, and the interesting one is rarely the first."""
    wanted = {code for g in config.TED_GROUPS for code in g["cpv"]}
    return [c for c in item["cpv"] if c in wanted]


def _is_core_training(item: dict) -> bool:
    """Is the notice ABOUT training, or does it just carry a training CPV on the
    side? A training code like 80533100 is attached to plenty of hardware and
    software purchases (medical equipment, spectrometers), so the CPV alone is a
    poor signal. TED builds its titles as
    "Country - <main CPV label> - <buyer's own title>", and that middle label is
    the main subject, so that is what decides."""
    parts = item["title"].split(" – ")
    label = parts[1].lower() if len(parts) >= 3 else ""
    return any(w in label for w in config.TED_TRAINING_TITLE_WORDS)


def _ranking_key(item: dict) -> tuple[int, str]:
    """Notices whose CPV is squarely IT training come first – otherwise a wave of
    hardware/licence procurements that merely carry a training code alongside
    would push the real training tenders past the MAX_CANDIDATES cut-off. Within
    a group, nearest deadline first; no deadline last."""
    return (0 if _is_core_training(item) else 1, item["deadline"] or "9999-12-31")
