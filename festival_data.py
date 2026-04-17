"""
Static festival data table and lookup for Telugu Panchang.

Key format: (masa_num, paksha_num, tithi_num)
  masa_num:   1=Chaitra, 2=Vaisakha, 3=Jyeshtha, 4=Ashadha, 5=Shravana,
              6=Bhadrapada, 7=Ashwina, 8=Kartika, 9=Margashira, 10=Pushya,
              11=Magha, 12=Phalguna
  paksha_num: 1=Shukla, 2=Krishna
  tithi_num:  1-15 (within each paksha)

Each entry is a list of dicts with "en" and "te" keys, allowing multiple
festivals on the same tithi.
"""

from typing import Dict, List, Tuple

# Masa names for Ekadashi naming
_MASA_NAMES_EN = {
    1: "Chaitra", 2: "Vaisakha", 3: "Jyeshtha", 4: "Ashadha",
    5: "Shravana", 6: "Bhadrapada", 7: "Ashwina", 8: "Kartika",
    9: "Margashira", 10: "Pushya", 11: "Magha", 12: "Phalguna",
}

_MASA_NAMES_TE = {
    1: "చైత్ర", 2: "వైశాఖ", 3: "జ్యేష్ఠ", 4: "ఆషాఢ",
    5: "శ్రావణ", 6: "భాద్రపద", 7: "ఆశ్వయుజ", 8: "కార్తీక",
    9: "మార్గశిర", 10: "పుష్య", 11: "మాఘ", 12: "ఫాల్గుణ",
}

# Specific Ekadashi names per masa and paksha
_EKADASHI_NAMES: Dict[Tuple[int, int], Tuple[str, str]] = {
    # (masa, paksha): (english_name, telugu_name)
    (1, 1): ("Kamada Ekadashi", "కామద ఏకాదశి"),
    (1, 2): ("Varuthini Ekadashi", "వరూథిని ఏకాదశి"),
    (2, 1): ("Mohini Ekadashi", "మోహిని ఏకాదశి"),
    (2, 2): ("Apara Ekadashi", "అపర ఏకాదశి"),
    (3, 1): ("Nirjala Ekadashi", "నిర్జల ఏకాదశి"),
    (3, 2): ("Yogini Ekadashi", "యోగిని ఏకాదశి"),
    (4, 1): ("Devshayani Ekadashi", "దేవశయని ఏకాదశి"),
    (4, 2): ("Kamika Ekadashi", "కామికా ఏకాదశి"),
    (5, 1): ("Putrada Ekadashi", "పుత్రద ఏకాదశి"),
    (5, 2): ("Aja Ekadashi", "అజా ఏకాదశి"),
    (6, 1): ("Parivartini Ekadashi", "పరివర్తిని ఏకాదశి"),
    (6, 2): ("Indira Ekadashi", "ఇందిర ఏకాదశి"),
    (7, 1): ("Papankusha Ekadashi", "పాపాంకుశ ఏకాదశి"),
    (7, 2): ("Rama Ekadashi", "రామా ఏకాదశి"),
    (8, 1): ("Prabodhini Ekadashi", "ప్రబోధిని ఏకాదశి"),
    (8, 2): ("Utpanna Ekadashi", "ఉత్పన్న ఏకాదశి"),
    (9, 1): ("Mokshada Ekadashi", "మోక్షద ఏకాదశి"),
    (9, 2): ("Saphala Ekadashi", "సఫల ఏకాదశి"),
    (10, 1): ("Putrada Ekadashi", "పుత్రద ఏకాదశి"),
    (10, 2): ("Shattila Ekadashi", "షట్తిల ఏకాదశి"),
    (11, 1): ("Jaya Ekadashi", "జయ ఏకాదశి"),
    (11, 2): ("Vijaya Ekadashi", "విజయ ఏకాదశి"),
    (12, 1): ("Amalaki Ekadashi", "ఆమలకి ఏకాదశి"),
    (12, 2): ("Papamochani Ekadashi", "పాపమోచని ఏకాదశి"),
}

# ---------------------------------------------------------------------------
# FESTIVALS table
# Key: (masa_num, paksha_num, tithi_num)
# Value: list of {"en": ..., "te": ...} dicts
# ---------------------------------------------------------------------------
FESTIVALS: Dict[Tuple[int, int, int], List[Dict[str, str]]] = {}

# ── Major fixed festivals ─────────────────────────────────────────────────

# Ugadi — Chaitra Shukla Pratipada
FESTIVALS[(1, 1, 1)] = [{"en": "Ugadi", "te": "ఉగాది"}]

# Rama Navami — Chaitra Shukla Navami
FESTIVALS[(1, 1, 9)] = [{"en": "Rama Navami", "te": "రామ నవమి"}]

# Akshaya Tritiya — Vaisakha Shukla Tritiya
FESTIVALS[(2, 1, 3)] = [{"en": "Akshaya Tritiya", "te": "అక్షయ తృతీయ"}]

# Krishna Janmashtami — Shravana Krishna Ashtami
FESTIVALS[(5, 2, 8)] = [{"en": "Krishna Janmashtami", "te": "కృష్ణ జన్మాష్టమి"}]

# Vinayaka Chaturthi — Bhadrapada Shukla Chaturthi
FESTIVALS[(6, 1, 4)] = [{"en": "Vinayaka Chaturthi", "te": "వినాయక చవితి"}]

# Dussehra / Vijayadashami — Ashwina Shukla Dashami
FESTIVALS[(7, 1, 10)] = [{"en": "Dussehra (Vijayadashami)", "te": "దసరా (విజయదశమి)"}]

# Diwali — Ashwina Krishna Chaturdashi (Naraka Chaturdashi)
FESTIVALS[(7, 2, 14)] = [{"en": "Diwali (Naraka Chaturdashi)", "te": "దీపావళి (నరక చతుర్దశి)"}]

# Diwali — Kartika Krishna Amavasya (main Diwali day)
FESTIVALS[(8, 2, 15)] = [{"en": "Diwali (Amavasya)", "te": "దీపావళి (అమావాస్య)"}]

# Karthika Pournami — Kartika Shukla Pournami
FESTIVALS[(8, 1, 15)] = [{"en": "Karthika Pournami", "te": "కార్తీక పౌర్ణమి"}]

# Maha Shivaratri — Magha Krishna Chaturdashi
FESTIVALS[(11, 2, 14)] = [{"en": "Maha Shivaratri", "te": "మహా శివరాత్రి"}]

# Holi — Phalguna Shukla Pournami
FESTIVALS[(12, 1, 15)] = [{"en": "Holi", "te": "హోళి"}]

# Sankranti note: solar-based, not tithi-based — included as a special note
# Sankranti is determined by the Sun's transit into Makara rashi, typically
# around January 14. It cannot be keyed by (masa, paksha, tithi).
# It should be handled separately in panchang_service.py via solar longitude.

# ── Ekadashi — tithi 11, all 12 masas × 2 pakshas (24 entries) ───────────

for masa in range(1, 13):
    for paksha in (1, 2):
        key = (masa, paksha, 11)
        en_name, te_name = _EKADASHI_NAMES[(masa, paksha)]
        entry = {"en": en_name, "te": te_name}
        if key in FESTIVALS:
            FESTIVALS[key].append(entry)
        else:
            FESTIVALS[key] = [entry]

# ── Pradosham — tithi 13, all 12 masas × 2 pakshas (24 entries) ──────────

for masa in range(1, 13):
    for paksha in (1, 2):
        key = (masa, paksha, 13)
        en_name = f"{_MASA_NAMES_EN[masa]} {'Shukla' if paksha == 1 else 'Krishna'} Pradosham"
        te_name = f"{_MASA_NAMES_TE[masa]} {'శుక్ల' if paksha == 1 else 'కృష్ణ'} ప్రదోషం"
        entry = {"en": en_name, "te": te_name}
        if key in FESTIVALS:
            FESTIVALS[key].append(entry)
        else:
            FESTIVALS[key] = [entry]

# ── Pournami — Shukla Paksha tithi 15, all 12 masas ──────────────────────
# Skip masas that already have a specific Pournami festival (8=Karthika, 12=Holi)

for masa in range(1, 13):
    key = (masa, 1, 15)
    if key in FESTIVALS:
        # Already has a specific festival (e.g. Karthika Pournami, Holi)
        continue
    en_name = f"{_MASA_NAMES_EN[masa]} Pournami"
    te_name = f"{_MASA_NAMES_TE[masa]} పౌర్ణమి"
    FESTIVALS[key] = [{"en": en_name, "te": te_name}]

# ── Amavasya — Krishna Paksha tithi 15, all 12 masas ─────────────────────
# Skip masas that already have a specific Amavasya festival (8=Diwali Amavasya)

for masa in range(1, 13):
    key = (masa, 2, 15)
    if key in FESTIVALS:
        # Already has a specific festival (e.g. Diwali Amavasya)
        continue
    en_name = f"{_MASA_NAMES_EN[masa]} Amavasya"
    te_name = f"{_MASA_NAMES_TE[masa]} అమావాస్య"
    FESTIVALS[key] = [{"en": en_name, "te": te_name}]

# ── Sankashtahara Chaturthi — Krishna Chaturthi (tithi 4), all 12 masas ──

for masa in range(1, 13):
    key = (masa, 2, 4)
    entry = {"en": "Sankashtahara Chaturthi", "te": "సంకష్టహర చతుర్థి"}
    if key in FESTIVALS:
        FESTIVALS[key].append(entry)
    else:
        FESTIVALS[key] = [entry]


# ---------------------------------------------------------------------------
# Lookup function
# ---------------------------------------------------------------------------

def get_festivals(
    masa_num: int,
    paksha_num: int,
    tithi_num: int,
    lang: str = "en",
) -> List[str]:
    """Return festival names for the given (masa, paksha, tithi) triple.

    Args:
        masa_num:   1-12 (Chaitra through Phalguna)
        paksha_num: 1 (Shukla) or 2 (Krishna)
        tithi_num:  1-15 within the paksha
        lang:       "en" for English, "te" for Telugu

    Returns:
        List of festival name strings in the requested language.
        Empty list if no festivals match.
    """
    entries = FESTIVALS.get((masa_num, paksha_num, tithi_num), [])
    return [entry.get(lang, entry.get("en", "")) for entry in entries]
