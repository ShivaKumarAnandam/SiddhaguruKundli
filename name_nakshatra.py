"""
Name-based Nakshatra lookup using Telugu syllable mapping.
Based on traditional Vedic astrology naming conventions.
Updated with accurate data from పేరు ప్రకారం రాశి - నక్షత్రం వివరాలు
"""

# Complete dataset - 108 entries matching the official Telugu syllable table
NAME_NAKSHATRA_MAP = [
    # S.NO 1-10
    {"syllables": ["ఆ", "అ", "aa", "a"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "కృత్తిక", "nakshatra_en": "Krittika", "pada": 1},
    {"syllables": ["ఈ", "ఇ", "ee", "i"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "కృత్తిక", "nakshatra_en": "Krittika", "pada": 2},
    {"syllables": ["ఊ", "ఉ", "oo", "u"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "కృత్తిక", "nakshatra_en": "Krittika", "pada": 3},
    {"syllables": ["ఏ", "ఎ", "ఐ", "e", "ai"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "కృత్తిక", "nakshatra_en": "Krittika", "pada": 4},
    {"syllables": ["ఓ", "ఒ", "ఔ", "o", "ou"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "రోహిణి", "nakshatra_en": "Rohini", "pada": 1},
    {"syllables": ["కా", "క", "కృ", "kaa", "ka", "kru"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "మృగశిర", "nakshatra_en": "Mrigashira", "pada": 3},
    {"syllables": ["కు", "కూ", "ku", "koo"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "ఆరుద్ర", "nakshatra_en": "Ardra", "pada": 1},
    {"syllables": ["కే", "కె", "కై", "ke", "kai"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "పునర్వసు", "nakshatra_en": "Punarvasu", "pada": 1},
    {"syllables": ["కి", "కీ", "ki", "kee"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "మృగశిర", "nakshatra_en": "Mrigashira", "pada": 4},
    {"syllables": ["కో", "కొ", "కౌ", "ko", "kou"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "పునర్వసు", "nakshatra_en": "Punarvasu", "pada": 2},
    
    # S.NO 11-20
    {"syllables": ["కం", "kam"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "ఆరుద్ర", "nakshatra_en": "Ardra", "pada": 2},
    {"syllables": ["ఖా", "ఖ", "khaa", "kha"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "శ్రవణం", "nakshatra_en": "Shravana", "pada": 4},
    {"syllables": ["గా", "గ", "gaa", "ga"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "ధనిష్ఠ", "nakshatra_en": "Dhanishtha", "pada": 1},
    {"syllables": ["గూ", "గు", "goo", "gu"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "ధనిష్ఠ", "nakshatra_en": "Dhanishtha", "pada": 3},
    {"syllables": ["గో", "గొ", "గౌ", "go", "gau"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "శతభిషం", "nakshatra_en": "Shatabhisha", "pada": 1},
    {"syllables": ["గీ", "గి", "gee", "gi"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "ధనిష్ఠ", "nakshatra_en": "Dhanishtha", "pada": 2},
    {"syllables": ["గె", "గే", "గై", "ge", "gai"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "ధనిష్ఠ", "nakshatra_en": "Dhanishtha", "pada": 4},
    {"syllables": ["చు", "చూ", "chu", "choo"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "అశ్విని", "nakshatra_en": "Ashwini", "pada": 1},
    {"syllables": ["చె", "చే", "చై", "che", "chai"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "అశ్విని", "nakshatra_en": "Ashwini", "pada": 2},
    {"syllables": ["చొ", "చో", "చౌ", "cho", "chou"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "అశ్విని", "nakshatra_en": "Ashwini", "pada": 3},
    
    # S.NO 21-30
    {"syllables": ["చా", "చ", "chaa", "cha"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "రేవతి", "nakshatra_en": "Revati", "pada": 3},
    {"syllables": ["చి", "చీ", "chi", "chee"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "రేవతి", "nakshatra_en": "Revati", "pada": 4},
    {"syllables": ["ఛ", "ఛా", "chha", "chhaa"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "ఆరుద్ర", "nakshatra_en": "Ardra", "pada": 4},
    {"syllables": ["జ్ఞ", "gna", "jna"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "ఆరుద్ర", "nakshatra_en": "Ardra", "pada": 3},
    {"syllables": ["జూ", "జు", "joo", "ju"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "శ్రవణం", "nakshatra_en": "Shravana", "pada": 1},
    {"syllables": ["జా", "జ", "jaa", "ja"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "ఉత్తరాషాఢ", "nakshatra_en": "Uttara Ashadha", "pada": 3},
    {"syllables": ["జే", "జె", "జై", "je", "jai"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "శ్రవణం", "nakshatra_en": "Shravana", "pada": 2},
    {"syllables": ["జీ", "జి", "jee", "ji"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "ఉత్తరాషాఢ", "nakshatra_en": "Uttara Ashadha", "pada": 4},
    {"syllables": ["జొ", "జో", "జౌ", "jo", "jou"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "శ్రవణం", "nakshatra_en": "Shravana", "pada": 3},
    {"syllables": ["ఝూ", "ఝు", "jhoo", "jhu"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "ఉత్తరాభాద్ర", "nakshatra_en": "Uttara Bhadrapada", "pada": 3},
    
    # S.NO 31-40
    {"syllables": ["టే", "టె", "టై", "te", "tai"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "ఉత్తర", "nakshatra_en": "Uttara Phalguni", "pada": 1},
    {"syllables": ["టో", "టొ", "టౌ", "to", "tou"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "ఉత్తర", "nakshatra_en": "Uttara Phalguni", "pada": 2},
    {"syllables": ["టా", "ట", "taa", "ta"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "పుబ్బ", "nakshatra_en": "Purva Phalguni", "pada": 2},
    {"syllables": ["టి", "టీ", "ti", "tee"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "పుబ్బ", "nakshatra_en": "Purva Phalguni", "pada": 3},
    {"syllables": ["టూ", "టు", "too", "tu"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "పుబ్బ", "nakshatra_en": "Purva Phalguni", "pada": 4},
    {"syllables": ["ఠ", "ఠా", "ta", "taa"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "హస్త", "nakshatra_en": "Hasta", "pada": 4},
    {"syllables": ["డి", "డీ", "di", "dee"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "ఆశ్లేష", "nakshatra_en": "Ashlesha", "pada": 1},
    {"syllables": ["డూ", "డు", "doo", "du"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "ఆశ్లేష", "nakshatra_en": "Ashlesha", "pada": 2},
    {"syllables": ["డే", "డె", "డై", "de", "dai"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "ఆశ్లేష", "nakshatra_en": "Ashlesha", "pada": 3},
    {"syllables": ["డా", "డ", "daa", "da"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "పుష్యమి", "nakshatra_en": "Pushya", "pada": 4},
    
    # S.NO 41-50
    {"syllables": ["డో", "డొ", "డౌ", "do", "dau"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "ఆశ్లేష", "nakshatra_en": "Ashlesha", "pada": 4},
    {"syllables": ["ఢా", "ఢ", "daa", "da"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "పూర్వాషాఢ", "nakshatra_en": "Purva Ashadha", "pada": 4},
    {"syllables": ["ణా", "ణ", "naa", "na"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "హస్త", "nakshatra_en": "Hasta", "pada": 3},
    {"syllables": ["తి", "తీ", "thi", "thee"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "విశాఖ", "nakshatra_en": "Vishakha", "pada": 1},
    {"syllables": ["తో", "తొ", "తౌ", "tho", "thau"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "విశాఖ", "nakshatra_en": "Vishakha", "pada": 4},
    {"syllables": ["తూ", "తు", "thoo", "thu"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "విశాఖ", "nakshatra_en": "Vishakha", "pada": 2},
    {"syllables": ["తే", "తె", "తై", "the", "thai"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "విశాఖ", "nakshatra_en": "Vishakha", "pada": 3},
    {"syllables": ["త", "తా", "tha", "thaa"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "స్వాతి", "nakshatra_en": "Swati", "pada": 4},
    {"syllables": ["థా", "థ", "thaa", "tha"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "ఉత్తరాభాద్ర", "nakshatra_en": "Uttara Bhadrapada", "pada": 4},
    {"syllables": ["ది", "దీ", "di", "dee"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "పూర్వాభాద్ర", "nakshatra_en": "Purva Bhadrapada", "pada": 4},
    
    # S.NO 51-60
    {"syllables": ["దూ", "దు", "doo", "du"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "ఉత్తరాభాద్ర", "nakshatra_en": "Uttara Bhadrapada", "pada": 1},
    {"syllables": ["దే", "దె", "దై", "de", "dai"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "రేవతి", "nakshatra_en": "Revati", "pada": 1},
    {"syllables": ["దో", "దొ", "దౌ", "do", "dou"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "రేవతి", "nakshatra_en": "Revati", "pada": 2},
    {"syllables": ["దా", "ద", "daa", "da"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "పూర్వాభాద్ర", "nakshatra_en": "Purva Bhadrapada", "pada": 3},
    {"syllables": ["ధా", "ధ", "dhaa", "dha"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "పూర్వాషాఢ", "nakshatra_en": "Purva Ashadha", "pada": 2},
    {"syllables": ["నా", "న", "naa", "na"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "అనురాధ", "nakshatra_en": "Anuradha", "pada": 1},
    {"syllables": ["నో", "నొ", "నౌ", "no", "nau"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "జ్యేష్ఠ", "nakshatra_en": "Jyeshtha", "pada": 1},
    {"syllables": ["నీ", "ని", "nee", "ni"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "అనురాధ", "nakshatra_en": "Anuradha", "pada": 2},
    {"syllables": ["నూ", "ను", "noo", "nu"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "అనురాధ", "nakshatra_en": "Anuradha", "pada": 3},
    {"syllables": ["నే", "నె", "నై", "ne", "nai"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "అనురాధ", "nakshatra_en": "Anuradha", "pada": 4},
    
    # S.NO 61-70
    {"syllables": ["పూ", "పు", "poo", "pu"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "హస్త", "nakshatra_en": "Hasta", "pada": 1},
    {"syllables": ["పే", "పె", "పై", "pe", "pai"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "చిత్త", "nakshatra_en": "Chitra", "pada": 1},
    {"syllables": ["పొ", "ప", "ఫ", "po", "pa", "fa"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "ఉత్తర", "nakshatra_en": "Uttara Phalguni", "pada": 3},
    {"syllables": ["పో", "పొ", "పౌ", "po", "pau"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "చిత్త", "nakshatra_en": "Chitra", "pada": 2},
    {"syllables": ["పీ", "పి", "pee", "pi"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "ఉత్తర", "nakshatra_en": "Uttara Phalguni", "pada": 4},
    {"syllables": ["బూ", "బు", "boo", "bu"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "పూర్వాషాఢ", "nakshatra_en": "Purva Ashadha", "pada": 1},
    {"syllables": ["బే", "బె", "బై", "be", "bai"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "ఉత్తరాషాఢ", "nakshatra_en": "Uttara Ashadha", "pada": 1},
    {"syllables": ["బో", "బొ", "బౌ", "bo", "bau"], "rashi": "మకర", "rashi_en": "Makara (Capricorn)", "nakshatra": "ఉత్తరాషాఢ", "nakshatra_en": "Uttara Ashadha", "pada": 2},
    {"syllables": ["బా", "బ", "భీ", "baa", "ba", "bhee"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "మూల", "nakshatra_en": "Mula", "pada": 3},
    {"syllables": ["బి", "బీ", "bi", "bee"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "మూల", "nakshatra_en": "Mula", "pada": 4},
    
    # S.NO 71-80
    {"syllables": ["భా", "భ", "భై", "bhaa", "bha", "bhai"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "పూర్వాషాఢ", "nakshatra_en": "Purva Ashadha", "pada": 3},
    {"syllables": ["మా", "మ", "maa", "ma"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "మఖ", "nakshatra_en": "Magha", "pada": 1},
    {"syllables": ["మో", "మొ", "మౌ", "mo", "mau"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "పుబ్బ", "nakshatra_en": "Purva Phalguni", "pada": 1},
    {"syllables": ["మీ", "మి", "mee", "mi"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "మఖ", "nakshatra_en": "Magha", "pada": 2},
    {"syllables": ["మూ", "ము", "moo", "mu"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "మఖ", "nakshatra_en": "Magha", "pada": 3},
    {"syllables": ["మే", "మె", "మై", "me", "mai"], "rashi": "సింహ", "rashi_en": "Simha (Leo)", "nakshatra": "మఖ", "nakshatra_en": "Magha", "pada": 4},
    {"syllables": ["యె", "యే", "యై", "ye", "yai"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "మూల", "nakshatra_en": "Mula", "pada": 1},
    {"syllables": ["యా", "య", "yaa", "ya"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "జ్యేష్ఠ", "nakshatra_en": "Jyeshtha", "pada": 2},
    {"syllables": ["యో", "యు", "యౌ", "yo", "yau"], "rashi": "ధనుస్సు", "rashi_en": "Dhanussu (Sagittarius)", "nakshatra": "మూల", "nakshatra_en": "Mula", "pada": 2},
    {"syllables": ["యి", "యీ", "yi", "yee"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "జ్యేష్ఠ", "nakshatra_en": "Jyeshtha", "pada": 3},
    
    # S.NO 81-90
    {"syllables": ["యూ", "యు", "yoo", "yu"], "rashi": "వృశ్చిక", "rashi_en": "Vrishchika (Scorpio)", "nakshatra": "జ్యేష్ఠ", "nakshatra_en": "Jyeshtha", "pada": 4},
    {"syllables": ["రా", "ర", "ప్ర", "ప్రా", "బ్ర", "raa", "ra", "pra", "praa", "bra"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "చిత్త", "nakshatra_en": "Chitra", "pada": 3},
    {"syllables": ["రూ", "రు", "హృ", "roo", "ru", "hru"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "స్వాతి", "nakshatra_en": "Swati", "pada": 1},
    {"syllables": ["రి", "రీ", "శ్రీ", "ri", "ree", "sri"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "చిత్త", "nakshatra_en": "Chitra", "pada": 4},
    {"syllables": ["రె", "రే", "రై", "re", "rai"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "స్వాతి", "nakshatra_en": "Swati", "pada": 2},
    {"syllables": ["రొ", "రో", "రౌ", "ద్రౌ", "ద్రో", "ro", "rau", "drau", "dro"], "rashi": "తుల", "rashi_en": "Tula (Libra)", "nakshatra": "స్వాతి", "nakshatra_en": "Swati", "pada": 3},
    {"syllables": ["లూ", "లు", "loo", "lu"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "భరణి", "nakshatra_en": "Bharani", "pada": 2},
    {"syllables": ["లి", "లీ", "li", "lee"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "భరణి", "nakshatra_en": "Bharani", "pada": 1},
    {"syllables": ["లె", "లే", "లై", "le", "lai"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "భరణి", "nakshatra_en": "Bharani", "pada": 3},
    {"syllables": ["లా", "ల", "laa", "la"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "అశ్విని", "nakshatra_en": "Ashwini", "pada": 4},
    
    # S.NO 91-100
    {"syllables": ["లో", "లొ", "లౌ", "lo", "lau"], "rashi": "మేష", "rashi_en": "Mesha (Aries)", "nakshatra": "భరణి", "nakshatra_en": "Bharani", "pada": 4},
    {"syllables": ["వే", "వె", "వై", "ve", "vai"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "మృగశిర", "nakshatra_en": "Mrigashira", "pada": 1},
    {"syllables": ["వా", "వ", "vaa", "va"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "రోహిణి", "nakshatra_en": "Rohini", "pada": 2},
    {"syllables": ["వో", "వొ", "వౌ", "vo", "vau"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "మృగశిర", "nakshatra_en": "Mrigashira", "pada": 3},
    {"syllables": ["వీ", "వి", "vee", "vi"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "రోహిణి", "nakshatra_en": "Rohini", "pada": 3},
    {"syllables": ["వూ", "వు", "voo", "vu"], "rashi": "వృషభ", "rashi_en": "Vrishabha (Taurus)", "nakshatra": "రోహిణి", "nakshatra_en": "Rohini", "pada": 4},
    {"syllables": ["శ", "శా", "శ్యా", "sha", "shaa", "shyaa", "sh"], "rashi": "మీన", "rashi_en": "Meena (Pisces)", "nakshatra": "ఉత్తరాభాద్ర", "nakshatra_en": "Uttara Bhadrapada", "pada": 2},
    {"syllables": ["షం", "క్షే", "sham", "kshe"], "rashi": "కన్య", "rashi_en": "Kanya (Virgo)", "nakshatra": "హస్త", "nakshatra_en": "Hasta", "pada": 2},
    {"syllables": ["సె", "సే", "సై", "se", "sai"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "పూర్వాభాద్ర", "nakshatra_en": "Purva Bhadrapada", "pada": 1},
    {"syllables": ["సా", "స", "saa", "sa"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "శతభిషం", "nakshatra_en": "Shatabhisha", "pada": 2},
    
    # S.NO 101-108
    {"syllables": ["సో", "సొ", "సౌ", "so", "sau"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "పూర్వాభాద్ర", "nakshatra_en": "Purva Bhadrapada", "pada": 2},
    {"syllables": ["సీ", "సి", "see", "si"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "శతభిషం", "nakshatra_en": "Shatabhisha", "pada": 3},
    {"syllables": ["సూ", "సు", "soo", "su"], "rashi": "కుంభ", "rashi_en": "Kumbha (Aquarius)", "nakshatra": "శతభిషం", "nakshatra_en": "Shatabhisha", "pada": 4},
    {"syllables": ["హి", "హీ", "hi", "hee"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "పునర్వసు", "nakshatra_en": "Punarvasu", "pada": 4},
    {"syllables": ["హూ", "హు", "hoo", "hu"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "పుష్యమి", "nakshatra_en": "Pushya", "pada": 1},
    {"syllables": ["హె", "హే", "హై", "he", "hai"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "పుష్యమి", "nakshatra_en": "Pushya", "pada": 2},
    {"syllables": ["హా", "హ", "haa", "ha"], "rashi": "మిథున", "rashi_en": "Mithuna (Gemini)", "nakshatra": "పునర్వసు", "nakshatra_en": "Punarvasu", "pada": 3},
    {"syllables": ["హొ", "హో", "హౌ", "ho", "hou"], "rashi": "కర్కాటక", "rashi_en": "Karkataka (Cancer)", "nakshatra": "పుష్యమి", "nakshatra_en": "Pushya", "pada": 3},
]


def normalize_syllable(syllable: str) -> str:
    """Normalize syllable for matching - lowercase and strip spaces."""
    return syllable.lower().strip()


def find_nakshatra_by_name(name: str) -> dict:
    """
    Find nakshatra details based on the first syllable of the name.
    Supports both Telugu and English input.
    
    Args:
        name: Person's name in Telugu or English
        
    Returns:
        dict with rashi, nakshatra, pada details or error
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    
    name = name.strip()
    
    # Try matching progressively shorter prefixes (5 chars down to 1 char)
    # Telugu syllables with combining marks can be 4-5 characters (e.g., శ్రీ = 4 chars)
    for length in [5, 4, 3, 2, 1]:
        prefix = normalize_syllable(name[:length])
        
        for entry in NAME_NAKSHATRA_MAP:
            for syllable in entry["syllables"]:
                if normalize_syllable(syllable) == prefix:
                    return {
                        "name": name,
                        "matched_syllable": syllable,
                        "rashi_telugu": entry["rashi"],
                        "rashi": entry["rashi_en"],
                        "nakshatra_telugu": entry["nakshatra"],
                        "nakshatra": entry["nakshatra_en"],
                        "pada": entry["pada"],
                        "pada_label": f"{entry['pada']}{'st' if entry['pada']==1 else 'nd' if entry['pada']==2 else 'rd' if entry['pada']==3 else 'th'}"
                    }
    
    raise ValueError(f"No nakshatra mapping found for name starting with '{name[:2]}'")



# Quick test
if __name__ == "__main__":
    test_names = [
        "Shiva",
        "శివ",
        "Kumar",
        "Sharanya",
        "శరణ్య",
        "Arjun",
        "అర్జున్",
        "Rama",
        "రామ",
    ]
    
    print("Name-based Nakshatra Lookup Test")
    print("=" * 60)
    
    for test_name in test_names:
        try:
            result = find_nakshatra_by_name(test_name)
            print(f"\n{result['name']} ({result['matched_syllable']})")
            print(f"  Rashi: {result['rashi']} ({result['rashi_telugu']})")
            print(f"  Nakshatra: {result['nakshatra']} ({result['nakshatra_telugu']})")
            print(f"  Pada: {result['pada_label']}")
        except ValueError as e:
            print(f"\n{test_name}: ERROR - {e}")
