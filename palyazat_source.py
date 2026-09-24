"""
palyazat.gov.hu – direct API access to Hungarian grant calls (Széchenyi Terv
Plusz: DIMOP Plusz, GINOP Plusz, EFOP Plusz …, plus NKFIA and the other
programmes the portal carries).
"""

import datetime as dt
import time
from zoneinfo import ZoneInfo

import requests

import config

PAGE_SIZE = 100
BUDAPEST = ZoneInfo("Europe/Budapest")

# The headers the portal's own front-end sends; without them the API answers 500.
HEADERS = {
    "Content-Type": "application/json",
    "application-name": "FairApp",
    "device-id": "40b0c32c-77fe-4380-9f5e-be96ae24fabd",
    "Origin": "https://www.palyazat.gov.hu",
    "Referer": "https://www.palyazat.gov.hu/",
}


def fetch_candidates() -> list[dict]:
    """Active Hungarian calls that fit Codecool, nearest deadline first.
    Never raises – a dead portal must not kill the weekly run."""
    try:
        raw = _fetch_open()
    except (requests.RequestException, ValueError) as exc:
        print(f"palyazat.gov.hu unavailable ({exc}) – skipped.")
        return []

    active = [r for r in raw if r.get("status") == "Aktív"]
    relevant = [item for item in (_normalize(r) for r in active) if item and _relevant(item)]
    relevant.sort(key=lambda i: i["deadline"])

    candidates, unrouted = [], []
    for item in relevant:
        if len(candidates) >= config.PALYAZAT_MAX_CANDIDATES:
            break
        route = _route(item["publication_number"])
        if route:
            item["url"] = f"https://www.palyazat.gov.hu/programok/{route}"
            item["group"] = "magyar pályázat (palyazat.gov.hu)"
            item["category"] = "hu"
            candidates.append(item)
        else:
            unrouted.append(item["publication_number"])

    print(f"palyazat.gov.hu: {len(raw)} not yet closed ({len(active)} active), "
          f"{len(relevant)} relevant, {len(candidates)} handed over "
          f"(quota {config.PALYAZAT_MAX_CANDIDATES}).")
    if unrouted:
        print(f"  no call page for: {', '.join(unrouted)} – left out.")
    return candidates


def _fetch_open() -> list[dict]:
    """Newest end date first, so paging can stop at the first expired call."""
    today = dt.date.today().isoformat()
    out: list[dict] = []
    for page in range(config.PALYAZAT_MAX_PAGES):
        body = {
            "pagination": {"pageSize": PAGE_SIZE, "pageIndex": page},
            "filtering": {"exactFilters": []},
            "sort": {"direction": "desc", "field": "endTime"},
        }
        batch = _request("POST", "/papi/tenders/list", json=body).get("tenders") or []
        out.extend(r for r in batch if _local_date(r.get("endTime")) >= today)
        if len(batch) < PAGE_SIZE or _local_date(batch[-1].get("endTime")) < today:
            break
    return out


def _route(code: str) -> str:
    try:
        return _request("GET", "/operational-map/call-for-applications-route",
                        params={"code": code}).get("route") or ""
    except (requests.RequestException, ValueError):
        return ""


def _request(method: str, path: str, **kwargs) -> dict:
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.request(method, config.PALYAZAT_API_URL + path,
                                    headers=HEADERS, timeout=60, **kwargs)
            if resp.status_code in (200, 201):
                return resp.json()
            if resp.status_code == 404:
                return {}
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            last_exc = ValueError(f"HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(5 * attempt)
    raise last_exc or ValueError("no response")


def _local_date(stamp: str | None) -> str:
    """End times are stored as UTC midnight-minus-one-hour ("2026-10-26T22:00Z"
    is 27 October in Budapest), so the date must be taken in local time."""
    if not stamp:
        return ""
    moment = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return moment.astimezone(BUDAPEST).date().isoformat()


def _normalize(raw: dict) -> dict | None:
    code = raw.get("code")
    if not code:
        return None
    return {
        "publication_number": code,
        "title": str(raw.get("name") or "").strip(),
        "description": " ".join(str(raw.get("supportPurpose") or "").split())[:500],
        "programme": raw.get("operationalProgram") or raw.get("developmentalProgram") or "",
        "beneficiaries": ", ".join(raw.get("beneficiaries") or []),
        "form": str(raw.get("formOfSupport") or ""),
        "opens": _local_date(raw.get("startTime")),
        "deadline": _local_date(raw.get("endTime")),
        "budget": _budget(raw),
        "url": "",   # filled in from the route API
    }


def _budget(raw: dict) -> str:
    total = raw.get("sumAvailableSupportAmount") or 0
    lo, hi = raw.get("minSupportAmount") or 0, raw.get("maxSupportAmount") or 0
    parts = []
    if total:
        parts.append(f"{total:,.0f} Ft keret".replace(",", " "))
    if hi:
        parts.append(f"{lo:,.0f}–{hi:,.0f} Ft / projekt".replace(",", " "))
    return ", ".join(parts)


def _relevant(item: dict) -> bool:
    """Drop what Codecool Kft. cannot apply to: calls open only to public bodies
    (border management, water works – a third of the active list), and the
    financial-intermediary plumbing (loan facilities, cost reimbursement of fund
    managers, venture capital). Then keep what mentions digital, training, R&D
    or labour-market content."""
    if "vállalkozás" not in item["beneficiaries"].lower():
        return False
    title = item["title"].lower()
    if any(x in title for x in config.PALYAZAT_EXCLUDE_WORDS):
        return False
    blob = f"{title} {item['description'].lower()}"
    return any(k in blob for k in config.PALYAZAT_KEYWORDS)
