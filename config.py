"""
Codecool Tender Watcher – configuration.

This is where you steer the focus of the search. You do NOT have to list the
websites to monitor: based on the company profile and the source portals, the AI
searches on its own and also discovers corporate procurement pages.

Note: COMPANY_PROFILE and SEARCH_SEGMENTS are injected verbatim into the model
prompt, so their text is deliberately kept in Hungarian.
"""

# --- Company profile (drives the relevance filtering) -----------------------
COMPANY_PROFILE = """
Cég: Codecool (codecool.com) – IT- és programozásoktatás, coding bootcamp.
Jelenlét: főként Magyarország és Közép-Kelet-Európa, de EGÉSZ EURÓPÁBAN vállal munkát.
Alaptevékenység: programozás- és digitális készségképzés, felnőtt- és szakképzés (VET),
átképzés / reskilling / upskilling, EdTech megoldások, e-learning.
Célterület a figyeléshez: a TELJES európai piac – minden EU-tagállam, továbbá UK, Norvégia,
Svájc. Minden típusú lehetőség érdekes: EU-s és nemzeti pályázatok, közbeszerzések
(állami, önkormányzati/városi), valamint magáncégek beszerzései / képzési tenderei.
Releváns kulcsszavak: digital skills, advanced digital skills, reskilling, upskilling,
vocational education and training (VET), programming / coding training, IT training,
corporate training, e-learning, EdTech, AI in education, AI training, micro-credentials,
felnőttképzés, informatikai képzés, digitális kompetencia, ajánlattételi felhívás,
request for proposal (RFP), invitation to tender, beszállítói pályázat.
"""

# --- Search segments ---------------------------------------------------------
# IMPORTANT: the portals listed below are only EXAMPLES, not an exhaustive list.
# The goal is to cover the whole European market – in every segment the AI is
# expected to discover further sources on its own (national, municipal and
# corporate procurement pages alike).
SEARCH_SEGMENTS = [
    "EU-s pályázatok és támogatások – pl. EU Funding & Tenders Portal (Digital Europe, ESF+, Horizon), "
    "Erasmus+ / EACEA (VET, KA2), Digital Skills and Jobs Platform",
    "Magyar pályázatok – pl. palyazat.gov.hu / Széchenyi Terv Plusz (DIMOP Plusz, EFOP Plusz), NKFIH",
    "Európai közbeszerzések, minden országból – pl. TED (ted.europa.eu), és a nemzeti portálok: "
    "EKR/kozbeszerzes.hu (HU), HILMA (FI), Mercell / Opic (SE/NO/DK), evergabe / DTVP (DE), "
    "BOAMP (FR), ANAC (IT), PLACE (ES), eZamówienia (PL), NEN (CZ), UVO (SK), e-licitatie (RO), "
    "PPA (görög KIMDIS / promitheus.gov.gr), Contracts Finder / Find a Tender (UK) – és bármely további nemzeti portál",
    "Városi / önkormányzati és közintézményi beszerzések – pl. Helsinki (hel.fi hankinnat), "
    "Bécs, Berlin, Amszterdam, Varsó, Budapest beszerzési oldalai, egyetemek, kamarák, "
    "munkaügyi hivatalok (pl. arbetsförmedlingen, Bundesagentur für Arbeit) képzési tenderei",
    "Céges / magánszektor tenderek – ezek gyakran 'ajánlattételi felhívás', 'RFP / request for proposal', "
    "'invitation to tender', 'beszállítói pályázat', 'Ausschreibung' címen jelennek meg. Helyek: "
    "nagyvállalatok saját supplier/procurement/hirdetmény oldalai (pl. bankok: UniCredit, Erste, OTP, "
    "Raiffeisen; telekom: Magyar Telekom, Vodafone, Deutsche Telekom; ipar: BASF, Siemens, Bosch; "
    "energetika: MOL, E.ON), publikus e-beszerzési platformok (SAP Ariba Discovery, Jaggaer, Coupa, "
    "tendigo, Mercell privát szekciói), ahol IT-képzést, reskilling/upskilling programot, "
    "digital academy szolgáltatást keresnek beszállítótól",
]

# --- Explicitly monitored sources -------------------------------------------
# Portals to watch on EVERY run. These are ENTRY POINTS, not results:
# the watcher must drill down from them to the individual call /
# notice page. The landing pages themselves are rejected by the link filter
# below, so they can never end up in a digest.
#
# "item_hint" tells the model what a concrete item URL looks like on that
# portal, so it knows when it has drilled down far enough.
MONITORED_SOURCES = [
    {
        "name": "EKR – közbeszerzési hirdetmények (HU)",
        "url": "https://ekr.gov.hu/portal/kozbeszerzes/hirdetmenyek",
        # Note: the EKR notice pages are a JavaScript app – search engines cannot
        # read them, so a concrete EKR link is rarely reachable. Hungarian
        # above-threshold notices are also published on TED, which IS readable.
        "item_hint": "egy konkrét eljárás oldala (ekr.gov.hu/eljarastar/eljaras/EKR<azonosító>); "
                     "ha az nem elérhető, ugyanannak az eljárásnak a TED-hirdetménye",
    },
    {
        "name": "TED – Tenders Electronic Daily (EU)",
        "url": "https://ted.europa.eu/hu/",
        "item_hint": "egy konkrét hirdetmény: ted.europa.eu/…/notice/<szám>-<év>",
    },
    {
        "name": "tendigo – Weiterbildung / képzési kiírások (DE)",
        "url": "https://tendigo.de/ausschreibungen/weiterbildung",
        "item_hint": "egy konkrét Ausschreibung aloldala, nem a 'weiterbildung' listaoldal",
    },
    {
        "name": "HADEA – Digital Europe call-bejelentések (EU)",
        "url": "https://hadea.ec.europa.eu/news/new-calls-proposals-under-digital-europe-programme-published-2026-04-10_en",
        "item_hint": "a hírben felsorolt EGYES call-ok saját oldala: hadea.ec.europa.eu/calls-proposals/… "
                     "vagy az EU Funding & Tenders Portal topic-details oldala",
    },
]

# Sources evaluated on 2026-09-16 and deliberately NOT added, so the question
# does not have to be re-researched:
#   - Közbeszerzési Értesítő (kozbeszerzes.hu/ertesito, /adatbazis/keres/hirdetmeny):
#     a real source, but its robots.txt disallows exactly those paths, so search
#     engines do not index them and a crawler would be going against the site's
#     stated wishes. Hungarian above-threshold procedures reach TED anyway.
#   - BOAMP (FR): has a proper open data API, but measured on 2026-09-16 it adds
#     little – of 20 open training notices, 11 were already on TED and the rest
#     were driving licences, fire-safety courses and catering.
#   - Bundesanzeiger (DE): the financial/legal gazette, not a procurement portal.
#   - Your Europe, Közbeszerzési Kisokos, ProcurCompEU, eProcurement Initiatives:
#     guides and policy pages, not opportunity sources – see GUIDE_PATH_PATTERNS.
#   - kozbeszerzes.khf.hu: a commercial monitoring service – an aggregator, and
#     this watcher is what it would be a paid substitute for.

# --- Link quality filter -----------------------------------------------------
# Aggregator, news and listing pages that do not point at
# ONE concrete opportunity must never be reported. This is enforced in code
# (tender_watcher.py -> reject_reason), not only in the prompt, because the
# model repeatedly ignored the soft instruction.

# Sites that only ever write ABOUT calls (grant-consultant blogs, tender news
# aggregators). Never a primary source – always dropped. Extend this list as
# new offenders show up in the "filtered out" section of the run log.
AGGREGATOR_DOMAINS = [
    "kozbeszerzes.khf.hu",   # commercial procurement-monitoring / BI service
    "palyazatmenedzser.hu",
    "palyaz.hu",
    "palyazatokabc.hu",
    "socialpro.hu",
    "dft.hu",
    "acridnetwork.com",
    "oferent.com.pl",
    "atlasprzetargow.pl",
    "it-ausschreibung.de",
    "openprocurements.com",
]

# Path fragments that mark a news / press / blog article rather than a call page.
# This is what drops e.g. hadea.ec.europa.eu/news/… – an official domain, but a
# news post that only announces that calls exist.
NEWS_PATH_PATTERNS = [
    "/news/", "/news-", "/latest/news", "/press", "/newsroom",
    "/hirek/", "/hir/", "/hirado", "/sajtokozlemeny", "/aktualitasok",
    "/blog/", "/article/", "/articles/", "/cikk/", "/nachrichten/", "/aktuelles/",
]

# Guide, rulebook and policy pages. They sit on impeccable official domains
# (europa.eu, kozbeszerzes.hu) and survive every other rule, yet they explain how
# procurement WORKS instead of naming one opportunity – the same complaint as
# with the aggregators. Seeded from a source list the client sent on 2026-09-16
# that was mostly made of these: Your Europe tendering rules, the Közbeszerzési
# Kisokos, ProcurCompEU, the Commission's eProcurement pages.
GUIDE_PATH_PATTERNS = [
    "youreurope", "/public-tendering-rules", "/search-bid-public-tender",
    "kisokos", "procurcompeu", "/digital-procurement", "/programme-guide",
    "/utmutato", "/tudastar", "/jogszabaly", "/szabalyoz", "/kisokos",
    "/guide/", "/guides/", "/faq", "/help/", "/how-to", "/leitfaden",
    "/ertesito",   # the gazette's own index page – a list of issues, not a notice
]

# Path segments that mark a search / category / listing page. Such a URL is only
# rejected when it carries NO item identifier (see has_identifier), so
# ".../ausschreibungen/weiterbildung" is dropped but ".../ausschreibungen/12345"
# is kept.
LISTING_PATH_KEYWORDS = {
    "ausschreibungen", "hirdetmenyek", "hirdetmeny", "kozbeszerzes",
    "przetargi", "tenders", "tender", "opportunities", "opportunity",
    "calls", "call-for-proposals", "calls-for-proposals", "palyazatok",
    "search", "kereses", "suche", "recherche", "szukaj",
    "kategoria", "kategorie", "category", "branza", "keyword", "cimke", "tag",
    "buyer", "buyers", "list", "lista", "deadlines", "archive", "archivum",
}

# An EU-level call must be reported from its OWN official page. A national
# contact point's or a consultant's summary of the same call is second-hand –
# same complaint as with the aggregators, just on a respectable domain. This is
# what rejects e.g. www.ffg.at/en/europe/dep/calls/SO4_2026_2 (the Austrian NCP
# writing about DIGITAL-2026-SKILLS-10) in favour of the HaDEA / Funding &
# Tenders Portal page for the same call.
OFFICIAL_EU_DOMAINS = ["europa.eu"]   # covers ec.europa.eu, hadea.ec.europa.eu, eacea…

# Call identifiers of EU programmes. A result carrying one of these is an
# EU-level call whatever the model put in "category", so it must live on an
# official domain.
EU_CALL_ID_PATTERNS = [
    r"\bDIGITAL-20\d\d-", r"\bERASMUS-[A-Z]+-20\d\d-", r"\bHORIZON-",
    r"\bCERV-20\d\d-", r"\bLIFE-20\d\d-", r"\bCEF-20\d\d-", r"\bEU4H-20\d\d-",
]

# Programme names. These only count together with category == "eu" – on their own
# they would also catch a national call co-financed by the programme, which is
# legitimately reported from its national page.
EU_PROGRAMME_MARKERS = [
    "digital europe programme", "erasmus+", "erasmus plus", "horizon europe",
    "creative europe", "eacea", "hadea", "esf+", "european social fund plus",
]

# Two-letter language prefixes, so that e.g. https://ted.europa.eu/hu/ counts as
# a portal homepage rather than as a specific page.
LANG_SEGMENTS = {
    "en", "hu", "de", "fr", "it", "es", "pl", "cs", "sk", "ro", "fi", "sv",
    "no", "da", "nl", "pt", "el", "bg", "hr", "sl", "et", "lv", "lt", "ga", "mt",
}

# --- TED direct API ----------------------------------------------------------
# TED is queried, not searched: see ted_source.py for why. The model's web
# searches are freed up for the segments that have no API.
TED_API_URL = "https://api.ted.europa.eu/v3/notices/search"
TED_LOOKBACK_DAYS = 30         # how far back to look for notices
TED_MAX_CANDIDATES = 40        # how many open notices are handed to the model
TED_MAX_PAGES = 8              # safety stop on paging (100 notices per page)

# Only open opportunities: contract notices, prior information and qualification
# systems. Award notices (can-*) are already decided, so they are excluded.
TED_NOTICE_TYPES = ["cn-standard", "cn-social", "pin-only", "qu-sy"]

# CPV codes that ARE digital/IT training – every open notice counts as a candidate.
TED_CPV_IT_TRAINING = [
    "80420000",   # e-learning services
    "80533000",   # computer-user training
    "80533100",   # computer training services
    "80533200",   # computer courses
    "80531200",   # technical training services
]

# Broader training CPVs – huge volume (driving schools, fire safety, language
# courses), so a notice here only counts if its text mentions something digital.
TED_CPV_GENERAL_TRAINING = [
    "80400000",   # adult and other education services
    "80500000",   # training services
    "80510000",   # specialist training services
    "80511000",   # staff training services
    "80530000",   # vocational training services
    "80532000",   # management training services
]

# TED titles read "Country - <main CPV label> - <buyer's own title>", and we ask
# for the Hungarian rendering, so these words in the middle label mark a notice
# that is genuinely ABOUT training rather than one that merely carries a
# training CPV next to a hardware purchase.
TED_TRAINING_TITLE_WORDS = ["képzés", "oktatás", "tanfolyam", "továbbképz", "e-learning", "tananyag"]

# Multilingual – the notice title/description is in the buyer's own language.
TED_DIGITAL_KEYWORDS = [
    "digital", "digitál", "digitale", "digitalis", "cyfrow", "numérique", "numerique",
    "informati", "informatyk", "it-", " it ", "ict", "computer", "komputer",
    "számítógép", "szoftver", "software", "programoz", "programming", "programista",
    "coding", "kódol", "e-learning", "elearning", "online", "webfejleszt", "web development",
    "cyber", "kiber", "cyberbezpiecz", "adatbázis", "database", "cloud", "felhő",
    "mesterséges intelligencia", "artificial intelligence", " ai ", "edv", "schulung it",
]

# --- OpenRouter / model / run settings ---------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = "anthropic/claude-sonnet-5"   # good value for money; for something stronger use e.g. "anthropic/claude-opus-4.5"

# Web search (openrouter:web_search server tool) settings:
MAX_RESULTS_PER_SEARCH = 5     # max. results per single search (Exa engine); 1–25
MAX_SEARCHES = 12              # how many searches the model may run in one pass (max_uses)
                               # Measured: 12 searches = 204k prompt tokens / $0.67 per run,
                               # 16 = 389k / $1.05. The results do not get better with 16 – the
                               # search results pile up in the context, so cost grows faster than
                               # the search count and the model's synthesis gets NARROWER, not
                               # wider. Do not raise this without measuring the item count too.
MAX_TOTAL_RESULTS = 60         # upper bound on all results in one pass (cost / context limit)
                               # 12 searches × 5 results – needed for full market coverage; lower it if too expensive

MIN_RELEVANCE = "med"          # "low" | "med" | "high" – anything below this is not reported in notifications
