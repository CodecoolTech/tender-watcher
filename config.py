"""
Codecool Pályázatfigyelő – konfiguráció.

Itt szabályozod a keresés fókuszát. A figyelt honlapokat NEM kell felsorolni:
az AI a profil + a forrásportálok alapján magától keres és felderít cégoldalakat is.
"""

# --- Cégprofil (a relevancia-szűrést vezérli) -------------------------------
COMPANY_PROFILE = """
Cég: Codecool (codecool.com) – IT- és programozásoktatás, coding bootcamp.
Jelenlét: főként Magyarország és Közép-Kelet-Európa.
Alaptevékenység: programozás- és digitális készségképzés, felnőtt- és szakképzés (VET),
átképzés / reskilling / upskilling, EdTech megoldások, e-learning.
Célországok a figyeléshez: Magyarország és EU (kiemelten EU-s cégoldalak, pl. finn / északi piac).
Releváns kulcsszavak: digital skills, advanced digital skills, reskilling, upskilling,
vocational education and training (VET), programming / coding training, e-learning, EdTech,
AI in education, micro-credentials, felnőttképzés, informatikai képzés, digitális kompetencia.
"""

# --- Forrásportálok (az AI ezeken fésül át, és célzottan bővíti cégoldalakkal) ---
SOURCES = [
    "EU Funding & Tenders Portal (ec.europa.eu) – Digital Europe (DIGITAL-*-SKILLS/BESTUSE/EDTECH), ESF+, Horizon education",
    "Erasmus+ / EACEA (erasmus-plus.ec.europa.eu) – VET, felnőttképzés, KA2, policy experimentation",
    "Digital Skills and Jobs Platform (digital-skills-jobs.europa.eu)",
    "TED – Tenders Electronic Daily (ted.europa.eu) – IT-képzés, programozás, e-learning közbeszerzések",
    "palyazat.gov.hu / Széchenyi Terv Plusz (DIMOP Plusz, EFOP Plusz)",
    "EKR / Közbeszerzési Értesítő (ekr.gov.hu, kozbeszerzes.hu)",
    "HILMA / hankintailmoitukset.fi (finn közbeszerzés) – pl. Business Finland, EDUFI képzési tenderek",
]

# --- OpenRouter / modell / futtatás -----------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = "anthropic/claude-sonnet-5"   # jó ár/érték; erősebbhez pl. "anthropic/claude-opus-4.5"

# Web-keresés (openrouter:web_search szervertool) beállításai:
MAX_RESULTS_PER_SEARCH = 5     # egy keresés max. találata (Exa-motor); 1–25
MAX_TOTAL_RESULTS = 25         # összes találat felső korlátja egy futásban (költség-/kontextuskorlát)

MIN_RELEVANCE = "med"          # "low" | "med" | "high" – ez alatti relevanciát nem jelentünk push-ban
