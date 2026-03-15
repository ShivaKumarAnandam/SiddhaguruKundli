import swisseph as swe

NAKSHATRA_SPAN = 360 / 27       # 13.3333...°
PADA_SPAN      = NAKSHATRA_SPAN / 4  # 3.3333...°

NAKSHATRAS = [
    {"name": "Ashwini",              "deity": "Ashwini Kumaras", "gana": "Deva",     "animal": "Horse",          "color": "Red",          "stone": "Coral",      "syllables": ["Chu","Che","Cho","La"],    "direction": "East",  "symbol": "Horse head",            "zodiac": "Aries"},
    {"name": "Bharani",              "deity": "Yama",            "gana": "Manushya", "animal": "Elephant",       "color": "Red",          "stone": "Diamond",    "syllables": ["Li","Lu","Le","Lo"],       "direction": "West",  "symbol": "Yoni (female organ)",   "zodiac": "Aries"},
    {"name": "Krittika",             "deity": "Agni",            "gana": "Rakshasa", "animal": "Sheep",          "color": "White",        "stone": "Ruby",       "syllables": ["A","I","U","E"],           "direction": "North", "symbol": "Razor / Flame",         "zodiac": "Aries/Taurus"},
    {"name": "Rohini",               "deity": "Brahma",          "gana": "Manushya", "animal": "Cobra",          "color": "White",        "stone": "Pearl",      "syllables": ["O","Va","Vi","Vu"],        "direction": "East",  "symbol": "Chariot",               "zodiac": "Taurus"},
    {"name": "Mrigashira",           "deity": "Soma",            "gana": "Deva",     "animal": "Female Serpent", "color": "Silver",       "stone": "Emerald",    "syllables": ["Ve","Vo","Ka","Ki"],       "direction": "South", "symbol": "Deer head",             "zodiac": "Taurus/Gemini"},
    {"name": "Ardra",                "deity": "Rudra",           "gana": "Manushya", "animal": "Dog",            "color": "Green",        "stone": "Hessonite",  "syllables": ["Ku","Gha","Ng/Na","Chha"], "direction": "West",  "symbol": "Teardrop (human head)", "zodiac": "Gemini"},
    {"name": "Punarvasu",            "deity": "Aditi",           "gana": "Deva",     "animal": "Cat",            "color": "Lead",         "stone": "Topaz",      "syllables": ["Ke","Ko","Ha","Hi"],       "direction": "North", "symbol": "Bow and quiver",        "zodiac": "Gemini/Cancer"},
    {"name": "Pushya",               "deity": "Brihaspati",      "gana": "Deva",     "animal": "Ram",            "color": "Red",          "stone": "Ruby",       "syllables": ["Hu","He","Ho","Da"],       "direction": "East",  "symbol": "Flower / Circle",       "zodiac": "Cancer"},
    {"name": "Ashlesha",             "deity": "Nagas",           "gana": "Rakshasa", "animal": "Cat",            "color": "Black",        "stone": "Moonstone",  "syllables": ["Di","Du","De","Do"],       "direction": "South", "symbol": "Coiled serpent",        "zodiac": "Cancer"},
    {"name": "Magha",                "deity": "Pitris",          "gana": "Rakshasa", "animal": "Rat",            "color": "Ivory",        "stone": "Ruby",       "syllables": ["Ma","Mi","Mu","Me"],       "direction": "West",  "symbol": "Throne room",           "zodiac": "Leo"},
    {"name": "Purva Phalguni",       "deity": "Bhaga",           "gana": "Manushya", "animal": "Female Rat",     "color": "Brown",        "stone": "Diamond",    "syllables": ["Mo","Ta","Ti","Tu"],       "direction": "North", "symbol": "Front legs of cot",     "zodiac": "Leo"},
    {"name": "Uttara Phalguni",      "deity": "Aryaman",         "gana": "Manushya", "animal": "Bull",           "color": "Blue",         "stone": "Peridot",    "syllables": ["Te","To","Pa","Pi"],       "direction": "East",  "symbol": "Back legs of cot",      "zodiac": "Leo/Virgo"},
    {"name": "Hasta",                "deity": "Savitar",         "gana": "Deva",     "animal": "Buffalo",        "color": "Black",        "stone": "Pearl",      "syllables": ["Pu","Sha","Na","Tha"],     "direction": "South", "symbol": "Open hand / Fist",      "zodiac": "Virgo"},
    {"name": "Chitra",               "deity": "Vishwakarma",     "gana": "Rakshasa", "animal": "Female Tiger",   "color": "Black",        "stone": "Coral",      "syllables": ["Pe","Po","Ra","Ri"],       "direction": "West",  "symbol": "Bright jewel / Pearl",  "zodiac": "Virgo/Libra"},
    {"name": "Swati",                "deity": "Vayu",            "gana": "Deva",     "animal": "Buffalo",        "color": "Black",        "stone": "Sapphire",   "syllables": ["Ru","Re","Ro","Ta"],       "direction": "North", "symbol": "Coral / Sword",         "zodiac": "Libra"},
    {"name": "Vishakha",             "deity": "Indra-Agni",      "gana": "Rakshasa", "animal": "Tiger",          "color": "Golden",       "stone": "Topaz",      "syllables": ["Ti","Tu","Te","To"],       "direction": "East",  "symbol": "Triumphal arch",        "zodiac": "Libra/Scorpio"},
    {"name": "Anuradha",             "deity": "Mitra",           "gana": "Deva",     "animal": "Deer",           "color": "Reddish Brown", "stone": "Topaz",     "syllables": ["Na","Ni","Nu","Ne"],       "direction": "South", "symbol": "Lotus",                 "zodiac": "Scorpio"},
    {"name": "Jyeshtha",             "deity": "Indra",           "gana": "Rakshasa", "animal": "Deer",           "color": "Cream",        "stone": "Amethyst",   "syllables": ["No","Ya","Yi","Yu"],       "direction": "West",  "symbol": "Earring / Umbrella",    "zodiac": "Scorpio"},
    {"name": "Mula",                 "deity": "Nirriti",         "gana": "Rakshasa", "animal": "Dog",            "color": "Brown",        "stone": "Cat's Eye",  "syllables": ["Ye","Yo","Bha","Bhi"],     "direction": "North", "symbol": "Tied roots / Tail",     "zodiac": "Sagittarius"},
    {"name": "Purva Ashadha",        "deity": "Apas",            "gana": "Manushya", "animal": "Monkey",         "color": "Golden",       "stone": "Topaz",      "syllables": ["Bhu","Dha","Pha","Da"],    "direction": "East",  "symbol": "Fan / Winnowing basket","zodiac": "Sagittarius"},
    {"name": "Uttara Ashadha",       "deity": "Vishvedevas",     "gana": "Manushya", "animal": "Mongoose",       "color": "Copper",       "stone": "Amethyst",   "syllables": ["Be","Bo","Ja","Ji"],       "direction": "South", "symbol": "Elephant tusk",         "zodiac": "Sagittarius/Capricorn"},
    {"name": "Shravana",             "deity": "Vishnu",          "gana": "Deva",     "animal": "Monkey",         "color": "Black",        "stone": "Moonstone",  "syllables": ["Ju","Je","Jo","Sha"],      "direction": "North", "symbol": "Three footprints",      "zodiac": "Capricorn"},
    {"name": "Dhanishtha",           "deity": "Ashta Vasus",     "gana": "Rakshasa", "animal": "Lion",           "color": "Silver",       "stone": "Red Coral",  "syllables": ["Ga","Gi","Gu","Ge"],       "direction": "East",  "symbol": "Drum / Flute",          "zodiac": "Capricorn/Aquarius"},
    {"name": "Shatabhisha",          "deity": "Varuna",          "gana": "Rakshasa", "animal": "Horse",          "color": "Blue",         "stone": "Hessonite",  "syllables": ["Go","Sa","Si","Su"],       "direction": "South", "symbol": "Empty circle",          "zodiac": "Aquarius"},
    {"name": "Purva Bhadrapada",     "deity": "Aja Ekapada",     "gana": "Manushya", "animal": "Lion",           "color": "Silver",       "stone": "Amethyst",   "syllables": ["Se","So","Da","Di"],       "direction": "West",  "symbol": "Front of funeral cot",  "zodiac": "Aquarius/Pisces"},
    {"name": "Uttara Bhadrapada",    "deity": "Ahir Budhanya",   "gana": "Manushya", "animal": "Cow",            "color": "Purple",       "stone": "Amethyst",   "syllables": ["Du","Tha","Jha","Da"],     "direction": "North", "symbol": "Back of funeral cot",   "zodiac": "Pisces"},
    {"name": "Revati",               "deity": "Pushan",          "gana": "Deva",     "animal": "Elephant",       "color": "Brown",        "stone": "Moonstone",  "syllables": ["De","Do","Cha","Chi"],     "direction": "East",  "symbol": "Fish / Drum",           "zodiac": "Pisces"},
]

RASI = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karkataka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Thula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

def ordinal(n: int) -> str:
    return {1:"1st", 2:"2nd", 3:"3rd", 4:"4th"}.get(n, f"{n}th")

def calculate_nakshatra(moon_lon: float, moon_speed: float = None) -> dict:
    index = int(moon_lon / NAKSHATRA_SPAN) % 27   # 0–26
    pada  = int((moon_lon % NAKSHATRA_SPAN) / PADA_SPAN) + 1  # 1–4
    rasi  = int(moon_lon / 30) % 12               # 0–11

    n = NAKSHATRAS[index]

    # Calculate nakshatra start/end longitude
    start_lon = index * NAKSHATRA_SPAN
    end_lon   = start_lon + NAKSHATRA_SPAN

    result = {
        "nakshatra":        n["name"],
        "pada":             pada,
        "pada_label":       ordinal(pada),
        "chandra_rasi":     RASI[rasi],
        "deity":            n["deity"],
        "gana":             n["gana"],
        "animal_sign":      n["animal"],
        "color":            n["color"],
        "birthstone":       n["stone"],
        "syllables":        n["syllables"],
        "best_direction":   n["direction"],
        "symbol":           n["symbol"],
        "zodiac_sign":      n["zodiac"],
        "moon_longitude":   round(moon_lon, 4),
        "nakshatra_range":  f"{start_lon:.4f}° – {end_lon:.4f}°",
    }

    if moon_speed is not None:
        result["moon_speed_deg_per_day"] = round(moon_speed, 4)

    return result
