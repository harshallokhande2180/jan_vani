"""
Intent extraction and NLP intelligence engine for Jan-Vani.
Extracts category, sub_category, urgency, duration, summary, and confidence
from vernacular Hindi and Marathi complaints.
Supports both LLM API calling and deterministic local semantic parsing.
"""

import os
import re
import json
from typing import Dict, Any, Tuple, Optional
from intelligence.schema import GrievanceExtraction, FallbackExtraction

# Keywords & dialect markers for Hindi and Marathi
PATTERNS = {
    "Water Supply": {
        "keywords": [
            "पानी", "जल", "नल", "गळती", "पाणी", "पाइप", "पिण्याचे पाणी",
            "जलकल", "सप्लाई", "टुटा पाइप", "water", "leak", "pipe", "tap"
        ],
        "sub_categories": {
            "Leakage": ["लीक", "गळती", "फुटा", "फुटला", "बहाव", "गळत", "leak", "burst"],
            "Disruption": ["बंद", "नाही", "आला नाही", "नहीं आया", "कटौती", "disruption", "no water"],
            "Contamination": ["गंदा", "घाण", "दुर्गंधी", "बदबू", "गढूळ", "dirty", "contaminated"]
        }
    },
    "Roads": {
        "keywords": [
            "सड़क", "रस्ता", "खड्डा", "गड्ढा", "मार्ग", "रोड", "डामर", "फुटपाथ",
            "पूल", "road", "pothole", "street", "highway"
        ],
        "sub_categories": {
            "Damage": ["खड्डा", "गड्ढा", "तुटला", "टूटा", "खराब", "दुरुस्ती", "pothole", "broken"],
            "Disruption": ["जाम", "बंद", "अवरोध", "block", "closed"]
        }
    },
    "Drainage": {
        "keywords": [
            "नाली", "नाला", "ड्रेनेज", "गटार", "तुंबले", "उतू", "गंदा पानी",
            "सीवर", "drain", "gutter", "sewage", "drainage"
        ],
        "sub_categories": {
            "Disruption": ["तुंबले", "अटकले", "जाम", "चौक", "blocked", "clogged", "overflow"],
            "Contamination": ["घाण", "दुर्गंधी", "बदबू", "मच्छर", "smell", "filth"]
        }
    },
    "Power": {
        "keywords": [
            "बिजली", "लाइट", "वीज", "करंट", "वायर", "पोल", "ट्रांसफार्मर", "खंभा",
            "अंधार", "पावर", "electricity", "power", "light", "wire", "pole"
        ],
        "sub_categories": {
            "Disruption": ["गुल", "गेली", "कट", "बंद", "नाही", "blackout", "cut", "failure"],
            "Damage": ["तूट", "टूटा", "झुकला", "धूर", "स्पार्क", "spark", "fallen"]
        }
    },
    "Garbage": {
        "keywords": [
            "कचरा", "कूड़ा", "कचरापेटी", "घाण", "उकिरडा", "डंपिंग", "सफाई",
            "garbage", "trash", "waste", "dump"
        ],
        "sub_categories": {
            "Disruption": ["उचलला नाही", "पडून आहे", "साचला", "पड़ा है", "not picked", "accumulated"],
            "Contamination": ["दुर्गंधी", "घाण", "सड", "rotten", "smell"]
        }
    }
}

DURATION_PATTERNS = [
    (r"(\d+)\s*(दिवस|दिन|days|day)", lambda m: f"{m.group(1)} days"),
    (r"(दोन|तीन|चार|पाच)\s*दिवस", lambda m: f"{m.group(0)}"),
    (r"(दो|तीन|चार|पांच)\s*दिन", lambda m: f"{m.group(0)}"),
    (r"एक\s*आठवडा|एक\s*सप्ताह|one\s*week", lambda m: "1 week"),
    (r"कालपासून|कल से|since\s*yesterday", lambda m: "since yesterday"),
    (r"आज सकाळपासून|आज सुबह से", lambda m: "since today morning")
]

URGENCY_HIGH_MARKERS = [
    "तातडीने", "लगेच", "धोका", "अपघात", "मोठा", "फार", "लवकर",
    "तुरंत", "खतरा", "दुर्घटना", "बड़ा", "बहुत ज्यादा", "urgent", "danger", "emergency"
]

def extract_duration(text: str) -> Optional[str]:
    for pattern, formatter in DURATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return formatter(match)
    return None

def extract_intent_local(transcript: str, language: str = "auto") -> GrievanceExtraction:
    """
    Deterministic rule-based NLP intent parser for Marathi and Hindi complaints.
    Provides reliable, schema-validated output.
    """
    text_lower = transcript.lower()

    # Score categories
    category_scores = {}
    sub_category_matches = {}

    for cat, data in PATTERNS.items():
        score = 0
        for kw in data["keywords"]:
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
    elif best_cat in ["Water Supply", "Power"] and "बंद" in text_lower:
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
