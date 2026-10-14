"""
Jan-Vani Intent Benchmark Suite.
Runs a labelled test set of at least 100 utterances in Marathi and Hindi across all 9 intents:
COMPLAINT, GREETING, YES, NO, CORRECTION, THANKS, HELP, OFF_TOPIC, UNCLEAR.

Reports:
1. Per-intent precision, recall, and F1-score.
2. The rate of tickets created from non-complaint intents (MUST be zero).
3. Overall classification accuracy.

Do not invent results. All metrics are computed dynamically at runtime.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from intelligence.intent import classify_intent
from intelligence.dialogue import GuidedDialogueSession
from intelligence.intent_schema import IntentType

# Labelled test set: exactly 108 authentic utterances (12 per intent across Marathi, Hindi, English)
LABELLED_DATASET = [
    # 1. GREETING (12)
    {"text": "हॅलो", "expected": "GREETING", "lang": "mr"},
    {"text": "नमस्कार", "expected": "GREETING", "lang": "mr"},
    {"text": "शुभ सकाळ", "expected": "GREETING", "lang": "mr"},
    {"text": "हॅलो जी", "expected": "GREETING", "lang": "mr"},
    {"text": "राम राम", "expected": "GREETING", "lang": "mr"},
    {"text": "जय हरी", "expected": "GREETING", "lang": "mr"},
    {"text": "नमस्ते", "expected": "GREETING", "lang": "hi"},
    {"text": "प्रणाम", "expected": "GREETING", "lang": "hi"},
    {"text": "शुभ प्रभात", "expected": "GREETING", "lang": "hi"},
    {"text": "नमस्ते जी", "expected": "GREETING", "lang": "hi"},
    {"text": "हेलो भाई", "expected": "GREETING", "lang": "hi"},
    {"text": "hello", "expected": "GREETING", "lang": "en"},

    # 2. THANKS (12)
    {"text": "धन्यवाद", "expected": "THANKS", "lang": "mr"},
    {"text": "खूप खूप धन्यवाद", "expected": "THANKS", "lang": "mr"},
    {"text": "आपले आभार", "expected": "THANKS", "lang": "mr"},
    {"text": "मनःपूर्वक आभार", "expected": "THANKS", "lang": "mr"},
    {"text": "धन्यवाद साहेब", "expected": "THANKS", "lang": "mr"},
    {"text": "आभार साहेब", "expected": "THANKS", "lang": "mr"},
    {"text": "शुक्रिया", "expected": "THANKS", "lang": "hi"},
    {"text": "बहुत बहुत धन्यवाद", "expected": "THANKS", "lang": "hi"},
    {"text": "धन्यवाद जी", "expected": "THANKS", "lang": "hi"},
    {"text": "आपकी बड़ी मेहरबानी", "expected": "THANKS", "lang": "hi"},
    {"text": "शुक्रिया धन्यवाद", "expected": "THANKS", "lang": "hi"},
    {"text": "thank you so much", "expected": "THANKS", "lang": "en"},

    # 3. HELP (12)
    {"text": "मदत करा", "expected": "HELP", "lang": "mr"},
    {"text": "मला मदत हवी आहे", "expected": "HELP", "lang": "mr"},
    {"text": "हे कसे वापरावे", "expected": "HELP", "lang": "mr"},
    {"text": "मी काय करू", "expected": "HELP", "lang": "mr"},
    {"text": "तक्रार कशी करायची सांगा", "expected": "HELP", "lang": "mr"},
    {"text": "मदत पाहिजे", "expected": "HELP", "lang": "mr"},
    {"text": "सहायता चाहिए", "expected": "HELP", "lang": "hi"},
    {"text": "मदद कीजिए", "expected": "HELP", "lang": "hi"},
    {"text": "यह कैसे काम करता है", "expected": "HELP", "lang": "hi"},
    {"text": "मुझे क्या करना होगा", "expected": "HELP", "lang": "hi"},
    {"text": "शिकायत कैसे दर्ज करें", "expected": "HELP", "lang": "hi"},
    {"text": "help me with this", "expected": "HELP", "lang": "en"},

    # 4. OFF_TOPIC (12)
    {"text": "आज पाऊस पडेल का?", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "उद्या पाऊस पडणार आहे का", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "आजचे हवामान कसे आहे", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "क्रिकेट सामना कोणी जिंकला", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "सोन्याचा आजचा भाव काय आहे", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "भाजीपाल्याचे भाव सांगा", "expected": "OFF_TOPIC", "lang": "mr"},
    {"text": "आज बारिश होगी क्या?", "expected": "OFF_TOPIC", "lang": "hi"},
    {"text": "कल का मौसम कैसा रहेगा", "expected": "OFF_TOPIC", "lang": "hi"},
    {"text": "क्रिकेट मैच का क्या स्कोर है", "expected": "OFF_TOPIC", "lang": "hi"},
    {"text": "सोने का भाव क्या चल रहा है", "expected": "OFF_TOPIC", "lang": "hi"},
    {"text": "आज चुनाव कौन जीतेगा", "expected": "OFF_TOPIC", "lang": "hi"},
    {"text": "who won the cricket match yesterday", "expected": "OFF_TOPIC", "lang": "en"},

    # 5. YES (12)
    {"text": "हो", "expected": "YES", "lang": "mr"},
    {"text": "होय", "expected": "YES", "lang": "mr"},
    {"text": "हो बरोबर", "expected": "YES", "lang": "mr"},
    {"text": "हो बरोबर आहे", "expected": "YES", "lang": "mr"},
    {"text": "हो करा नोंद", "expected": "YES", "lang": "mr"},
    {"text": "नक्कीच", "expected": "YES", "lang": "mr"},
    {"text": "हाँ", "expected": "YES", "lang": "hi"},
    {"text": "हाँ बिल्कुल", "expected": "YES", "lang": "hi"},
    {"text": "हाँ सही है", "expected": "YES", "lang": "hi"},
    {"text": "हाँ दर्ज कीजिए", "expected": "YES", "lang": "hi"},
    {"text": "सही है", "expected": "YES", "lang": "hi"},
    {"text": "yes confirm", "expected": "YES", "lang": "en"},

    # 6. NO (12)
    {"text": "नाही", "expected": "NO", "lang": "mr"},
    {"text": "नाही नको", "expected": "NO", "lang": "mr"},
    {"text": "नाही चूक आहे", "expected": "NO", "lang": "mr"},
    {"text": "नाही थांबवा", "expected": "NO", "lang": "mr"},
    {"text": "नाही नोंदवू नका", "expected": "NO", "lang": "mr"},
    {"text": "चूक", "expected": "NO", "lang": "mr"},
    {"text": "नहीं", "expected": "NO", "lang": "hi"},
    {"text": "नहीं गलत है", "expected": "NO", "lang": "hi"},
    {"text": "नहीं मत करो", "expected": "NO", "lang": "hi"},
    {"text": "रद्द करो", "expected": "NO", "lang": "hi"},
    {"text": "गलत है", "expected": "NO", "lang": "hi"},
    {"text": "no cancel it", "expected": "NO", "lang": "en"},

    # 7. CORRECTION (12)
    {"text": "नाही, हे धरमपेठ मध्ये आहे", "expected": "CORRECTION", "lang": "mr"},
    {"text": "नाही ठिकाण बदला, सीताबर्डी आहे", "expected": "CORRECTION", "lang": "mr"},
    {"text": "नाही हे चार दिवसांपासून आहे", "expected": "CORRECTION", "lang": "mr"},
    {"text": "नाही तीन दिवस झाले आहेत", "expected": "CORRECTION", "lang": "mr"},
    {"text": "नाही, धंतोली येथे रस्ता तुटला आहे", "expected": "CORRECTION", "lang": "mr"},
    {"text": "दुरुस्ती करा, पाणीपुरवठा समस्या आहे", "expected": "CORRECTION", "lang": "mr"},
    {"text": "नहीं, यह धरमपेठ में है", "expected": "CORRECTION", "lang": "hi"},
    {"text": "नहीं स्थान बदलो, सीताबर्डी है", "expected": "CORRECTION", "lang": "hi"},
    {"text": "नहीं यह चार दिनों से है", "expected": "CORRECTION", "lang": "hi"},
    {"text": "नहीं तीन दिन हो गए", "expected": "CORRECTION", "lang": "hi"},
    {"text": "नहीं, धंतोली में सड़क टूटी है", "expected": "CORRECTION", "lang": "hi"},
    {"text": "no, correct it to Dharampeth", "expected": "CORRECTION", "lang": "en"},

    # 8. UNCLEAR (12)
    {"text": "...", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "अं... उं...", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "अरे", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "काहीतरी", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "काय सांगू आता", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "कदाचित", "expected": "UNCLEAR", "lang": "mr"},
    {"text": "बस ऐसे ही", "expected": "UNCLEAR", "lang": "hi"},
    {"text": "हम्म", "expected": "UNCLEAR", "lang": "hi"},
    {"text": "कुछ भी नहीं", "expected": "UNCLEAR", "lang": "hi"},
    {"text": "पता नहीं क्या हुआ", "expected": "UNCLEAR", "lang": "hi"},
    {"text": "अजीब बात है", "expected": "UNCLEAR", "lang": "hi"},
    {"text": "xyz abc blabla", "expected": "UNCLEAR", "lang": "en"},

    # 9. COMPLAINT (12)
    {"text": "धरमपेठ मुख्य रस्त्यावर मोठा खड्डा पडला आहे तीन दिवसांपासून.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "पिण्याच्या पाण्याची पाइपलाइन फुटली असून पाणी गळत आहे.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "गटार तुंबले असून घाण पाणी रस्त्यावर येत आहे.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "रात्रीपासून संपूर्ण गल्लीतील वीज पुरवठा खंडित झाला आहे.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "कचरा साचला असून भटक्या कुत्र्यांचा त्रास वाढला आहे.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "धंतोली मध्ये ड्रेनेज चोक झाली आहे.", "expected": "COMPLAINT", "lang": "mr"},
    {"text": "धरमपेठ में सड़क पर गहरा गड्ढा है तीन दिनों से।", "expected": "COMPLAINT", "lang": "hi"},
    {"text": "पीने के पानी का पाइप टूट गया है और गंदा पानी आ रहा है।", "expected": "COMPLAINT", "lang": "hi"},
    {"text": "सीवर लाइन ब्लॉक है और बदबू आ रही है।", "expected": "COMPLAINT", "lang": "hi"},
    {"text": "कल से बिजली का पोल झुका हुआ है, करंट आ सकता है।", "expected": "COMPLAINT", "lang": "hi"},
    {"text": "कचरा उठाने वाली गाड़ी एक हफ्ते से नहीं आई है।", "expected": "COMPLAINT", "lang": "hi"},
    {"text": "water supply disrupted in Dharampeth for two days", "expected": "COMPLAINT", "lang": "en"}
]

def run_intent_benchmark() -> dict:
    """
    Evaluates labelled dataset, computing precision, recall, F1 per intent,
    and auditing ticket creation rate from non-complaint intents.
    """
    intents = [
        "COMPLAINT", "GREETING", "YES", "NO", "CORRECTION", "THANKS", "HELP", "OFF_TOPIC", "UNCLEAR"
    ]

    total_samples = len(LABELLED_DATASET)
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    support = defaultdict(int)

    correct_predictions = 0
    non_complaint_tickets_created = 0
    non_complaint_count = 0

    results_details = []

    for item in LABELLED_DATASET:
        text = item["text"]
        expected = item["expected"]
        lang = item["lang"]
        support[expected] += 1

        # 1. Intent Classification
        res = classify_intent(text, lang)
        predicted = res.intent

        if predicted == expected:
            correct_predictions += 1
            tp[expected] += 1
        else:
            fp[predicted] += 1
            fn[expected] += 1

        # 2. Check dialogue ticket creation for non-complaints
        if expected != "COMPLAINT":
            non_complaint_count += 1
            session = GuidedDialogueSession(language=lang)
            turn = session.process_turn(text)
            if turn["ticket_created"]:
                non_complaint_tickets_created += 1

        results_details.append({
            "text": text,
            "language": lang,
            "expected_intent": expected,
            "predicted_intent": predicted,
            "confidence": res.confidence,
            "is_correct": predicted == expected
        })

    # Compute metrics per intent
    per_intent_metrics = {}
    for intent in intents:
        t = tp[intent]
        f_p = fp[intent]
        f_n = fn[intent]
        sup = support[intent]

        precision = round((t / (t + f_p)) * 100, 2) if (t + f_p) > 0 else 0.0
        recall = round((t / (t + f_n)) * 100, 2) if (t + f_n) > 0 else 0.0
        f1 = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 0.0

        per_intent_metrics[intent] = {
            "support": sup,
            "true_positives": t,
            "false_positives": f_p,
            "false_negatives": f_n,
            "precision_pct": precision,
            "recall_pct": recall,
            "f1_score": f1
        }

    overall_accuracy = round((correct_predictions / total_samples) * 100, 2)
    ticket_creation_rate_non_complaints = round((non_complaint_tickets_created / non_complaint_count) * 100, 4) if non_complaint_count > 0 else 0.0

    report = {
        "dataset_name": "Jan-Vani Labelled Multilingual Intent Test Set",
        "total_samples": total_samples,
        "overall_accuracy_pct": overall_accuracy,
        "non_complaint_utterances_tested": non_complaint_count,
        "tickets_created_from_non_complaints": non_complaint_tickets_created,
        "ticket_creation_rate_non_complaint_pct": ticket_creation_rate_non_complaints,
        "per_intent_metrics": per_intent_metrics,
        "sample_evaluations": results_details
    }

    # Save to tests/results/intent_benchmark_report.json
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "intent_benchmark_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def main():
    print("=" * 72)
    print("   JAN-VANI INTENT CLASSIFICATION & DIALOGUE BENCHMARK SUITE")
    print("=" * 72)

    report = run_intent_benchmark()

    print(f"\nTotal Labelled Utterances Tested: {report['total_samples']}")
    print(f"Overall Classification Accuracy: {report['overall_accuracy_pct']}%\n")

    print(f"{'INTENT':<14} | {'SUPPORT':<8} | {'PRECISION':<10} | {'RECALL':<8} | {'F1-SCORE':<8}")
    print("-" * 58)
    for intent, m in report["per_intent_metrics"].items():
        print(f"{intent:<14} | {m['support']:<8} | {m['precision_pct']:>8.2f}% | {m['recall_pct']:>6.2f}% | {m['f1_score']:>7.2f}")
    print("-" * 58)

    print(f"\n[CRITICAL SAFETY CHECK] Rate of tickets created from non-complaint intents:")
    print(f"  -> Measured: {report['ticket_creation_rate_non_complaint_pct']}% ({report['tickets_created_from_non_complaints']}/{report['non_complaint_utterances_tested']} tickets created)")
    if report["ticket_creation_rate_non_complaint_pct"] == 0.0:
        print("  -> Status: [PASS] Zero tickets created from non-complaint intents.")
    else:
        print("  -> Status: [FAIL] Tickets were incorrectly created from non-complaint intents!")

    print(f"\nBenchmark report saved to: tests/results/intent_benchmark_report.json")

if __name__ == "__main__":
    main()
