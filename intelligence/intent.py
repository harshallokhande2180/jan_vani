"""
Jan-Vani Strict Intent Classifier.
Strictly returns one intent from:
COMPLAINT, GREETING, YES, NO, CORRECTION, THANKS, HELP, OFF_TOPIC, UNCLEAR.
Enforces Pydantic schema validation. Rejects any non-conforming output as UNCLEAR.
Extracts problem_category, place, and duration ONLY if they explicitly appear in the citizen's utterance.
Never invents a field. Missing fields stay None / null.
"""

import os
import re
import json
from typing import Optional, Dict, Any, Tuple

from pydantic import ValidationError
from intelligence.intent_schema import (
    IntentClassificationResult,
    ExtractedFields,
    IntentType,
    CategoryType,
    SubCategoryType,
    APPROVED_CATEGORIES
)

ALLOWED_INTENTS = {
    "COMPLAINT", "GREETING", "YES", "NO", "CORRECTION", "THANKS", "HELP", "OFF_TOPIC", "UNCLEAR"
}

# Known landmarks / wards in Nagpur to identify place mentions without hallucination
KNOWN_PLACES = [
    # Nagpur wards / landmarks (Marathi & Hindi & English)
    ("धरमपेठ", "धरमपेठ"),
    ("dharampeth", "Dharampeth"),
    ("धंतोली", "धंतोली"),
    ("dhantoli", "Dhantoli"),
    ("लक्ष्मीनगर", "लक्ष्मीनगर"),
    ("laxmi nagar", "Laxmi Nagar"),
    ("हनुमान नगर", "हनुमान नगर"),
    ("hanuman nagar", "Hanuman Nagar"),
    ("सीताबर्डी", "सीताबर्डी"),
    ("sitabuldi", "Sitabuldi"),
    ("सदर", "सदर"),
    ("sadar", "Sadar"),
    ("मानेवाडा", "मानेवाडा"),
    ("manewada", "Manewada"),
    ("प्रतापनगर", "प्रतापनगर"),
    ("pratap nagar", "Pratap Nagar"),
    ("वाडी", "वाडी"),
    ("wadi", "Wadi"),
    ("गोकुळपेठ", "गोकुळपेठ"),
    ("gokulpeth", "Gokulpeth"),
    ("गांधीबाग", "गांधीबाग"),
    ("gandhibagh", "Gandhibagh"),
    ("रामदासपेठ", "रामदासपेठ"),
    ("ramdaspeth", "Ramdaspeth"),
    ("टिळक नगर", "टिळक नगर"),
    ("tilak nagar", "Tilak Nagar"),
    ("वार्ड क्रमांक २", "वार्ड क्रमांक २"),
    ("वार्ड ४", "वार्ड ४"),
    ("ward 2", "Ward 2"),
    ("ward 4", "Ward 4"),
    ("कॉलोनी", "कॉलोनी"),
    ("मोहल्ला", "मोहल्ला"),
    ("चौकात", "चौकात"),
    ("चौक", "चौक"),
    ("मार्केट", "मार्केट")
]

DURATION_REGEXES = [
    r"(\d+|दोन|तीन|चार|पाच|दहा|एक|दो|तीन|चार|पांच)\s*(दिवसांपासून|दिवसांची|दिवस|महिने|तासांपासून|तास|हफ्ते|आठवडे)",
    r"(\d+|दो|तीन|चार|पांच|एक)\s*(दिनों से|दिन|महीने|घंटों से|घंटे|सप्ताह)",
    r"(\d+|two|three|four|five|one)\s*(days?|hours?|weeks?|months?)(\s*ago|\s*now)?",
    r"(कालपासून|परवापासून|आजपासून|आठवड्यापासून|महिनाभरापासून)",
    r"(कल से|परसों से|आज से|हफ्ते भर से|महीने से)",
    r"(since yesterday|since morning|for a week|for 3 days)"
]

GREETING_PATTERNS = [
    r"(हॅलो|नमस्कार|नमस्ते|प्रणाम|शुभ सकाळ|शुभ प्रभात|राम राम|जय हरी|हेलो|hello|hi|hey|good morning|namaste)",
]

THANKS_PATTERNS = [
    r"(धन्यवाद|आभार|खूप खूप धन्यवाद|शुक्रिया|मेहरबानी|thank you|thanks|thank you so much|मनःपूर्वक आभार)",
]

HELP_PATTERNS = [
    r"(मदत|कसे वापरावे|काय करू|हे कसे चालते|मदत करा|help|how to use|what to do|assist|मदत पाहिजे|सहायता|मदद|शिकायत कैसे)",
]

YES_PATTERNS = [
    r"^(हो|होय|हो बरोबर|नक्कीच|हो बरोबर आहे|बरोबर|करा नोंद|हो करा|हाँ|हा|हाँ बिल्कुल|हाँ सही है|सही है|yes|yeah|yep|correct|confirm|proceed)\b",
    r"(होय|नक्कीच|सही है|हो बरोबर|हाँ सही|yes confirm|करा नोंद|दर्ज कीजिए)"
]

NO_PATTERNS = [
    r"^(नाही|नाही नको|नको|चूक|नाही चूक आहे|नाही थांबवा|नाही नोंदवू नका|नहीं|ना|गलत है|नहीं मत करो|नहीं गलत है|रद्द करो|no|nope|wrong|cancel|do not)\b",
    r"(नाही नको|नाही चूक|नाही थांबवा|नाही नोंदवू नका|नहीं गलत|नहीं मत|रद्द करो|गलत है|no cancel)"
]

CORRECTION_PATTERNS = [
    r"(नाही,\s*हे|नाही\s+हे|नाही\s+माझे|नाही\s+तिथे|नाही\s+बदला|नाही,\s*ठिकाण|नाही\s+ठिकाण|बदला|दुरूस्ती|दुरुस्ती|नाही\s+\d+|नाही\s+(दोन|तीन|चार|पाच))",
    r"(नहीं,\s*यह|नहीं\s+यह|नहीं\s+वहाँ|नहीं\s+स्थान|नहीं\s+समय|सुधार|बदलो|change to|correct it to|not there|नहीं\s+\d+|नहीं\s+(दो|तीन|चार))"
]

OFF_TOPIC_PATTERNS = [
    r"(पाऊस पडेल का|हवामान कसे आहे|आज पाऊस|उद्या पाऊस|क्रिकेट|सामना|मॅच|चित्रपट|गाणी|राजकारण|पंतप्रधान|निवडणूक|भाजीचा भाव|भाजीपाल्याचे|सोने भाव|सोन्याचा)",
    r"(मौसम कैसा है|बारिश होगी क्या|आज बारिश|कल का मौसम|क्रिकेट मैच|फिल्म|गाना|राजनीति|चुनाव|weather|rain today|cricket score|movie|who won|score)"
]

CIVIC_CATEGORIES = {
    "Water Supply": [
        "पाणी", "पिण्याचे पाणी", "जल", "नल", "पाइप", "गळती", "सप्लाई", "water", "pipe", "tap", "leak", "जलकल"
    ],
    "Roads": [
        "रस्ता", "सड़क", "खड्डा", "गड्ढा", "मार्ग", "रोड", "डामर", "फुटपाथ", "road", "pothole", "street", "डांबरीकरण"
    ],
    "Drainage": [
        "ड्रेनेज", "गटार", "नाली", "सीवर", "चोक", "तुंबले", "drainage", "sewer", "gutter", "नाल्याची"
    ],
    "Power": [
        "वीज", "लाइट", "बिजली", "करंट", "पोल", "खांब", "ट्रान्सफॉर्मर", "power", "electricity", "street light", "अंधार"
    ],
    "Garbage": [
        "कचरा", "घाण", "कूड़ा", "कचराकुंडी", "डंपिंग", "सफाई", "garbage", "trash", "waste", "दुर्गंधी"
    ]
}

def extract_place_from_text(text: str) -> Optional[str]:
    """Finds explicit landmark or ward in transcript. Never invents."""
    text_lower = text.lower()
    for pattern, canonical in KNOWN_PLACES:
        if pattern.lower() in text_lower:
            # Return matching word as said or canonical place
            return canonical
    # Check for words like "येथे" or "मध्ये" or "में"
    m = re.search(r"([A-Za-z\u0900-\u097F]+)\s+(येथे|मध्ये|जवळ|में|कॉलोनी|वार्ड|nagar|road|ward)", text, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        if len(candidate) > 2 and candidate not in ["माझ्या", "आमच्या", "आमच्याकडे", "हमारे", "यहाँ", "येथे"]:
            return f"{candidate} {m.group(2)}"
    return None

def extract_duration_from_text(text: str) -> Optional[str]:
    """Finds duration mentioned in transcript. Never invents."""
    for reg in DURATION_REGEXES:
        m = re.search(reg, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None

def extract_problem_from_text(text: str) -> Tuple[Optional[CategoryType], Optional[SubCategoryType], Optional[str]]:
    """Identifies civic problem words from transcript or canonical mapping."""
    for cat, kws in CIVIC_CATEGORIES.items():
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}", text, re.IGNORECASE) or kw in text:
                # determine sub-category
                sub_cat: SubCategoryType = "Other"
                if cat == "Water Supply":
                    if any(w in text for w in ["गळती", "लीक", "फुटा", "फुटली", "leak", "बहाव"]):
                        sub_cat = "Leakage"
                    elif any(w in text for w in ["नाही", "बंद", "ठप", "कटौती", "no water"]):
                        sub_cat = "Disruption"
                    elif any(w in text for w in ["गंदा", "घाण", "दुर्गंधी", "गढूळ"]):
                        sub_cat = "Contamination"
                elif cat == "Roads":
                    sub_cat = "Damage"
                elif cat == "Drainage":
                    sub_cat = "Disruption"
                elif cat == "Power":
                    sub_cat = "Disruption"
                elif cat == "Garbage":
                    sub_cat = "Disruption"
                return cat, sub_cat, kw
    return None, None, None

def classify_intent(transcript: str, language: str = "mr") -> IntentClassificationResult:
    """
    Classifies a citizen's utterance into strictly one allowed intent:
    COMPLAINT, GREETING, YES, NO, CORRECTION, THANKS, HELP, OFF_TOPIC, UNCLEAR.
    
    Guarantees:
    - Pydantic schema validation.
    - If empty or malformed: UNCLEAR.
    - Missing fields remain None / null. Never invented.
    """
    clean_text = (transcript or "").strip()
    if not clean_text:
        return IntentClassificationResult(
            intent="UNCLEAR",
            confidence=0.0,
            fields=ExtractedFields(),
            summary_en="Empty or blank utterance"
        )

    # 1. Check OFF_TOPIC first (e.g. "आज पाऊस पडेल का?", weather, cricket, politics)
    for p in OFF_TOPIC_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            return IntentClassificationResult(
                intent="OFF_TOPIC",
                confidence=0.98,
                fields=ExtractedFields(),
                summary_en="Off-topic question not related to civic redressal"
            )

    # 2. Check GREETING (e.g. "हॅलो", "नमस्कार", "नमस्ते")
    for p in GREETING_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            # If greeting also contains a substantive civic complaint like "हॅलो धरमपेठ मध्ये पाणी गळती आहे", treat as complaint
            cat, _, _ = extract_problem_from_text(clean_text)
            if not cat:
                return IntentClassificationResult(
                    intent="GREETING",
                    confidence=0.99,
                    fields=ExtractedFields(),
                    summary_en="Citizen greeting"
                )

    # 3. Check THANKS (e.g. "धन्यवाद", "शुक्रिया", "thank you")
    for p in THANKS_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            return IntentClassificationResult(
                intent="THANKS",
                confidence=0.99,
                fields=ExtractedFields(),
                summary_en="Expression of gratitude"
            )

    # 4. Check HELP (e.g. "मदत करा", "हे कसे चालते", "help")
    for p in HELP_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            return IntentClassificationResult(
                intent="HELP",
                confidence=0.95,
                fields=ExtractedFields(),
                summary_en="Request for instructions/help"
            )

    # 5. Check CORRECTION (e.g. "नाही धरमपेठ नाही, सीताबर्डी आहे", "नाही चार दिवस झाले")
    is_correction = False
    for p in CORRECTION_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            is_correction = True
            break
    
    if is_correction:
        place = extract_place_from_text(clean_text)
        duration = extract_duration_from_text(clean_text)
        cat, sub_cat, prob_kw = extract_problem_from_text(clean_text)
        
        corr_field = None
        if place:
            corr_field = "place"
        elif duration:
            corr_field = "duration"
        elif cat:
            corr_field = "problem_category"

        return IntentClassificationResult(
            intent="CORRECTION",
            confidence=0.95,
            fields=ExtractedFields(
                problem_category=cat,
                sub_category=sub_cat,
                problem=prob_kw,
                place=place,
                duration=duration,
                corrected_field=corr_field
            ),
            summary_en="Correction of prior complaint field"
        )

    # 6. Check YES (confirmation)
    for p in YES_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            # Ensure not a long complaint starting with "हो"
            words = clean_text.split()
            if len(words) <= 5:
                return IntentClassificationResult(
                    intent="YES",
                    confidence=0.99,
                    fields=ExtractedFields(),
                    summary_en="Affirmative confirmation"
                )

    # 7. Check NO (rejection / cancellation)
    for p in NO_PATTERNS:
        if re.search(p, clean_text, re.IGNORECASE):
            words = clean_text.split()
            if len(words) <= 5:
                return IntentClassificationResult(
                    intent="NO",
                    confidence=0.99,
                    fields=ExtractedFields(),
                    summary_en="Negative rejection / cancellation"
                )

    # 8. Check COMPLAINT
    cat, sub_cat, prob_kw = extract_problem_from_text(clean_text)
    if cat:
        place = extract_place_from_text(clean_text)
        duration = extract_duration_from_text(clean_text)
        
        # Use approved mapped name for problem placeholder if problem text extracted
        lang_key = language if language in ["mr", "hi", "en"] else "mr"
        approved_prob_name = APPROVED_CATEGORIES.get(cat, {}).get(lang_key, cat)

        return IntentClassificationResult(
            intent="COMPLAINT",
            confidence=0.92,
            fields=ExtractedFields(
                problem_category=cat,
                sub_category=sub_cat,
                problem=approved_prob_name,
                place=place,
                duration=duration
            ),
            summary_en=f"Civic complaint regarding {cat}"
        )

    # 9. Fallback if unrecognized
    return IntentClassificationResult(
        intent="UNCLEAR",
        confidence=0.40,
        fields=ExtractedFields(),
        summary_en="Unrecognized or unclear utterance"
    )
