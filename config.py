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
Cég: Codecool Kft. (codecool.com) – 2014-ben alapított, budapesti székhelyű, magántulajdonú
oktatási vállalatcsoport; a közép-kelet-európai régió egyik vezető felnőtt IT- és
digitáliskészség-fejlesztő szereplője. Magyar felnőttképzési engedéllyel rendelkezik,
2020 óta E&Y által auditált. 100+ szakértő és tréner, 10+ év működés.

MIT CSINÁL – NÉGY SZOLGÁLTATÁSI ÁG, MINDEGYIK ÖNÁLLÓ LEHETŐSÉGFORRÁS:
 1. Képzés, át- és továbbképzés (reskilling / upskilling): 60+ kurzus, 20+ tanulási útvonal,
    az 1–5 napos szaktanfolyamtól a 12 hónapos, ~1000 órás full-stack átképzésig.
    Online, jelenléti és hibrid formában, helyi nyelveken is.
 2. E-learning tananyagfejlesztés és LMS: saját fejlesztésű, AI-támogatott tanulásirányítási
    rendszer (Journey), valamint önállóan és oktató által vezetett digitális tananyagok
    gyártása megrendelésre.
 3. Készségfelmérés és képzési tanácsadás: kompetenciamátrix kidolgozása, skills gap analízis,
    rövid és hosszú távú képzési terv, digitális érettség felmérése, megvalósíthatósági
    tanulmány, mikrotanúsítványok kibocsátása (egyetemi kreditrendszerrel kompatibilisen).
 4. IT-toborzás és munkaerő-biztosítás: szakember-kiválasztás, munkaerő-kölcsönzés, valamint
    toborzást és képzést egyben nyújtó vállalati akadémia-programok.

SZAKTERÜLETEK: mesterséges intelligencia és gépi tanulás, adat és analitika, felhő (AWS,
Azure), DevOps (Docker, Kubernetes, Terraform, CI/CD, Ansible, Jenkins), kiberbiztonság,
full-stack szoftverfejlesztés (Java, Python, JavaScript, React, C#, C++, PHP, Go),
szoftvertesztelés (manuális és automata), UX/UI, low-code / no-code, Salesforce,
IT-projektmenedzsment. Az AI készségszintű használata minden képzésbe integrált.

CÉLCSOPORTOK – NEM CSAK IT-SEK: informatikusok és fejlesztők; nem-IKT munkatársak tömeges
digitális alapkészség-fejlesztése (akár több ezer fő); C-szintű vezetők digitális
felkészítése; munkanélküliek és pályamódosítók átképzése; hátrányos helyzetű csoportok,
fogyatékossággal élők, nők IT-pályára segítése. Ezért a LAKOSSÁGI / ÁLLAMPOLGÁRI digitális
alapkészség-programok is relevánsak, nem csak a szakmai IT-képzés.

FÖLDRAJZ: budapesti székhely; a közép-kelet-európai régióban (Magyarország, Románia,
Lengyelország, Szlovákia, Csehország, Bulgária, Horvátország, Szlovénia, Ukrajna, Baltikum)
rendszeres működés, összesen 14+ országban dolgozott már. Egész Európában vállal munkát, a
régión kívül jellemzően helyi partnerrel vagy konzorciumi tagként.

REFERENCIÁK (ezek mutatják, milyen kiírásra hiteles az ajánlata): Innovációs és Technológiai
Minisztérium átképzési programjai (750, illetve 400 fő); GINOP Plusz-3.2.1 munkavállalói
készségfejlesztés; NKFIH K+F projektek (2020-1.1.2-PIACI-KFI, 2023-1.1.1-PIACI_FÓKUSZ);
European Software Skills Alliance – Erasmus+ konzorcium 21+ partnerrel; Google.org / Centre
for Public Impact AI-program 10 országban, 4100 fő; Motorola Solutions Akadémia
(Lengyelország, 7 kiadás); Citibank kiberbiztonsági átképzés; MBH Bank (3000 fő nem-IKT
program, egyetemi együttműködésben); DSK Bank vezetői digitális akadémia (Bulgária);
Pomorskie regionális fejlesztési ügynökség (140 fejlesztő képzése).

TIPIKUS MÉRET: 10 fős vezetői csoporttól 4100 fős országos programig; 200–1000 képzési óra;
néhány tízezer eurótól több százezer eurós szerződésig. Fővállalkozóként és konzorciumi
partnerként is tud pályázni.
"""

# --- Search segments ---------------------------------------------------------
# IMPORTANT: the portals listed below are only EXAMPLES, not an exhaustive list.
# The goal is to cover the whole European market – in every segment the AI is
# expected to discover further sources on its own (national, municipal and
# corporate procurement pages alike).
#
# Note on the division of labour: European public procurement now arrives
# through the TED API (ted_source.py), so these segments are what the model's
# web searches are FOR – grants, corporate tenders and below-threshold national
# notices, which TED does not carry.
#
# Segments 6-8 were added on 2026-09-17 from the company intro documents: they
# are service lines Codecool sells but the watcher was not looking for.
SEARCH_SEGMENTS = [
    "EU-s pályázatok és támogatások – pl. EU Funding & Tenders Portal (Digital Europe, ESF+, Horizon), "
    "Erasmus+ / EACEA (VET, KA2), Digital Skills and Jobs Platform. Konzorciumi partnert kereső "
    "felhívások is érdekesek (a Codecool az ESSA-ban is konzorciumi tag volt)",
    "Magyar pályázatok – pl. palyazat.gov.hu / Széchenyi Terv Plusz (DIMOP Plusz, EFOP Plusz), "
    "valamint KUTATÁS-FEJLESZTÉSI és innovációs pályázatok: NKFIH, PIACI-KFI, PIACI FÓKUSZ típusú "
    "kiírások – a Codecoolnak két ilyen futó/lezárt K+F projektje is van (oktatási platform, MI-fejlesztés)",
    "Európai közbeszerzések, minden országból – a TED-et az API már lefedi, ezért ITT a nemzeti, "
    "értékhatár alatti portálokra koncentrálj: HILMA (FI), Mercell / Opic (SE/NO/DK), evergabe / DTVP (DE), "
    "BOAMP (FR), ANAC (IT), PLACE (ES), eZamówienia (PL), NEN (CZ), UVO (SK), e-licitatie (RO), "
    "promitheus.gov.gr (GR), Contracts Finder / Find a Tender (UK) – és bármely további nemzeti portál",
    "Városi / önkormányzati és közintézményi beszerzések – pl. Helsinki (hel.fi hankinnat), "
    "Bécs, Berlin, Amszterdam, Varsó, Budapest beszerzési oldalai, egyetemek, kamarák, "
    "munkaügyi hivatalok (pl. arbetsförmedlingen, Bundesagentur für Arbeit) képzési tenderei, "
    "valamint regionális fejlesztési ügynökségek munkaerőpiaci képzési programjai",
    "Céges / magánszektor tenderek – ezek gyakran 'ajánlattételi felhívás', 'RFP / request for proposal', "
    "'invitation to tender', 'beszállítói pályázat', 'Ausschreibung' címen jelennek meg. Helyek: "
    "nagyvállalatok saját supplier/procurement/hirdetmény oldalai (pl. bankok: UniCredit, Erste, OTP, "
    "Raiffeisen; telekom: Magyar Telekom, Vodafone, Deutsche Telekom; ipar: BASF, Siemens, Bosch; "
    "energetika: MOL, E.ON), publikus e-beszerzési platformok (SAP Ariba Discovery, Jaggaer, Coupa, "
    "tendigo, Mercell privát szekciói), ahol IT-képzést, reskilling/upskilling programot, "
    "digital academy szolgáltatást keresnek beszállítótól",
    "E-learning tananyagfejlesztés és LMS – digitális tananyag gyártása, e-learning kurzusfejlesztés, "
    "SCORM-tartalom, oktatóvideó-produkció, tanulásirányítási rendszer (LMS) bevezetése vagy "
    "tartalommal való feltöltése. Keresd így is: 'e-learning tananyagfejlesztés', 'digitális tananyag "
    "beszerzés', 'e-learning content development RFP', 'Erstellung von E-Learning-Inhalten', "
    "'opracowanie materiałów e-learningowych', 'learning management system tender'",
    "Készségfelmérés és képzési tanácsadás – kompetenciamátrix kidolgozása, skills gap analízis, "
    "képzési terv és képzési stratégia készítése, digitális érettségfelmérés, megvalósíthatósági "
    "tanulmány, mikrotanúsítványi rendszer kialakítása. Keresd így is: 'képzési terv kidolgozása "
    "ajánlatkérés', 'skills gap analysis tender', 'competency framework consultancy', "
    "'digital maturity assessment RFP'",
    "IT-toborzás és munkaerő-biztosítás – informatikai szakemberek toborzása, kiválasztása, "
    "munkaerő-kölcsönzés, valamint toborzást ÉS képzést együtt kérő 'academy' típusú programok. "
    "Keresd így is: 'IT munkaerő-kölcsönzés közbeszerzés', 'informatikai szakemberek toborzása "
    "ajánlattételi felhívás', 'IT recruitment services tender', 'Personaldienstleistung IT', "
    "'rekrutacja specjalistów IT przetarg'. FIGYELEM: csak akkor releváns, ha IT/digitális "
    "profilú – az általános munkaerő-kölcsönzést (takarítás, ápolás, logisztika) hagyd ki",
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
        "name": "Baza Konkurencyjności – EU-forrásból finanszírozott beszerzések (PL)",
        "url": "https://bazakonkurencyjnosci.funduszeeuropejskie.gov.pl/ogloszenia/szukaj",
        # No public API: every /api/ endpoint is 401 behind Keycloak, so this one
        # can only be reached by search. Its content is unique though – EU-funded
        # beneficiaries publish training procurements here that reach no other portal.
        "item_hint": "egy konkrét ogłoszenie saját oldala (…/ogloszenia/<azonosító>), nem a keresőoldal",
    },
    {
        "name": "platformazakupowa.pl – lengyel e-beszerzési platform",
        "url": "https://platformazakupowa.pl/",
        # No API, and robots.txt asks for a 900 s crawl delay – search only.
        "item_hint": "egy konkrét transakcja oldala (platformazakupowa.pl/transakcja/<szám>)",
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
TED_MAX_CANDIDATES = 40        # ceiling on notices handed to the model (= sum of the group quotas)
TED_MAX_PAGES = 8              # safety stop on paging (100 notices per page)

# Only open opportunities: contract notices, prior information and qualification
# systems. Award notices (can-*) are already decided, so they are excluded.
TED_NOTICE_TYPES = ["cn-standard", "cn-social", "pin-only", "qu-sy"]

# Candidate families. Each is fetched separately and gets its OWN quota, so the
# training notices (by far the most numerous) cannot crowd the other service
# lines out of the list handed to the model. "digital_only" applies the keyword
# filter below; it is on where the CPV group is broad enough to be full of
# driving schools and temp nurses.
TED_GROUPS = [
    {
        "key": "kepzes",
        "label": "IT / digitális képzés",
        "quota": 22,
        "digital_only": False,
        "cpv": [
            "80420000",   # e-learning services
            "80533000",   # computer-user training
            "80533100",   # computer training services
            "80533200",   # computer courses
            "80531200",   # technical training services
        ],
    },
    {
        "key": "kepzes_altalanos",
        "label": "általános képzés, digitális tartalommal",
        "quota": 8,
        "digital_only": True,   # huge volume: fire safety, driving, language courses
        "cpv": [
            "80400000",   # adult and other education services
            "80500000",   # training services
            "80510000",   # specialist training services
            "80511000",   # staff training services
            "80530000",   # vocational training services
            "80532000",   # management training services
        ],
    },
    {
        "key": "elearning_szoftver",
        "label": "oktatási szoftver / LMS / tananyag",
        "quota": 10,
        "digital_only": False,  # the CPV group is already specific
        "cpv": [
            "48190000",   # educational software package
            "48931000",   # training software package
            "72212190",   # educational software development services
        ],
    },
]

# WITHDRAWN 2026-09-18 – IT recruitment through TED. Codecool does want these
# tenders, but this was the wrong channel for them: the recruitment CPVs carry
# ~272 notices a month of overwhelmingly generic staffing, and across two live
# runs the group handed over 5 then 3 candidates (conflict-management training,
# a leadership course, generic HR services, a data-entry contract) of which the
# model kept NONE – it only displaced better candidates from the quota.
#
# IT recruitment is still covered: SEARCH_SEGMENTS has a dedicated web-search
# segment for it, which also reaches the corporate RFPs where such work is
# usually advertised, and costs no candidate slots.
#
# To put it back: drop this block into TED_GROUPS and take the quota from
# "kepzes". `digital_in_title_only` is still supported in ted_source.py.
#
# {
#     "key": "toborzas",
#     "label": "IT-toborzás / munkaerő-biztosítás",
#     "quota": 3,
#     "digital_only": True,
#     "digital_in_title_only": True,   # title must say IT; description is too loose
#     "cpv": [
#         "79600000",   # recruitment services
#         "79610000",   # placement services of personnel
#         "79611000",   # job search services
#         "79620000",   # supply services of personnel incl. temporary staff
#         "79634000",   # career guidance services
#     ],
# },

# TED titles read "Country - <main CPV label> - <buyer's own title>", and we ask
# for the Hungarian rendering, so these words in the middle label mark a notice
# that is genuinely ABOUT training rather than one that merely carries a
# training CPV next to a hardware purchase.
TED_TRAINING_TITLE_WORDS = ["képzés", "oktatás", "tanfolyam", "továbbképz", "e-learning", "tananyag"]

# Multilingual – the notice title/description is in the buyer's own language.
TED_DIGITAL_KEYWORDS = [
    "digital", "digitál", "digitale", "digitalis", "cyfrow", "numérique", "numerique",
    "informati", "informatyk", "it-", "-it", "ict", "computer", "komputer",
    "számítógép", "szoftver", "software", "programoz", "programming", "programista",
    "coding", "kódol", "e-learning", "elearning", "online", "webfejleszt", "web development",
    "cyber", "kiber", "cyberbezpiecz", "adatbázis", "database", "cloud", "felhő",
    "mesterséges intelligencia", "artificial intelligence", " ai ", "edv", "schulung it",
]

# --- e-Zamówienia (PL) direct API --------------------------------------------
# Polish public procurement, and crucially the BELOW-EU-THRESHOLD notices that
# never reach TED. Poland is a real market for Codecool, so this is the one
# addition of the three Polish portals suggested on 2026-09-18 that has a usable
# public interface. See ezamowienia_source.py for why the other two do not.
EZAM_API_URL = "https://ezamowienia.gov.pl/mo-board/api/v1/Board/Search"
EZAM_LOOKBACK_DAYS = 30
EZAM_MAX_CANDIDATES = 10       # how many Polish notices are handed to the model
EZAM_MAX_PAGES = 6             # the API returns 10 records per page, hard-capped

EZAM_CPV_CODES = [
    "80500000",   # usługi szkoleniowe – training services
    "80510000",   # specialist training
    "80511000",   # staff training
    "80530000",   # vocational training
    "80533100",   # computer training
    "80420000",   # e-learning
    "72212190",   # educational software development
]

# The subject line must ALSO say this is training. Without it the training CPV
# codes drag in hardware and system rollouts that merely carry an 80533100 code
# on the side – measured 2026-09-18: of 10 candidates, 5 were waterworks cyber
# systems, lab software and equipment delivery. Same lesson as the TED titles.
EZAM_TRAINING_WORDS = [
    "szkolen", "szkoleń", "szkolenie", "kurs", "warsztat", "edukac",
    "nauczan", "kompetencj", "e-learning", "doskonalen", "podnoszenie kwalifikacji",
]

# Polish terms on top of TED_DIGITAL_KEYWORDS – the subject lines here are
# Polish only, and these are the words that mark an IT/digital tender.
EZAM_EXTRA_KEYWORDS = [
    "informatyczn", "cyfrow", "komputerow", "programowani", "oprogramowani",
    "cyberbezpiecz", "sieci", "chmur", "sztucznej inteligencji", "e-usług",
    "szkolenia it", "kompetencji cyfrowych", "system informatyczny",
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

# Output ceiling for one model reply. Raised from 16000 on 2026-09-17: with 40 TED
# candidates plus the relevance rubric (every item now carries a justification),
# a run hit max_tokens mid-JSON and the whole array was lost. Reasoning tokens
# count against this too, so keep real headroom.
MAX_OUTPUT_TOKENS = 32000

MIN_RELEVANCE = "med"          # "low" | "med" | "high" – anything below this is not reported in notifications
