"""
Comprehensive horoscope data including weekday, tithi, karana, yoga predictions
Based on traditional Vedic astrology texts
"""

# Weekday predictions
WEEKDAY_PREDICTIONS = {
    "Monday": {
        "description": "Individuals born on a Monday are known for their gallantry, possessing a lovely form and a perpetually tender-hearted nature. They exhibit purity in their character, experiencing the ebb and flow of life. Despite being short in stature, they boast a fair complexion, a broad chest, and exceptional intelligence. According to astrological beliefs, those born on a Monday are considered wise, peaceful, eloquent, knowledgeable in behaviour, always seeking the protection of royalty, and maintaining equanimity in joy and sorrow. According to another source, individuals born on this day are described as industrious, having a body adorned with auspicious marks, and consistently compassionate. In summary, they are intelligent, articulate speakers, possessing a dignified nature, leading a life under the shelter of royalty, and treating joy and sorrow with equanimity, all while being prosperous.",
        "ruling_planet": "Moon"
    },
    "Tuesday": {
        "description": "Individuals born on Tuesday are characterized by courage, strength, and determination. They possess a warrior-like spirit and are known for their boldness and assertiveness. These individuals are energetic, passionate, and have strong leadership qualities. They may be prone to anger but are also quick to forgive. They excel in competitive fields and are natural fighters who stand up for justice.",
        "ruling_planet": "Mars"
    },
    "Wednesday": {
        "description": "Those born on Wednesday are intelligent, communicative, and versatile. They possess excellent analytical skills and are quick learners. These individuals are witty, adaptable, and have a natural talent for business and commerce. They are skilled in multiple areas and can handle various tasks simultaneously. They are diplomatic and excel in fields requiring communication and intellect.",
        "ruling_planet": "Mercury"
    },
    "Thursday": {
        "description": "Individuals born on Thursday are wise, optimistic, and generous. They possess strong moral values and are inclined towards spirituality and higher learning. These people are fortunate, respected in society, and often achieve positions of authority. They are kind-hearted, charitable, and have a natural inclination towards teaching and guiding others. They enjoy prosperity and lead a righteous life.",
        "ruling_planet": "Jupiter"
    },
    "Friday": {
        "description": "Those born on Friday are artistic, charming, and possess refined tastes. They are attracted to beauty, luxury, and comfort. These individuals are diplomatic, romantic, and have strong aesthetic sensibilities. They excel in arts, music, and creative fields. They are sociable, attractive, and enjoy harmonious relationships. They have a natural ability to attract wealth and material comforts.",
        "ruling_planet": "Venus"
    },
    "Saturday": {
        "description": "Individuals born on Saturday are disciplined, hardworking, and patient. They face challenges with determination and perseverance. These people are serious, responsible, and mature beyond their years. They may experience delays and obstacles but ultimately achieve success through persistent effort. They are practical, organized, and have strong endurance. They value tradition and are reliable.",
        "ruling_planet": "Saturn"
    },
    "Sunday": {
        "description": "Those born on Sunday are confident, authoritative, and possess natural leadership abilities. They have a strong sense of self and are ambitious. These individuals are dignified, generous, and command respect. They have a regal bearing and are inclined towards positions of power and influence. They are creative, vital, and have strong willpower. They shine in their chosen fields and inspire others.",
        "ruling_planet": "Sun"
    }
}

# Rasi (Moon Sign) predictions
RASI_PREDICTIONS = {
    "Mesha (Aries)": {
        "description": "Individuals with Moon in Aries are courageous, energetic, and pioneering. They are natural leaders with strong initiative and competitive spirit. Quick to act and passionate in their pursuits.",
        "element": "Fire",
        "quality": "Movable",
        "lord": "Mars"
    },
    "Vrishabha (Taurus)": {
        "description": "Those with Moon in Taurus are stable, patient, and practical. They appreciate beauty, comfort, and material security. They are reliable, determined, and have strong aesthetic sensibilities.",
        "element": "Earth",
        "quality": "Fixed",
        "lord": "Venus"
    },
    "Mithuna (Gemini)": {
        "description": "Individuals with Moon in Gemini are intellectual, communicative, and versatile. They are curious, adaptable, and skilled in multiple areas. They excel in communication and learning.",
        "element": "Air",
        "quality": "Dual",
        "lord": "Mercury"
    },
    "Karkataka (Cancer)": {
        "description": "Those with Moon in Cancer are emotional, nurturing, and intuitive. They are deeply connected to family and home. They are sensitive, caring, and have strong protective instincts.",
        "element": "Water",
        "quality": "Movable",
        "lord": "Moon"
    },
    "Simha (Leo)": {
        "description": "Individuals with Moon in Leo are confident, generous, and dignified. They possess natural leadership and creative abilities. They are warm-hearted, loyal, and enjoy recognition.",
        "element": "Fire",
        "quality": "Fixed",
        "lord": "Sun"
    },
    "Kanya (Virgo)": {
        "description": "Those with Moon in Virgo are analytical, practical, and detail-oriented. They are service-minded, health-conscious, and perfectionistic. They excel in organization and problem-solving.",
        "element": "Earth",
        "quality": "Dual",
        "lord": "Mercury"
    },
    "Tula (Libra)": {
        "description": "Individuals born with the Moon in Libra are characterized by eloquence and nobility, embodying the traits of a noble wanderer and a clever traveler. They exhibit purity, courtesy, luck, and physical attractiveness. Devoted to worshiping gods, Brahmins, and holy figures, they engage in generous acts, offering gifts to both deities and people. Proficient in commerce, particularly in buying and selling jewels, they possess a firm character but may be drawn to romantic pursuits. Knowledgeable in unguents, clothing, and ornaments, they are prosperous yet endure challenges from their own kin. Despite limited pleasures, they excel in wealth accumulation through determined efforts, embodying righteousness and sacred traditions.",
        "element": "Air",
        "quality": "Movable",
        "lord": "Venus"
    },
    "Vrishchika (Scorpio)": {
        "description": "Those with Moon in Scorpio are intense, passionate, and transformative. They possess deep emotional strength and investigative abilities. They are secretive, determined, and have strong willpower.",
        "element": "Water",
        "quality": "Fixed",
        "lord": "Mars"
    },
    "Dhanussu (Sagittarius)": {
        "description": "Individuals with Moon in Sagittarius are optimistic, philosophical, and adventurous. They seek higher knowledge and truth. They are generous, honest, and have strong moral principles.",
        "element": "Fire",
        "quality": "Dual",
        "lord": "Jupiter"
    },
    "Makara (Capricorn)": {
        "description": "Those with Moon in Capricorn are disciplined, ambitious, and practical. They are hardworking, responsible, and achieve success through perseverance. They value tradition and authority.",
        "element": "Earth",
        "quality": "Movable",
        "lord": "Saturn"
    },
    "Kumbha (Aquarius)": {
        "description": "Individuals with Moon in Aquarius are innovative, humanitarian, and independent. They are progressive thinkers with unique perspectives. They value freedom and social causes.",
        "element": "Air",
        "quality": "Fixed",
        "lord": "Saturn"
    },
    "Meena (Pisces)": {
        "description": "Those with Moon in Pisces are compassionate, intuitive, and spiritual. They are imaginative, artistic, and deeply empathetic. They have strong connection to the mystical and transcendent.",
        "element": "Water",
        "quality": "Dual",
        "lord": "Jupiter"
    }
}

# Nakshatra predictions
NAKSHATRA_PREDICTIONS = {
    "Ashwini": "Individuals born in Ashwini nakshatra are swift, energetic, and pioneering. They possess healing abilities and are adventurous. They are independent, courageous, and have a youthful spirit throughout life.",
    "Bharani": "Those born in Bharani are creative, passionate, and possess strong willpower. They can handle responsibilities and transformations. They are determined, artistic, and have the ability to nurture and create.",
    "Krittika": "Individuals born in Krittika are sharp, determined, and possess cutting insight. They are purifying in nature and have strong digestive fire. They are courageous, straightforward, and seek truth.",
    "Rohini": "Those born in Rohini are attractive, creative, and materialistic. They appreciate beauty and luxury. They are charming, fertile in ideas, and have strong growth potential.",
    "Mrigashira": "Individuals born in Mrigashira are curious, searching, and gentle. They are seekers of knowledge and new experiences. They are restless, intelligent, and have refined sensibilities.",
    "Ardra": "Those born in Ardra are intense, transformative, and emotional. They experience storms and renewal. They are intelligent, research-oriented, and have the ability to destroy and rebuild.",
    "Punarvasu": "Individuals born in Punarvasu are optimistic, renewable, and philosophical. They bounce back from difficulties. They are generous, content, and have the ability to return to original state.",
    "Pushya": "Those born in Pushya are nourishing, spiritual, and auspicious. They are devoted, disciplined, and supportive. They are respected, traditional, and have the ability to provide and protect.",
    "Ashlesha": "Individuals born in Ashlesha are mystical, penetrating, and secretive. They possess hypnotic charm and psychological insight. They are cunning, protective, and have transformative wisdom.",
    "Magha": "Those born in Magha are regal, authoritative, and traditional. They honor ancestors and heritage. They are dignified, generous, and have natural leadership abilities.",
    "Purva Phalguni": "Individuals born in Purva Phalguni are creative, pleasure-loving, and artistic. They enjoy luxury and relationships. They are charming, generous, and have strong procreative abilities.",
    "Uttara Phalguni": "Those born in Uttara Phalguni are generous, helpful, and organized. They form lasting partnerships. They are reliable, kind-hearted, and have the ability to provide support.",
    "Hasta": "Individuals born in Hasta are skillful, dexterous, and clever. They are good with hands and crafts. They are humorous, intelligent, and have the ability to manifest desires.",
    "Chitra": "Those born in Chitra are artistic, charismatic, and creative. They create beautiful things. They are dynamic, fashionable, and have strong aesthetic sense.",
    "Swati": "Individuals born in Swati are independent, flexible, and diplomatic. They move like the wind. They are balanced, business-minded, and have the ability to adapt and trade.",
    "Vishakha": "Individuals born in Visakha nakshatra may exhibit pride, luxury, jealousy, linguistic skill, enemy overcoming, and occasional irritability. They tend to be ascetic yet wealthy, not easily forming friendships. According to astrology texts, they are proud, submissive to their spouse, victorious over enemies, and easily angered.",
    "Anuradha": "Those born in Anuradha are devoted, friendly, and balanced. They form deep friendships. They are diplomatic, successful, and have the ability to bridge differences.",
    "Jyeshtha": "Individuals born in Jyeshtha are protective, authoritative, and responsible. They are eldest and most accomplished. They are courageous, charitable, and have leadership abilities.",
    "Mula": "Those born in Mula are investigative, philosophical, and transformative. They get to the root of matters. They are determined, spiritual, and have the ability to destroy and rebuild.",
    "Purva Ashadha": "Individuals born in Purva Ashadha are invincible, purifying, and ambitious. They are early victors. They are optimistic, proud, and have the ability to energize and inspire.",
    "Uttara Ashadha": "Those born in Uttara Ashadha are ethical, ambitious, and responsible. They achieve lasting victory. They are determined, righteous, and have leadership qualities.",
    "Shravana": "Individuals born in Shravana are learned, listening, and connecting. They seek knowledge through hearing. They are wise, organized, and have the ability to learn and teach.",
    "Dhanishtha": "Those born in Dhanishtha are wealthy, musical, and adaptable. They are prosperous and rhythmic. They are ambitious, charitable, and have the ability to achieve material success.",
    "Shatabhisha": "Individuals born in Shatabhisha are healing, mystical, and independent. They are the hundred physicians. They are secretive, research-oriented, and have the ability to heal and discover.",
    "Purva Bhadrapada": "Those born in Purva Bhadrapada are intense, transformative, and idealistic. They are passionate about causes. They are philosophical, eccentric, and have the ability to sacrifice for higher goals.",
    "Uttara Bhadrapada": "Individuals born in Uttara Bhadrapada are wise, patient, and deep. They bring rain and prosperity. They are contemplative, stable, and have the ability to provide sustained support.",
    "Revati": "Those born in Revati are nurturing, wealthy, and spiritual. They are the final journey. They are compassionate, artistic, and have the ability to guide and protect."
}

# Tithi predictions (30 tithis - 15 Shukla Paksha + 15 Krishna Paksha)
TITHI_PREDICTIONS = {
    "Shukla Paksha Pratipada": "Being born on Pratipada, the first lunar day, may put the child's survival at risk, but if they overcome this critical phase, these individuals will be brilliant and attain great prosperity. Survival may be attributed to remedies or other counteracting factors in the horoscope. Such individuals will lead an industrious and virtuous life. As per astrological beliefs, those born on Pratipada are associated with wealth, wisdom, discernment, and beauty, receiving wealth from royalty. However, contrasting views suggest a person born on Pratipada may associate with sinners, lack wealth, cause family distress, and have an inclination towards addiction.",
    "Shukla Paksha Dwitiya": "Individuals born on Dwitiya are gentle, peaceful, and prosperous. They possess good character, are devoted to their duties, and enjoy material comforts. They are balanced in nature and maintain harmonious relationships.",
    "Shukla Paksha Tritiya": "Those born on Tritiya are courageous, energetic, and successful. They possess strong willpower and achieve their goals through determination. They are respected in society and lead a prosperous life.",
    "Shukla Paksha Chaturthi": "Individuals born on Chaturthi are intelligent, learned, and wise. They have strong analytical abilities and are skilled in various arts. They may face some obstacles but overcome them through knowledge.",
    "Shukla Paksha Panchami": "Those born on Panchami are creative, artistic, and knowledgeable. They are devoted to learning and possess refined tastes. They are respected for their wisdom and cultural accomplishments.",
    "Shukla Paksha Shashthi": "Individuals born on Shashthi are strong, victorious, and determined. They overcome enemies and obstacles. They possess good health and achieve success through persistent effort.",
    "Shukla Paksha Saptami": "Those born on Saptami are spiritual, wise, and fortunate. They are inclined towards religious practices and higher knowledge. They lead a righteous life and are respected in society.",
    "Shukla Paksha Ashtami": "Individuals born on Ashtami are intense, transformative, and powerful. They possess strong willpower and mystical abilities. They may face challenges but emerge stronger through transformation.",
    "Shukla Paksha Navami": "Those born on Navami are devoted, energetic, and victorious. They are blessed by divine grace and achieve success in their endeavors. They are courageous and righteous.",
    "Shukla Paksha Dashami": "Individuals born on Dashami are successful, prosperous, and respected. They achieve their goals and enjoy material comforts. They are balanced and lead a harmonious life.",
    "Shukla Paksha Ekadashi": "Those born on Ekadashi are spiritual, disciplined, and pure. They are devoted to higher principles and lead a righteous life. They are respected for their moral character.",
    "Shukla Paksha Dwadashi": "Individuals born on Dwadashi are prosperous, generous, and fortunate. They enjoy material success and are charitable. They are respected in society and lead a comfortable life.",
    "Shukla Paksha Trayodashi": "Those born on Trayodashi are determined, powerful, and successful. They overcome obstacles and achieve their goals. They possess strong willpower and leadership abilities.",
    "Shukla Paksha Chaturdashi": "Individuals born on Chaturdashi are intense, mystical, and transformative. They possess deep insight and spiritual abilities. They may face challenges but have the power to overcome them.",
    "Purnima": "Those born on Purnima (Full Moon) are complete, balanced, and prosperous. They possess full potential and achieve success. They are emotionally fulfilled and lead a harmonious life.",
    "Krishna Paksha Pratipada": "Individuals born on Krishna Paksha Pratipada are introspective, wise, and spiritual. They possess inner strength and the ability to let go. They are philosophical and seek deeper meaning.",
    "Krishna Paksha Dwitiya": "Those born on Krishna Paksha Dwitiya are balanced, peaceful, and contemplative. They possess inner harmony and are skilled in managing resources. They are practical and grounded.",
    "Krishna Paksha Tritiya": "Individuals born on Krishna Paksha Tritiya are determined, focused, and successful. They achieve their goals through concentrated effort. They are strategic and resourceful.",
    "Krishna Paksha Chaturthi": "Those born on Krishna Paksha Chaturthi are intelligent, analytical, and wise. They possess deep understanding and problem-solving abilities. They are respected for their knowledge.",
    "Krishna Paksha Panchami": "Individuals born on Krishna Paksha Panchami are creative, introspective, and knowledgeable. They possess refined sensibilities and are drawn to arts and culture.",
    "Krishna Paksha Shashthi": "Those born on Krishna Paksha Shashthi are strong, resilient, and victorious. They overcome challenges through inner strength. They are determined and persistent.",
    "Krishna Paksha Saptami": "Individuals born on Krishna Paksha Saptami are spiritual, wise, and contemplative. They seek inner truth and higher knowledge. They are philosophical and introspective.",
    "Krishna Paksha Ashtami": "Those born on Krishna Paksha Ashtami are mystical, powerful, and transformative. They possess deep spiritual insight and the ability to transcend limitations.",
    "Krishna Paksha Navami": "Individuals born on Krishna Paksha Navami are devoted, strong, and victorious. They overcome obstacles through spiritual strength. They are courageous and righteous.",
    "Krishna Paksha Dashami": "Those born on Krishna Paksha Dashami are balanced, successful, and wise. They achieve their goals through strategic planning. They are practical and efficient.",
    "Krishna Paksha Ekadashi": "Individuals born on Krishna Paksha Ekadashi are spiritual, disciplined, and pure. They are devoted to higher principles and possess strong moral character.",
    "Krishna Paksha Dwadashi": "Those born on Krishna Paksha Dwadashi are wise, prosperous, and generous. They possess inner wealth and are charitable. They are respected for their character.",
    "Krishna Paksha Trayodashi": "Individuals born on Krishna Paksha Trayodashi are powerful, determined, and successful. They possess strong willpower and the ability to overcome obstacles.",
    "Krishna Paksha Chaturdashi": "Those born on Krishna Paksha Chaturdashi are mystical, intense, and transformative. They possess deep spiritual abilities and insight into hidden matters.",
    "Amavasya": "Individuals born on Amavasya (New Moon) are introspective, spiritual, and transformative. They possess the ability to start anew and have deep inner strength. They are philosophical and seek spiritual growth."
}

# Karana predictions (11 karanas)
KARANA_PREDICTIONS = {
    "Bava": "Individuals born under Bava Karana are skilled, intelligent, and successful. They possess good character and are respected in society. They are balanced and lead a prosperous life.",
    "Balava": "Those born under Balava Karana are strong, powerful, and determined. They possess physical strength and courage. They overcome obstacles and achieve success through effort.",
    "Kaulava": "Individuals born under Kaulava Karana are family-oriented, traditional, and prosperous. They value heritage and maintain strong family bonds. They are respected and lead a comfortable life.",
    "Taitila": "Those born under Taitila Karana are sharp, intelligent, and analytical. They possess keen insight and problem-solving abilities. They are successful in intellectual pursuits.",
    "Gara": "Individuals born under Gara Karana are deep, mysterious, and transformative. They possess hidden strengths and the ability to overcome challenges. They are resilient and determined.",
    "Vanija": "Those born under Vanija Karana are business-minded, practical, and prosperous. They excel in commerce and trade. They are skilled in financial matters and accumulate wealth.",
    "Vishti": "Individuals born under Vishti (Bhadra) Karana may face obstacles and challenges. However, they develop strong resilience and wisdom through difficulties. They possess the ability to transform adversity into strength.",
    "Shakuni": "Those born under Shakuni Karana are strategic, intelligent, and cunning. They possess sharp intellect and the ability to plan effectively. They are resourceful and achieve their goals through clever means.",
    "Chatushpada": "Individuals born under Chatushpada Karana are stable, grounded, and practical. They possess strong foundation and the ability to build lasting structures. They are reliable and hardworking.",
    "Naga": "The individual born under Naga Karana is characterized as having a challenging nature, being restless, powerful, and possessing a wicked heart. According to the astrological insights of ancient texts, the Naga Karana native may engage in wrongful deeds, be prone to anger, and potentially cause harm to lineage through deceit and belligerence.",
    "Kimstughna": "Those born under Kimstughna Karana are transformative, powerful, and intense. They possess the ability to destroy obstacles and create new beginnings. They are strong-willed and determined."
}

# Yoga predictions (27 yogas)
YOGA_PREDICTIONS = {
    "Vishkambha": "Individuals born under Vishkambha Yoga are strong, determined, and capable of overcoming obstacles. They possess great willpower and achieve success through persistent effort.",
    "Priti": "Those born under Priti Yoga are loving, affectionate, and popular. They are liked by others and form harmonious relationships. They are gentle and kind-hearted.",
    "Ayushman": "Individuals born under Ayushman Yoga are blessed with longevity, good health, and vitality. They are energetic and lead a long, prosperous life.",
    "Saubhagya": "A person born under Saubhagya Yoga is wise, wealthy, truthful, well-behaved, strong-willed, discerning, attractive, fortunate, and confident. According to astrological texts, such an individual is happy. Psychologically, they are like a king's advisor, clever in all tasks, and deeply affectionate towards the opposite gender.",
    "Shobhana": "Those born under Shobhana Yoga are beautiful, attractive, and prosperous. They possess grace and charm. They are fortunate and lead a comfortable life.",
    "Atiganda": "Individuals born under Atiganda Yoga may face obstacles and challenges. However, they develop strong resilience and the ability to overcome difficulties through determination.",
    "Sukarma": "Those born under Sukarma Yoga are virtuous, righteous, and successful. They perform good deeds and are respected for their moral character. They lead a prosperous life.",
    "Dhriti": "Individuals born under Dhriti Yoga are patient, stable, and determined. They possess strong endurance and the ability to persevere. They are reliable and achieve long-term success.",
    "Shula": "Those born under Shula Yoga may experience pain and challenges. However, they develop strength through difficulties and possess the ability to heal and transform.",
    "Ganda": "Individuals born under Ganda Yoga may face obstacles and complications. They develop problem-solving abilities and resilience through challenges.",
    "Vriddhi": "Those born under Vriddhi Yoga are prosperous, growing, and successful. They experience expansion and increase in all areas of life. They are fortunate and wealthy.",
    "Dhruva": "Individuals born under Dhruva Yoga are stable, fixed, and reliable. They possess strong determination and the ability to maintain consistency. They are trustworthy and steadfast.",
    "Vyaghata": "Those born under Vyaghata Yoga may face conflicts and obstacles. However, they develop strong fighting spirit and the ability to overcome adversaries.",
    "Harshana": "Individuals born under Harshana Yoga are joyful, happy, and optimistic. They spread happiness and are cheerful in nature. They are fortunate and lead a pleasant life.",
    "Vajra": "Those born under Vajra Yoga are strong, powerful, and indestructible. They possess diamond-like qualities and the ability to withstand any challenge. They are determined and successful.",
    "Siddhi": "Individuals born under Siddhi Yoga are accomplished, successful, and spiritually advanced. They achieve their goals and possess special abilities. They are fortunate and respected.",
    "Vyatipata": "Those born under Vyatipata Yoga may face unexpected changes and challenges. However, they develop adaptability and the ability to handle crises effectively.",
    "Variyan": "Individuals born under Variyan Yoga are excellent, superior, and distinguished. They possess outstanding qualities and achieve high status. They are respected and successful.",
    "Parigha": "Those born under Parigha Yoga may face restrictions and obstacles. However, they develop the ability to break through barriers and achieve freedom.",
    "Shiva": "Individuals born under Shiva Yoga are auspicious, spiritual, and transformative. They are blessed with divine grace and lead a righteous life. They are respected and prosperous.",
    "Siddha": "Those born under Siddha Yoga are accomplished, perfected, and successful. They achieve mastery in their fields and possess special abilities. They are highly respected.",
    "Sadhya": "Individuals born under Sadhya Yoga are achievable, successful, and divine. They accomplish their goals and are blessed with spiritual qualities. They are fortunate and respected.",
    "Shubha": "Those born under Shubha Yoga are auspicious, fortunate, and prosperous. They are blessed with good fortune and lead a happy life. They are respected and successful.",
    "Shukla": "Individuals born under Shukla Yoga are pure, bright, and virtuous. They possess clarity and righteousness. They are respected for their moral character and lead a prosperous life.",
    "Brahma": "Those born under Brahma Yoga are wise, spiritual, and creative. They possess divine knowledge and creative abilities. They are highly respected and lead a righteous life.",
    "Indra": "Individuals born under Indra Yoga are powerful, authoritative, and successful. They possess leadership qualities and achieve high status. They are prosperous and respected.",
    "Vaidhriti": "Those born under Vaidhriti Yoga may face obstacles and separations. However, they develop independence and the ability to stand alone. They are resilient and determined."
}

# Moon Transit (Gochara) Predictions - House positions from Janma Rasi
MOON_TRANSIT_PREDICTIONS = {
    1: "The Moon transiting your own sign brings physical comfort, good health, and mental peace. You feel confident and attractive. Success in your efforts and gain of wealth are likely.",
    2: "The Moon in the 2nd house may cause some financial fluctuations or family tension. Watch your speech and avoid arguments. Minor eye or facial discomfort is possible.",
    3: "The Moon in the 3rd house is highly favorable. It brings courage, victory over obstacles, and gain of wealth. Good news from siblings or short travels will be pleasant.",
    4: "The Moon in the 4th house can cause domestic discomfort or mental worry. You may feel a lack of peace at home. Avoid disputes with relatives and take care of your health.",
    5: "The Moon in the 5th house might lead to mental anxiety or concerns about children. Avoid gambling or risky investments. You may feel a bit restless or indecisive.",
    6: "The Moon in the 6th house brings victory over enemies and recovery from illness. You will find relief from debts or long-standing problems. Success in work is indicated.",
    7: "The Moon in the 7th house brings happiness in relationships and partnerships. You will enjoy good food, comfort, and social respect. A pleasant time with your spouse or partner.",
    8: "The Moon in the 8th house requires caution. You may face obstacles, sudden expenses, or health issues. Avoid risky activities and stay calm through mental stress.",
    9: "The Moon in the 9th house may cause some delays in fortune or fatigue from travel. You might feel a bit spiritually inclined but face minor hurdles in planned activities.",
    10: "The Moon in the 10th house is very good for career and social status. You will receive honor, respect, and success in your professional life. Your efforts are recognized.",
    11: "The Moon in the 11th house brings gains of wealth, fulfillment of desires, and happiness from friends. New opportunities and financial prosperity are highly likely.",
    12: "The Moon in the 12th house indicates high expenditure or mental fatigue. You may need extra rest. Avoid impulsive spending and keep a low profile to maintain peace."
}

