"""
Intent extraction and NLP intelligence engine for Jan-Vani.
Extracts category, sub_category, urgency, duration, summary, and confidence
from vernacular Indian languages (Hindi, Marathi, Bengali, Gujarati, Kannada,
Malayalam, Punjabi, Tamil, Telugu) and English complaints.
Supports both LLM API calling and deterministic local semantic parsing.
"""

import os
import re
import json
from typing import Dict, Any, Tuple, Optional
from intelligence.schema import GrievanceExtraction, FallbackExtraction

# Keywords & dialect markers across all supported Indian languages
PATTERNS = {
    "Water Supply": {
        "strong_keywords": [
            "पिण्याचे पाणी", "जलकल", "पानी की सप्लाई", "पीने का पानी", "पिण्याच्या पाण्याची",
            "পানীয় জল", "জল সরবরাহ", "নলকূপ", "পাইপলাইন",
            "પાણી પુરવઠો", "પીવાનું પાણી", "પીવાના પાણીની", "વોટર",
            "ಕುಡಿಯುವ ನೀರು", "ಕುಡಿಯುವ ನೀರಿನ", "ನೀರು ಸರಬರಾಜು", "ನಲ್ಲಿಯಲ್ಲಿ",
            "കുടിവെള്ളം", "കുടിവെള്ള", "ശുദ്ധജലം", "ജലവിതരണം", "പൈപ്പിൽ", "പൈപ്പിലൂടെ",
            "ਪੀਣ ਵਾਲਾ ਪਾਣੀ", "ਜਲ ਸਪਲਾਈ", "ਨਲਕਾ", "ਪਾਈਪਲਾਈਨ",
            "குடிநீர்", "குடிநீரில்", "குடிநீர் விநியோகம்",
            "మంచినీటి", "తాగునీరు", "మంచినీరు", "కుళాయిల్లో"
        ],
        "keywords": [
            "पानी", "जल", "नल", "गळती", "पाणी", "पाइप", "पिण्याचे पाणी",
            "जलकल", "सप्लाई", "टुटा पाइप", "water", "leak", "pipe", "tap",
            "জল", "পানি", "পাইপ",
            "પાણી", "નળ", "પાઇપ",
            "ನೀರು", "ಪೈಪ್",
            "വെള്ളം", "പൈപ്പ്",
            "ਪਾਣੀ", "ਪਾਈਪ",
            "தண்ணீர்", "பைப்",
            "నీరు", "పైపు", "పైప్"
        ],
        "sub_categories": {
            "Leakage": [
                "लीक", "गळती", "फुटा", "फुटला", "बहाव", "गळत", "leak", "burst",
                "লিকেজ", "গলતર", "ಸೋರಿಕೆ", "ചോർച്ച", "ਲੀਕ", "கசிவு", "లీకేజ్",
                "ফেটে", "તૂટી", "ഒഴുക്ക്", "பொட்டல்", "പగిలిపోయింది"
            ],
            "Disruption": [
                "बंद", "नाही", "आला नाही", "नहीं आया", "कटौती", "disruption", "no water",
                "ठप", "येत नाही", "नहीं आया",
                "বন্ধ", "બંધ", "ನಿಲ್ಲಿಸಲಾಗಿದೆ", "ತಡಸ್ಸപ്പെട്ടു", "ਬੰਦ", "நிறுத்தம்", "నిలిచిపోయింది",
                "সংকট", "ઓછું", "ഇല്ല", "വരவில்லை", "రాలేదు"
            ],
            "Contamination": [
                "गंदा", "घाण", "दुर्गंधी", "बदबू", "गढूळ", "dirty", "contaminated",
                "নোংরা", "ગંદુ", "ಕೊಳಕು", "മലിനമായ", "ਗੰਦਾ", "அசுத்தமான", "కలుషిత"
            ]
        }
    },
    "Roads": {
        "strong_keywords": [
            "खड्डा पडला", "खड्डा", "गड्ढा", "डामर", "डांबरीकरण", "फुटपाथ", "पादचारी", "रस्ता खचला",
            "ভাঙা রাস্তা", "ফুটপাথ", "পিচ",
            "તૂટેલા રોડ", "તૂટેલો રોડ", "ખાડા", "ફૂટપાથ", "પાદચારીઓ",
            "ಹಾಳಾದ ರಸ್ತೆ", "ಕಾಲುದಾರಿ", "ಪಾದಚಾರಿಗಳಿಗೆ", "ಫುಟ್‌ಪಾತ್",
            "തകർന്ന റോഡ്", "നടപ്പാത", "ടാറിങ്", "കാൽനടയാത്രക്കാർക്ക്", "ഫുട്പാത്ത്",
            "ਖਸਤਾ", "ਫੁੱਟਪਾਥ", "ਲੁੱਕ",
            "சேதமடைந்த சாலை", "நடைபாதை", "பாதசாரிகள்", "தார் பெயர்ந்து",
            "పాదచారుల", "ఫుట్‌పాత్", "తారు"
        ],
        "keywords": [
            "सड़क", "रस्ता", "गड्ढा", "मार्ग", "रोड", "डामर", "फुटपाथ",
            "पूल", "road", "pothole", "street", "highway",
            "রাস্তা", "রাস্তায়", "গর্ত", "সড়ক", "ডামার",
            "રસ્તો", "રસ્તા", "ખાડો", "માર્ગ", "રોડ", "ડામર",
            "ರಸ್ತೆ", "ರಸ್ತೆಯಲ್ಲಿ", "ರಸ್ತೆಯ", "ಗುಂಡಿ", "ಡಾಂಬರು",
            "റോഡ്", "റോഡിൽ", "റോഡിലെ", "കുഴി", "കുഴികൾ",
            "ਸੜਕ", "ਟੋਆ", "ਰੋਡ",
            "சாலை", "சாலையில்", "குழி", "தார்",
            "రోడ్డు", "రహదారి", "రహదారిపై", "గుంత"
        ],
        "sub_categories": {
            "Damage": [
                "खड्डा", "गड्ढा", "तुटला", "टूटा", "खराब", "दुरुस्ती", "pothole", "broken",
                "গর্ত", "ખાડો", "ಗುಂಡಿ", "കുഴി", "ਟੋਆ", "குழி", "గుంత"
            ],
            "Disruption": [
                "जाम", "बंद", "अवरोध", "block", "closed",
                "অবরুদ্ধ", "જામ", "ನಿರ್ಬಂಧ", "ತಡಸ್സം", "ਜਾਮ", "தடை", "అవరోధం"
            ]
        }
    },
    "Drainage": {
        "strong_keywords": [
            "गटार", "गटाराचे", "तुंबले", "ड्रेनेज", "ड्रेनेज पाइपलाइन", "सीवर", "नाली", "नाला", "नाला ओसंडून", "गंदे नाले",
            "নর্দমা", "পয়ঃনিষ্কাশন", "সিউয়ার", "ড্রেন", "ড্রেনের",
            "ગટર", "ગટરનું", "ડ્રેનેજ", "સીવર",
            "ಚರಂಡಿ", "ಚರಂಡಿ ಕಟ್ಟಿಕೊಂಡು", "ಡ್ರೈನೇಜ್", "ಗಟಾರ",
            "ഓട", "ഓവുചാൽ", "ഓവുചാലിന്റെ", "ഡ്രെയിനേജ്",
            "ਨਾਲਾ", "ਨਾਲੇ", "ਸੀਵਰ", "ਸੀਵਰੇਜ", "ਗਟਰ",
            "சாக்கடை", "வடிகால்", "கழிவுநீர்",
            "మురుగు కాలువ", "మురుగునీరు", "డ్రైనేజీ", "మురుగు", "కాలువలో", "పూడిక", "కాలువ"
        ],
        "keywords": [
            "नाली", "नाला", "ड्रेनेज", "गटार", "तुंबले", "उतू",
            "सीवर", "drain", "gutter", "sewage", "drainage",
            "পয়ঃনিষ্কাশন", "ড্রেন",
            "ચોક",
            "ಮಳೆಗಾಲದಲ್ಲಿ ಚರಂಡಿ",
            "മഴവെള്ളം ഓടയിലൂടെ",
            "கழிவு",
            "కాలువ"
        ],
        "sub_categories": {
            "Disruption": [
                "तुंबले", "अटकले", "जाम", "चौक", "blocked", "clogged", "overflow",
                "আটকে", "ચોક", "ತುಂಬಿ", "ತಡಸ್സം", "ਜਾਮ", "அடைப்பு", "జామ్"
            ],
            "Contamination": [
                "घाण", "दुर्गंधी", "बदबू", "मच्छर", "smell", "filth",
                "দুর্গন্ধ", "ગંદકી", "ದುರ್ವಾಸನೆ", "ദുർഗന്ധം", "ਬਦਬੂ", "துர்நாற்றம்", "దుర్వాసన"
            ]
        }
    },
    "Power": {
        "strong_keywords": [
            "विजेच्या", "विजेचा", "स्ट्रीट लाइट", "ट्रांसफार्मर जल", "बिजली का तार", "बिजली का खंभा", "बिजली गुल", "वोल्टेज",
            "বিদ্যুৎ", "কারেন্ট", "ট্রান্সফরমার", "ট্রান্সফরমারে", "বৈদ্যুতিক তার", "খুঁটি", "বিদ্যুতের খুঁটি",
            "વીજળી", "ટ્રાન્સફોર્મર", "વીજળીનો તાર", "વીજળીનો થાંભલો", "વીજળીનો વાયર",
            "ವಿದ್ಯುತ್", "ವಿದ್ಯುತ್ ಕಡಿತ", "ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್", "ಕರೆಂಟ್ ವೈರ್", "ವಿದ್ಯುತ್ ಕಂಬ",
            "വൈദ്യുതി", "വൈദ്യുത പോസ്റ്റ്", "ട്രാൻസ്ഫോർമർ", "ഇലക്ട്രിക് ലൈൻ", "കറണ്ട്",
            "ਬਿਜਲੀ", "ਟਰਾਂਸਫਾਰਮਰ", "ਬਿਜਲੀ ਦੀ ਤਾਰ", "ਬਿਜਲੀ ਦਾ ਖੰਭਾ", "ਬਿਜਲੀ ਗੁੱਲ",
            "மின்வெட்டு", "மின்மாற்றி", "மின்கம்பி", "மின்கம்பம்", "மின்சாரம்",
            "విద్యుత్", "ట్రాన్స్‌ఫార్మర్", "కరెంట్ వైర్", "విద్యుత్ స్తంభం", "కరెంట్ పోయి"
        ],
        "keywords": [
            "बिजली", "लाइट", "वीज", "करंट", "वायर", "पोल", "ट्रांसफार्मर", "खंभा",
            "अंधार", "पावर", "electricity", "power", "light", "wire", "pole",
            "কারেন্টের",
            "તાર", "થાંભલો",
            "ಕಂಬ", "ಕತ್ತಲೆಯಲ್ಲಿದೆ",
            "പോസ്റ്റ്",
            "ਖੰਭਾ",
            "இருளில்",
            "చీకటి"
        ],
        "sub_categories": {
            "Disruption": [
                "गुल", "गेली", "कट", "बंद", "नाही", "blackout", "cut", "failure",
                "বিভ্রাট", "ગુલ", "ವಿದ್ಯುತ್ ಕಡಿತ", "വൈദ്യുതി നിലച്ചു", "ਬੰਦ", "மின்வெட்டு", "విద్యుత్ అంతరాయం"
            ],
            "Damage": [
                "तूट", "टूटा", "झुकला", "धूर", "स्पार्क", "spark", "fallen",
                "স্পার্ক", "સ્પાર્ક", "ಸ್ಪಾರ್ಕ್", "തീപ്പൊരി", "ਸਪਾਰਕ", "தீப்பொறி", "స్పార్కింగ్"
            ]
        }
    },
    "Garbage": {
        "strong_keywords": [
            "कचरापेटी", "उकिरड्यावर", "कचरा गाडी", "डंपिंग ग्राउंड", "कूड़ेदान", "कचरा उठाने", "कूड़े का ढेर", "सफाई कर्मचारी",
            "আবর্জনা", "আবর্জনার", "ডাস্টবিন", "সফাই", "সাফাই", "ময়লা",
            "કચરો", "કચરા", "કચરાના", "કચરાપેટી", "સફાઈ કામદારો",
            "ಕಸ", "ಕಸದ ಬುಟ್ಟಿ", "ಕಸದ ವಾಹನ", "ಕಸ ಸಂಗ್ರಹವಾಗಿ", "ಕಸ ಕೊಳೆತು", "ಸ್ವಚ್ಛತಾ",
            "മാലിന്യം", "മാലിന്യ", "മാലിന്യക്കൂമ്പാരം", "ഡസ്റ്റ്ബിൻ", "ചപ്പുചവറുകൾ", "വേസ്റ്റ് എടുക്കാൻ",
            "ਕੂੜਾ", "ਕੂੜੇ", "ਕੂੜੇਦਾਨ", "ਕੂੜੇ ਦੇ ਢੇਰ", "ਸਫਾਈ ਵਾਲੀ ਗੱਡੀ",
            "குப்பை", "குப்பைகளை", "குப்பை குவியல்", "குப்பைத்தொட்டி", "குப்பை வண்டி",
            "చెత్త", "చెత్త కుప్పలు", "చెత్తకుండీ", "చెత్త వాహనం", "వ్యర్థాలు"
        ],
        "keywords": [
            "कचरा", "कूड़ा", "कचरापेटी", "घाण", "उकिरडा", "डंपिंग", "सफाई",
            "garbage", "trash", "waste", "dump",
            "ময়লার",
            "ગંદકી",
            "ಗಲೀಜು",
            "വേസ്റ്റ്",
            "ਗੰਦਗੀ",
            "துப்புரவு",
            "పారిశుద్ధ్య"
        ],
        "sub_categories": {
            "Disruption": [
                "उचलला नाही", "पडून आहे", "साचला", "पड़ा है", "not picked", "accumulated",
                "তুলে নেওয়া হয়নি", "ઉપાડ્યો નથી", "ಎತ್ತಿಲ್ಲ", "നീക്കം ചെയ്തില്ല", "ਚੁੱਕਿਆ ਨਹੀਂ", "அள்ளவில்லை", "ఎత్తలేదు"
            ],
            "Contamination": [
                "दुर्गंधी", "घाण", "सड", "rotten", "smell",
                "পচা", "સડી", "ಕೊಳೆತ", "ചീഞ്ഞ", "ਸੜ", "அழுகிய", "కుళ్ళిన"
            ]
        }
    }
}

DURATION_PATTERNS = [
    (r"(\d+)\s*(दिवस|दिन|days|day|দিন|દિવસ|ದಿನ|ദിവസം|ਦਿਨ|நாட்களாக|రోజులుగా)", lambda m: f"{m.group(1)} days"),
    (r"(दोन|तीन|चार|पाच)\s*दिवस", lambda m: f"{m.group(0)}"),
    (r"(दो|तीन|चार|पांच)\s*दिन", lambda m: f"{m.group(0)}"),
    (r"(তিন|চার|পাঁচ)\s*দিন", lambda m: f"{m.group(0)}"),
    (r"(ત્રણ|ચાર|પાંચ)\s*દિવસ", lambda m: f"{m.group(0)}"),
    (r"(ಮೂರು|ನಾಲ್ಕು)\s*ದಿನ", lambda m: f"{m.group(0)}"),
    (r"(മൂന്ന്|നാല്)\s*ദിവസം", lambda m: f"{m.group(0)}"),
    (r"(ਤਿੰਨ|ਚਾਰ)\s*ਦਿਨ", lambda m: f"{m.group(0)}"),
    (r"एक\s*आठवडा|एक\s*सप्ताह|one\s*week|এক\s*সপ্তাহ|એક\s*અઠવાડિયા|ಒಂದು\s*ವಾರ|ഒരു\s*ആഴ്ച|ਇੱਕ\s*ਹਫ਼ਤਾ|ஒரு\s*வாரம்|ఒక\s*వారం", lambda m: "1 week"),
    (r"कालपासून|कल से|since\s*yesterday", lambda m: "since yesterday"),
    (r"आज सकाळपासून|आज सुबह से", lambda m: "since today morning")
]

URGENCY_HIGH_MARKERS = [
    "तातडीने", "लगेच", "धोका", "अपघात", "मोठा", "फार", "लवकर",
    "तुरंत", "खतरा", "दुर्घटना", "बड़ा", "बहुत ज्यादा", "urgent", "danger", "emergency",
    "জরুরি", "অবিলম্বে", "বিপদ", "তাৎकालिक", "ખતરો", "અકસ્માತ", "ತುರ್ತು", "ಅಪಾಯ",
    "അടിയന്തരമായി", "അപകടം", "ਤੁਰੰਤ", "ਖਤਰਾ", "உடனடியாக", "ஆபத்து", "వెంటనే", "ప్రమాదం"
]

def extract_duration(text: str) -> Optional[str]:
    for pattern, formatter in DURATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return formatter(match)
    return None

def extract_intent_local(transcript: str, language: str = "auto") -> GrievanceExtraction:
    """
    Deterministic rule-based NLP intent parser for all supported vernacular languages.
    Provides reliable, schema-validated output.
    """
    text_lower = transcript.lower()

    # Score categories
    category_scores = {}
    sub_category_matches = {}

    for cat, data in PATTERNS.items():
        score = 0
        for skw in data.get("strong_keywords", []):
            if skw.lower() in text_lower:
                score += 5

        for kw in data.get("keywords", []):
            if kw.lower() in text_lower:
                score += 2

        matched_sub = "Other"
        for sub, sub_kws in data.get("sub_categories", {}).items():
            for skw in sub_kws:
                if skw.lower() in text_lower:
                    matched_sub = sub
                    score += 1
                    break

        category_scores[cat] = score
        sub_category_matches[cat] = matched_sub

    best_cat = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_cat]

    if best_score == 0:
        # Fallback to Other
        best_cat = "Other"
        best_sub = "Other"
        confidence = 0.40
    else:
        best_sub = sub_category_matches[best_cat]
        confidence = min(0.95, 0.65 + (best_score * 0.05))

    # Determine urgency
    urgency = "Medium"
    if any(marker in text_lower for marker in URGENCY_HIGH_MARKERS):
        urgency = "High"
    elif best_cat in ["Water Supply", "Power"] and any(w in text_lower for w in ["बंद", "বন্ধ", "ನಿಲ್ಲಿಸಲಾಗಿದೆ", "നിലച്ചു", "തുണ്ടിക്കப்பட்டுள்ளது", "నిలిచిపోయింది"]):
        urgency = "High"
    elif best_cat in ["Garbage"] and not any(marker in text_lower for marker in URGENCY_HIGH_MARKERS):
        urgency = "Low"

    duration = extract_duration(text_lower)

    # Generate one English sentence summary
    summary_parts = []
    if best_cat == "Water Supply":
        summary_parts.append(f"Water supply {best_sub.lower()} reported")
    elif best_cat == "Roads":
        summary_parts.append(f"Road {best_sub.lower()} and pothole issue")
    elif best_cat == "Drainage":
        summary_parts.append(f"Drainage blockage causing sewage overflow")
    elif best_cat == "Power":
        summary_parts.append(f"Electricity outage and power failure")
    elif best_cat == "Garbage":
        summary_parts.append(f"Garbage accumulation without clearance")
    else:
        summary_parts.append("Civic issue reported by citizen")

    if duration:
        summary_parts.append(f"lasting for {duration}")

    summary_en = " ".join(summary_parts) + "."

    # Construct and validate through Pydantic
    try:
        extraction = GrievanceExtraction(
            category=best_cat,
            sub_category=best_sub,
            urgency=urgency,
            duration_text=duration,
            summary_en=summary_en,
            confidence=confidence
        )
        return extraction
    except Exception:
        fallback = FallbackExtraction()
        return GrievanceExtraction(
            category=fallback.category,
            sub_category=fallback.sub_category,
            urgency=fallback.urgency,
            duration_text=fallback.duration_text,
            summary_en=fallback.summary_en,
            confidence=fallback.confidence
        )

def parse_complaint(transcript: str, language: str = "auto") -> Dict[str, Any]:
    """
    Main entry point for intent parsing.
    Returns validated dict adhering to Section 3.3.
    """
    extraction = extract_intent_local(transcript, language)
    return extraction.model_dump()
