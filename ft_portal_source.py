"""
EU Funding & Tenders Portal – direct API access to EU grant calls.
"""

import datetime as dt
import html
import json
import re
import time

import requests

import config

PAGE_SIZE = 100

# SEDIA codes. type: 1 = call topic, 2 = call for tenders, 8 = cascade funding
# (a project's own open call, e.g. Eurostars or the EU Code Week small grants).
# status: 31094501 = forthcoming, 31094502 = open.
TOPIC_TYPES = ["1", "2", "8"]
OPEN_STATUSES = ["31094501", "31094502"]

TAG_RE = re.compile(r"<[^>]+>")


def fetch_candidates() -> list[dict]:
    """Open EU calls that fit Codecool, best match first.

    Never raises: a dead portal must not kill the weekly run."""
    try:
        raw = _fetch_all()
    except (requests.RequestException, ValueError) as exc:
        print(f"EU Funding & Tenders Portal unavailable ({exc}) – skipped.")
        return []

    today = dt.date.today().isoformat()
    found: dict[str, dict] = {}
    for r in raw:
        item = _normalize(r, today)
        if item and _relevant(item):
            # Keyed by URL, not identifier: cascade calls of one project share
            # the identifier (DIGITAL-2022-SKILLS-03-…) but are separate calls.
            if item["url"] in found:
                _merge(found[item["url"]], item)
            else:
                found[item["url"]] = item

    for item in found.values():
        item["group"] = "EU-s pályázat (Funding & Tenders Portal)"
        item["category"] = "eu"
        item["must_report"] = _is_must_report(item)

    # Must-report calls ride outside the quota: a call on the watch list must
    # never lose its slot to a better keyword score.
    ranked = sorted(found.values(), key=_ranking_key)
    must = [c for c in ranked if c["must_report"]]
    rest = [c for c in ranked if not c["must_report"]]
    candidates = must + rest[:max(0, config.FT_MAX_CANDIDATES - len(must))]
    print(f"EU Funding & Tenders Portal: {len(raw)} open/forthcoming topics, "
          f"{len(found)} relevant, {len(candidates)} handed over "
          f"({len(must)} must-report, quota {config.FT_MAX_CANDIDATES}).")
    return candidates


def _merge(kept: dict, other: dict) -> None:
    calls = kept.setdefault("calls", [(kept["title"], kept["deadline"])])
    calls.append((other["title"], other["deadline"]))
    calls.sort(key=lambda c: c[1])
    kept["title"] = " / ".join(t for t, _ in calls)
    kept["deadline"] = calls[0][1]
    kept["deadline_text"] = "; ".join(f"{t}: {d}" for t, d in calls)
    kept["description"] = (kept["description"] + " " + other["description"]).strip()[:3000]


def _is_must_report(item: dict) -> bool:
    return any(re.search(p, item["publication_number"]) for p in config.FT_MUST_REPORT_PATTERNS)


def _fetch_all() -> list[dict]:
    query = {"bool": {"must": [
        {"terms": {"type": TOPIC_TYPES}},
        {"terms": {"status": OPEN_STATUSES}},
    ]}}
    out: list[dict] = []
    for page in range(1, config.FT_MAX_PAGES + 1):
        batch = _post(query, page)
        out.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    return out


def _post(query: dict, page: int) -> list[dict]:
    params = {"apiKey": "SEDIA", "text": "***", "pageSize": PAGE_SIZE, "pageNumber": page}
    files = {
        "query": ("query", json.dumps(query), "application/json"),
        "languages": ("languages", '["en"]', "application/json"),
        "sort": ("sort", json.dumps({"field": "identifier", "order": "ASC"}), "application/json"),
    }
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(config.FT_API_URL, params=params, files=files, timeout=90)
            if resp.status_code == 200:
                return resp.json().get("results") or []
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            last_exc = ValueError(f"HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(10 * attempt)
    raise last_exc or ValueError("no response")


def _first(meta: dict, key: str) -> str:
    values = meta.get(key) or [""]
    return str(values[0]) if values else ""


def _clean(text: str) -> str:
    return " ".join(TAG_RE.sub(" ", html.unescape(text or "")).split())


def _normalize(raw: dict, today: str) -> dict | None:
    meta = raw.get("metadata") or {}
    url = raw.get("url") or ""
    identifier = _first(meta, "identifier")
    # Multi-stage and cut-off calls carry several dates: the next one counts.
    deadlines = sorted(d[:10] for d in (meta.get("deadlineDate") or []) if d and d[:10] >= today)
    if not url or not identifier or not deadlines:
        return None
    return {
        "publication_number": identifier,
        "title": _clean(raw.get("summary") or _first(meta, "title")),
        "call_title": _clean(_first(meta, "callTitle")),
        "description": _clean(_first(meta, "descriptionByte"))[:3000],
        "programme": identifier.split("-")[0],
        "status": "nyitott" if _first(meta, "status") == "31094502" else "hamarosan nyílik",
        "opens": _first(meta, "startDate")[:10],
        "deadline": deadlines[0],
        "budget": _budget(meta, identifier),
        "url": url,
    }


def _budget(meta: dict, identifier: str) -> str:
    """The topic's own line from the call-level budget table, e.g.
    "10 000 000 EUR összesen, 3 000 000–5 000 000 EUR / projekt"."""
    try:
        table = json.loads(_first(meta, "budgetOverview") or "{}")
    except ValueError:
        return ""
    for actions in (table.get("budgetTopicActionMap") or {}).values():
        for action in actions:
            if not str(action.get("action", "")).startswith(identifier):
                continue
            total = sum(float(v or 0) for v in (action.get("budgetYearMap") or {}).values())
            lo, hi = action.get("minContribution") or 0, action.get("maxContribution") or 0
            parts = []
            if total:
                parts.append(f"{total:,.0f} EUR összesen".replace(",", " "))
            if hi:
                span = f"{lo:,.0f}–{hi:,.0f}" if lo and lo != hi else f"{hi:,.0f}"
                parts.append(f"{span} EUR / projekt".replace(",", " "))
            return ", ".join(parts)
    return ""


def _head(item: dict) -> str:
    return f" {item['title']} {item['call_title']} ".lower()


def _is_priority(item: dict) -> bool:
    return any(re.search(p, item["publication_number"]) for p in config.FT_PRIORITY_PATTERNS)


def _score(item: dict) -> int:
    """Keyword hits, counted three times over when they are in the title – the
    descriptions are long and mention "skills" and "training" in passing even
    in a shipping or agriculture topic."""
    head, desc = _head(item), item["description"].lower()
    return sum(3 * (k in head) + (k in desc) for k in config.FT_KEYWORDS)


def _relevant(item: dict) -> bool:
    """Programme whitelist first (Horizon has 400+ open topics, most of them on
    batteries and fisheries), then no student-mobility schemes, then either a
    priority call or at least one keyword."""
    if not any(re.search(p, item["publication_number"]) for p in config.FT_PROGRAMME_PATTERNS):
        return False
    if any(x in _head(item) for x in config.FT_EXCLUDE_WORDS):
        return False
    return _is_priority(item) or _score(item) > 0


def _ranking_key(item: dict) -> tuple[int, int, str]:
    """Priority calls first, then the best keyword match, then nearest deadline."""
    return (0 if _is_priority(item) else 1, -_score(item), item["deadline"])
