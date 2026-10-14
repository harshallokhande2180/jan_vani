"""
Test Suite: Intent Classification & Dialogue Rules.
Covers:
- At least 10 examples per intent in Marathi and Hindi (9 intents x 10+ = 90+ tests).
- Explicit cases:
  1. "हॅलो" (must not create a ticket)
  2. "आज पाऊस पडेल का?" (must be OFF_TOPIC)
  3. Correction example (CORRECTION updates the named field and confirms again)
- Verifies Pydantic schema validation.
- Verifies that GREETING, THANKS, HELP, UNCLEAR, OFF_TOPIC never create tickets.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from intelligence.intent import classify_intent
from intelligence.dialogue import GuidedDialogueSession, DialogueState
from intelligence.intent_schema import IntentClassificationResult

# 10+ examples per intent (Marathi & Hindi)
INTENT_EXAMPLES = {
    "GREETING": [
        ("हॅलो", "mr"),
        ("नमस्कार", "mr"),
        ("शुभ सकाळ", "mr"),
        ("हॅलो जी", "mr"),
        ("राम राम", "mr"),
        ("नमस्ते", "hi"),
        ("प्रणाम", "hi"),
        ("शुभ प्रभात", "hi"),
        ("नमस्ते जी", "hi"),
        ("हेलो", "hi"),
        ("hello", "en")
    ],
    "THANKS": [
        ("धन्यवाद", "mr"),
        ("खूप खूप धन्यवाद", "mr"),
        ("आपले मनापासून आभार", "mr"),
        ("आभार", "mr"),
        ("धन्यवाद साहेब", "mr"),
        ("शुक्रिया", "hi"),
        ("बहुत बहुत धन्यवाद", "hi"),
        ("धन्यवाद जी", "hi"),
        ("आपकी बड़ी मेहरबानी", "hi"),
        ("शुक्रिया बहुत बहुत", "hi"),
        ("thank you very much", "en")
    ],
    "HELP": [
        ("मदत करा", "mr"),
        ("हे कसे वापरावे", "mr"),
        ("मला मदत हवी आहे", "mr"),
        ("मी काय करू", "mr"),
        ("तक्रार कशी करायची", "mr"),
        ("सहायता चाहिए", "hi"),
        ("मदद कीजिए", "hi"),
        ("यह कैसे काम करता है", "hi"),
        ("मुझे क्या करना होगा", "hi"),
        ("शिकायत कैसे दर्ज करें", "hi"),
        ("help me please", "en")
    ],
    "OFF_TOPIC": [
        ("आज पाऊस पडेल का?", "mr"),
        ("उद्या पाऊस येणार आहे का", "mr"),
        ("क्रिकेट सामना कोणी जिंकला", "mr"),
        ("आजचे हवामान कसे आहे", "mr"),
        ("सोन्याचा भाव काय आहे", "mr"),
        ("आज बारिश होगी क्या?", "hi"),
        ("कल का मौसम कैसा रहेगा", "hi"),
        ("क्रिकेट मैच का स्कोर क्या है", "hi"),
        ("सोने का भाव क्या चल रहा है", "hi"),
        ("आज चुनाव कौन जीतेगा", "hi"),
        ("who will win the match today", "en")
    ],
    "YES": [
        ("हो", "mr"),
        ("होय", "mr"),
        ("हो बरोबर", "mr"),
        ("हो बरोबर आहे", "mr"),
        ("हो करा नोंद", "mr"),
        ("हाँ", "hi"),
        ("हाँ बिल्कुल", "hi"),
        ("हाँ सही है", "hi"),
        ("हाँ दर्ज कीजिए", "hi"),
        ("सही है", "hi"),
        ("yes", "en")
    ],
    "NO": [
        ("नाही", "mr"),
        ("नाही नको", "mr"),
        ("नाही थांबवा", "mr"),
        ("चूक आहे", "mr"),
        ("नाही नोंदवू नका", "mr"),
        ("नहीं", "hi"),
        ("नहीं गलत है", "hi"),
        ("नहीं मत करो", "hi"),
        ("नाही ऐसा नहीं है", "hi"),
        ("गलत है", "hi"),
        ("no cancel", "en")
    ],
    "CORRECTION": [
        ("नाही, हे धरमपेठ मध्ये आहे", "mr"),
        ("नाही ठिकाण बदला, सीताबर्डी आहे", "mr"),
        ("नाही हे चार दिवसांपासून आहे", "mr"),
        ("नाही तीन दिवस झाले", "mr"),
        ("नाही, धंतोली येथे रस्ता खराब आहे", "mr"),
        ("नहीं, यह धरमपेठ में है", "hi"),
        ("नहीं स्थान बदलो, सीताबर्डी है", "hi"),
        ("नहीं यह चार दिनों से है", "hi"),
        ("नहीं तीन दिन हो गए", "hi"),
        ("नहीं, धंतोली में सड़क टूटी है", "hi"),
        ("no, correct it to Dharampeth", "en")
    ],
    "UNCLEAR": [
        ("...", "mr"),
        ("अं... उं...", "mr"),
        ("अरे", "mr"),
        ("काहीतरी", "mr"),
        ("काय सांगू", "mr"),
        ("बस ऐसे ही", "hi"),
        ("हम्म", "hi"),
        ("कुछ भी नहीं", "hi"),
        ("पता नहीं", "hi"),
        ("अजीब बात है", "hi"),
        ("xyz abc", "en")
    ],
    "COMPLAINT": [
        ("धरमपेठ मुख्य रस्त्यावर मोठा खड्डा पडला आहे तीन दिवसांपासून.", "mr"),
        ("पिण्याच्या पाण्याची पाइपलाइन फुटली असून पाणी गळत आहे.", "mr"),
        ("गटार तुंबले असून घाण पाणी रस्त्यावर येत आहे.", "mr"),
        ("रात्रीपासून संपूर्ण गल्लीतील वीज पुरवठा खंडित झाला आहे.", "mr"),
        ("कचरा साचला असून दुर्गंधी पसरली आहे.", "mr"),
        ("धरमपेठ में सड़क पर गहरा गड्ढा है तीन दिनों से।", "hi"),
        ("पीने के पानी का पाइप टूट गया है और पानी बह रहा है।", "hi"),
        ("सीवर लाइन जाम है और गंदा पानी फैल रहा है।", "hi"),
        ("कल से बिजली गुल है, अंधेरा छाया हुआ है।", "hi"),
        ("सड़क पर भारी कचरा फैला हुआ है और बदबू आ रही है।", "hi"),
        ("pothole on Dharampeth road for 3 days", "en")
    ]
}

def test_intent_classification_schema_validity():
    """Validates that all classified outputs conform to strict Pydantic model."""
    for intent, examples in INTENT_EXAMPLES.items():
        for text, lang in examples:
            result = classify_intent(text, lang)
            assert isinstance(result, IntentClassificationResult)
            assert result.intent in [
                "COMPLAINT", "GREETING", "YES", "NO", "CORRECTION", "THANKS", "HELP", "OFF_TOPIC", "UNCLEAR"
            ]

def test_required_case_hello():
    """Case: 'हॅलो' must be GREETING and MUST NOT create a ticket."""
    result = classify_intent("हॅलो", "mr")
    assert result.intent == "GREETING"

    session = GuidedDialogueSession(language="mr")
    turn = session.process_turn("हॅलो")
    assert turn["intent"] == "GREETING"
    assert turn["ticket_created"] is False
    assert turn["ticket_id"] is None

def test_required_case_off_topic_rain():
    """Case: 'आज पाऊस पडेल का?' must be classified strictly as OFF_TOPIC."""
    result = classify_intent("आज पाऊस पडेल का?", "mr")
    assert result.intent == "OFF_TOPIC"

    session = GuidedDialogueSession(language="mr")
    turn = session.process_turn("आज पाऊस पडेल का?")
    assert turn["intent"] == "OFF_TOPIC"
    assert turn["ticket_created"] is False
    assert turn["ticket_id"] is None

def test_required_case_correction():
    """
    Case: Correction example where citizen corrects a named field,
    and dialogue updates the field then confirms again.
    """
    session = GuidedDialogueSession(language="mr")

    # Turn 1: Complaint with problem only
    t1 = session.process_turn("रस्त्यावर मोठा खड्डा पडला आहे")
    assert t1["intent"] == "COMPLAINT"
    assert t1["ticket_created"] is False
    # Asks for place
    assert session.state == DialogueState.GATHERING

    # Turn 2: Citizen gives wrong place
    t2 = session.process_turn("धरमपेठ")
    assert session.fields["place"] == "धरमपेठ"

    # Turn 3: Correction
    t3 = session.process_turn("नाही ठिकाण बदला, सीताबर्डी आहे")
    assert t3["intent"] == "CORRECTION"
    assert session.fields["place"] == "सीताबर्डी"
    assert session.state == DialogueState.CONFIRM
    assert "सीताबर्डी" in t3["spoken_reply"]

    # Turn 4: Confirmation with YES
    t4 = session.process_turn("हो बरोबर")
    assert t4["intent"] == "YES"
    assert t4["ticket_created"] is True
    assert t4["ticket_id"] is not None

def test_non_complaints_never_create_tickets():
    """Ensures GREETING, THANKS, HELP, UNCLEAR, OFF_TOPIC never create a ticket."""
    non_complaint_intents = ["GREETING", "THANKS", "HELP", "UNCLEAR", "OFF_TOPIC"]
    for intent_name in non_complaint_intents:
        for text, lang in INTENT_EXAMPLES[intent_name]:
            session = GuidedDialogueSession(language=lang)
            turn = session.process_turn(text)
            assert turn["ticket_created"] is False, f"Ticket wrongly created for {intent_name}: '{text}'"

def test_minimum_10_examples_per_intent():
    """Asserts each intent has at least 10 examples in test definition."""
    for intent, examples in INTENT_EXAMPLES.items():
        assert len(examples) >= 10, f"Intent {intent} has only {len(examples)} examples, minimum 10 required."

def run_all_intent_tests():
    print("Running Intent Classification & Dialogue Test Suite...")
    test_minimum_10_examples_per_intent()
    print("  [PASS] At least 10 examples per intent defined")
    test_intent_classification_schema_validity()
    print("  [PASS] Schema validation and allowed intent enums")
    test_required_case_hello()
    print("  [PASS] 'हॅलो' GREETING case (no ticket created)")
    test_required_case_off_topic_rain()
    print("  [PASS] 'आज पाऊस पडेल का?' OFF_TOPIC case")
    test_required_case_correction()
    print("  [PASS] Field correction & re-confirmation workflow")
    test_non_complaints_never_create_tickets()
    print("  [PASS] Non-complaint intents strictly create zero tickets")
    print("All Intent & Dialogue tests passed successfully!")

if __name__ == "__main__":
    run_all_intent_tests()
