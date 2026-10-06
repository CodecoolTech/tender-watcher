"""
EKR (ekr.gov.hu) – direct API access to Hungarian public procurement.

Why this module exists: EKR was a monitored web-search source, but its pages
are a JavaScript app, so the model's searches never reached a concrete
procedure. Above-threshold Hungarian procedures still came in through TED, the
national (below-EU-threshold) ones did not – measured on 2026-10-06, 159 of the
374 open EKR notices had no TED id at all.

The portal's notice list loads from a public JSON endpoint that needs no key:
  GET /api/publikus/kozbeszerzesi-hirdetmenyek?hirdetmenyKozzetetelDatumaKezdet=…
      &eljarasAjanlatteteliHataridoKezdet=…&tartalombanSzereploSzavak=…&oldal=…
Paging starts at 1, `elemszam` is honoured up to 100, and the dates must be in
the frontend's own format (2026-09-06T00:00:00.000+0000) or the API answers 500.

CPV codes are matched with the full-text filter (tartalombanSzereploSzavak),
not with the portal's CPV filter (eljarasCPVkodok): that one answered 0 hits
for every top-level code – construction included – and HTTP 500 for every
sub-code. Neither the list nor the notice detail carries the CPV codes, so the
full-text search over the notice body is the only way to select by CPV.

The procedure page (ekr.gov.hu/eljarastar/eljaras/EKR…) is what the portal
itself links a notice to, and it is readable without logging in.
"""

import datetime as dt
import time

import requests

import config

PAGE_SIZE = 100
GROUP_LABEL = "magyar közbeszerzés (EKR)"


def fetch_candidates(skip_ted: set[str] = frozenset()) -> list[dict]:
    """Open Hungarian procedures matching the TED_GROUPS CPV codes, nearest
    deadline first. `skip_ted` holds the TED publication numbers already handed
    over, so an above-threshold procedure is not listed twice.

    Never raises – EKR being down must not kill the weekly run."""
    found: dict[str, dict] = {}
    failed = 0
    for group in config.TED_GROUPS:
        for cpv in group["cpv"]:
            try:
                notices = _search(cpv)
            except (requests.RequestException, ValueError) as exc:
                print(f"EKR CPV {cpv} unavailable ({exc}) – skipped.")
                failed += 1
                continue
            for raw in notices:
                item = _normalize(raw)
                if not item or not _is_call_for_tenders(raw) or not _is_open(item):
                    continue
                if group["digital_only"] and not _mentions_digital(item):
                    continue
                kept = found.setdefault(item["publication_number"], item)
                if cpv not in kept["cpv"]:
                    kept["cpv"].append(cpv)

    total_cpvs = sum(len(g["cpv"]) for g in config.TED_GROUPS)
    if failed == total_cpvs:
        print("EKR unavailable – this run continues without Hungarian EKR procedures.")
        return []
    if not found:
        print("EKR: no open procedure matched.")
        return []

    fresh = [c for c in found.values() if c["ted_number"] not in skip_ted]
    candidates = sorted(fresh, key=_ranking_key)[:config.EKR_MAX_CANDIDATES]
    for c in candidates:
        c["group"] = GROUP_LABEL
        c["cpv_label"] = ", ".join(c["cpv"])
    print(f"EKR · magyar közbeszerzés: {len(found)} open, "
          f"{len(found) - len(fresh)} already on TED, "
          f"{len(candidates)} handed over (quota {config.EKR_MAX_CANDIDATES}).")
    return candidates


def _search(cpv: str) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=config.EKR_LOOKBACK_DAYS)
    out: list[dict] = []
    for page in range(1, config.EKR_MAX_PAGES + 1):
        params = {
            "hirdetmenyKozzetetelDatumaKezdet": _api_time(since),
            "eljarasAjanlatteteliHataridoKezdet": _api_time(now),
            "tartalombanSzereploSzavak": cpv,
            "elemszam": PAGE_SIZE,
            "oldal": page,
        }
        data = _get(params)
        batch = data.get("lista") or []
        out.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    return out


def _api_time(moment: dt.datetime) -> str:
    """The frontend's BACKEND_API_DATE_TIME_FORMAT: YYYY-MM-DDTHH:mm:ss.SSSZZ."""
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def _get(params: dict) -> dict:
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(config.EKR_API_URL, params=params, timeout=60,
                                headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, dict) else {}
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise ValueError(f"HTTP {resp.status_code}")
            last_exc = ValueError(f"HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < 3:
            time.sleep(5 * attempt)
    raise last_exc or ValueError("no response")


def _normalize(raw: dict) -> dict | None:
    procedure = raw.get("eljarasTechnikaiAzonosito") or \
        str(raw.get("hirdetmenyEKRazonosito") or "").split("/")[0]
    if not procedure:
        return None
    ted = str(raw.get("tedAzonosito") or "")
    return {
        "publication_number": procedure,
        "title": str(raw.get("eljarasTargya") or "").strip(),
        "description": "",
        "buyer": str(raw.get("ajanlatkeroNeve") or "").strip(),
        "country": "HUN",
        "cpv": [],
        "cpv_label": "",
        "deadline": _local_date(raw.get("eljarasAjanlatteteliHatarido")),
        "published": _local_date(raw.get("hirdetmenyKozzetetelDatuma")),
        "notice_type": str(raw.get("hirdetmenyTipusa") or ""),
        "ted_number": ted.lstrip("0"),
        "below_eu_threshold": not ted,
        "url": f"https://ekr.gov.hu/eljarastar/eljaras/{procedure}",
    }


def _local_date(value) -> str:
    """EKR stores Budapest midnight as 22:00/23:00 UTC of the previous day, so
    the UTC date would be a day early. A fixed +2h is enough to land on the
    right calendar day both in summer (CEST) and in winter (CET)."""
    if not value:
        return ""
    try:
        moment = dt.datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return str(value)[:10]
    return (moment + dt.timedelta(hours=2)).date().isoformat()


def _is_call_for_tenders(raw: dict) -> bool:
    kind = str(raw.get("hirdetmenyTipusa") or "").lower()
    return any(w in kind for w in config.EKR_NOTICE_TYPE_WORDS)


def _is_open(item: dict) -> bool:
    return bool(item["deadline"]) and item["deadline"] >= dt.date.today().isoformat()


def _mentions_digital(item: dict) -> bool:
    """For the broad training CPVs only: the subject line must say it is
    digital. EKR gives no description in the list, so the title decides."""
    return any(k in item["title"].lower() for k in config.TED_DIGITAL_KEYWORDS)


def _ranking_key(item: dict) -> tuple[int, str]:
    """National (below-threshold) procedures first – TED never shows those, so
    they are what this source adds. Within that, nearest deadline first."""
    return (0 if item["below_eu_threshold"] else 1, item["deadline"])
