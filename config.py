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

# --- OpenRouter / model / run settings ---------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = "anthropic/claude-sonnet-5"   # good value for money; for something stronger use e.g. "anthropic/claude-opus-4.5"

# Web search (openrouter:web_search server tool) settings:
MAX_RESULTS_PER_SEARCH = 5     # max. results per single search (Exa engine); 1–25
MAX_SEARCHES = 12              # how many searches the model may run in one pass (max_uses)
MAX_TOTAL_RESULTS = 60         # upper bound on all results in one pass (cost / context limit)
                               # 12 searches × 5 results – needed for full market coverage; lower it if too expensive

MIN_RELEVANCE = "med"          # "low" | "med" | "high" – anything below this is not reported in notifications
