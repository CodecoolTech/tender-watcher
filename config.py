"""
Codecool Pályázatfigyelő – konfiguráció.

Itt szabályozod a keresés fókuszát. A figyelt honlapokat NEM kell felsorolni:
az AI a profil + a forrásportálok alapján magától keres és felderít cégoldalakat is.
"""

# --- Cégprofil (a relevancia-szűrést vezérli) -------------------------------
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
felnőttképzés, informatikai képzés, digitális kompetencia.
"""

# --- Keresési szegmensek -----------------------------------------------------
# FONTOS: a felsorolt portálok csak PÉLDÁK, nem kimerítő lista. A cél a teljes
# európai piac lefedése – az AI minden szegmensben maga derít fel további
# forrásokat (országos, városi és céges beszerzési oldalakat egyaránt).
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
    "Céges / magánszektor tenderek és beszerzési portálok – nagyvállalatok saját supplier/procurement "
    "oldalai (pl. BASF, Siemens, Bosch, banki és telekom cégek beszállítói portáljai), ahol IT-képzést, "
    "reskilling/upskilling programot, digital academy szolgáltatást keresnek beszállítótól",
]

# Visszafelé kompatibilitás (régi név)
SOURCES = SEARCH_SEGMENTS

# --- OpenRouter / modell / futtatás -----------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = "anthropic/claude-sonnet-5"   # jó ár/érték; erősebbhez pl. "anthropic/claude-opus-4.5"

# Web-keresés (openrouter:web_search szervertool) beállításai:
MAX_RESULTS_PER_SEARCH = 5     # egy keresés max. találata (Exa-motor); 1–25
MAX_TOTAL_RESULTS = 40         # összes találat felső korlátja egy futásban (költség-/kontextuskorlát)
                               # 40 ≈ 8 keresés – kell a szélesebb piaci lefedettséghez; ha drága, vedd vissza 25-re

MIN_RELEVANCE = "med"          # "low" | "med" | "high" – ez alatti relevanciát nem jelentünk push-ban
