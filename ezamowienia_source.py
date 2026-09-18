"""
e-Zamówienia (ezamowienia.gov.pl) – direct API access to Polish procurement.

Why a second source module: TED only carries notices above the EU threshold.
Poland is a real market for Codecool (Motorola Academy, Pomorskie, IT's
possible), and measured on 2026-09-18 practically every open Polish training
notice in this API was flagged `isTenderAmountBelowEU` – meaning TED never
sees it. This module closes that gap.

The API is public and needs no key:
  GET /mo-board/api/v1/Board/Search?CpvCode=…&PublicationDateFrom=…&Page=…
It returns at most 10 records per page regardless of PageSize, so it is paged.

The two other Polish portals that were suggested are NOT fetched here:
  - Baza Konkurencyjności: every /api/ endpoint answers 401 behind Keycloak and
    the swagger URL just serves the SPA shell, so there is no documented public
    interface to build on.
  - platformazakupowa.pl: no API, and its robots.txt asks for a 900-second
    crawl delay; its notices also largely reappear in the BZP feed this module
    already reads.
Both are covered as web-search entry points in config.MONITORED_SOURCES.
"""

import datetime as dt
import time

import requests

import config

PAGE_SIZE = 10          # the API's hard ceiling, whatever PageSize is sent


def fetch_candidates() -> list[dict]:
    """Open Polish notices matching the training CPV codes, nearest deadline
    first. Never raises – a dead portal must not kill the weekly run."""
    found: dict[str, dict] = {}
    for cpv in config.EZAM_CPV_CODES:
        try:
            for raw in _search_cpv(cpv):
                item = _normalize(raw)
                if item and _is_open(item) and _relevant(item):
                    found.setdefault(item["publication_number"], item)
        except (requests.RequestException, ValueError) as exc:
            print(f"e-Zamówienia CPV {cpv} unavailable ({exc}) – skipped.")
            continue

    if not found:
        print("e-Zamówienia: no open notice matched.")
        return []
    candidates = sorted(found.values(), key=lambda i: i["deadline"] or "9999-12-31")
    if len(candidates) > config.EZAM_MAX_CANDIDATES:
        candidates = candidates[:config.EZAM_MAX_CANDIDATES]
    print(f"e-Zamówienia · lengyel közbeszerzés: {len(found)} open, "
          f"{len(candidates)} handed over (quota {config.EZAM_MAX_CANDIDATES}).")
    for c in candidates:
        c["group"] = "lengyel közbeszerzés (e-Zamówienia)"
    return candidates


def _search_cpv(cpv: str) -> list[dict]:
    since = (dt.date.today() - dt.timedelta(days=config.EZAM_LOOKBACK_DAYS)).isoformat()
    out: list[dict] = []
    for page in range(1, config.EZAM_MAX_PAGES + 1):
        params = {
            "CpvCode": cpv,
            "PublicationDateFrom": since,
            "SortingColumnName": "PublicationDate",
            "SortingDirection": "DESC",
            "PageSize": PAGE_SIZE,
            "Page": page,
        }
        batch = _get(params)
        out.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    return out


def _get(params: dict) -> list[dict]:
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(config.EZAM_API_URL, params=params, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else []
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise ValueError(f"HTTP {resp.status_code}")
            last_exc = ValueError(f"HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(5 * attempt)
    raise last_exc or ValueError("no response")


def _normalize(raw: dict) -> dict | None:
    number = raw.get("noticeNumber") or raw.get("bzpNumber")
    tender_id = raw.get("tenderId")
    if not number or not tender_id:
        return None
    return {
        "publication_number": str(number),
        "title": str(raw.get("orderObject") or "").strip(),
        "description": "",
        "buyer": str(raw.get("organizationName") or "").strip(),
        "country": "POL",
        "cpv_label": str(raw.get("cpvCode") or "")[:120],
        "deadline": str(raw.get("submittingOffersDate") or "")[:10],
        "published": str(raw.get("publicationDate") or "")[:10],
        "below_eu_threshold": bool(raw.get("isTenderAmountBelowEU")),
        "url": f"https://ezamowienia.gov.pl/mp-client/search/list/{tender_id}",
    }


def _is_open(item: dict) -> bool:
    return bool(item["deadline"]) and item["deadline"] >= dt.date.today().isoformat()


def _relevant(item: dict) -> bool:
    """Two tests, both on the subject line, because one alone is not enough:
    the CPV groups carry barber courses and excavator training (so it must be
    digital), and they are also bolted onto hardware and IT system rollouts
    (so it must actually be training)."""
    blob = f"{item['title']} {item['cpv_label']}".lower()
    digital = any(k in blob for k in config.TED_DIGITAL_KEYWORDS + config.EZAM_EXTRA_KEYWORDS)
    training = any(k in item["title"].lower() for k in config.EZAM_TRAINING_WORDS)
    return digital and training
