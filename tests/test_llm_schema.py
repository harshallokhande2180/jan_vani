"""
Test Suite: LLM Schema Validation & Intent Parsing (Section 5.3)
Evaluates 40 realistic sample sentences in Hindi and Marathi dialects.
Measures:
- Valid JSON schema rate (100% target via Pydantic enforcement)
- Category classification accuracy
"""

from intelligence.intent_extractor import parse_complaint
from intelligence.schema import GrievanceExtraction

TEST_SENTENCES = [
    # Water Supply (Marathi)
    {"text": "पिण्याच्या पाण्याची पाइपलाइन फुटली असून रस्ता पाण्याने भरला आहे.", "expected_cat": "Water Supply", "lang": "mr"},
    {"text": "आमच्या नळाला तीन दिवसांपासून पाणी येत नाही.", "expected_cat": "Water Supply", "lang": "mr"},
    {"text": "पाणी अत्यंत गढूळ आणि घाण वास येत आहे, पिण्यायोग्य नाही.", "expected_cat": "Water Supply", "lang": "mr"},
    {"text": "जलकल विभागाचा व्हॉल्व्ह खराब झाल्याने पाणी पुरवठा बंद आहे.", "expected_cat": "Water Supply", "lang": "mr"},

    # Water Supply (Hindi)
    {"text": "हमारे मोहल्ले में चार दिनों से पानी की सप्लाई पूरी तरह ठप है।", "expected_cat": "Water Supply", "lang": "hi"},
    {"text": "सरकारी नल की पाइप टूट गई है और पीने का पानी बह रहा है।", "expected_cat": "Water Supply", "lang": "hi"},
    {"text": "नल से बहुत गंदा और बदबूदार पानी आ रहा है।", "expected_cat": "Water Supply", "lang": "hi"},
    {"text": "पानी का टैंकर नहीं आया, लोग प्यासे हैं।", "expected_cat": "Water Supply", "lang": "hi"},

    # Roads (Marathi)
    {"text": "धरमपेठ मुख्य रस्त्यावर मोठा खड्डा पडला आहे, अपघात होत आहेत.", "expected_cat": "Roads", "lang": "mr"},
    {"text": "रस्ता खचला असून डांबरीकरण उखडून गेले आहे.", "expected_cat": "Roads", "lang": "mr"},
    {"text": "पादचारी फुटपाथ तुटलेला आहे, चालणे कठीण झाले आहे.", "expected_cat": "Roads", "lang": "mr"},
    {"text": "रस्त्यावरील कामामुळे मार्ग बंद झाला आहे आणि वाहतूक कोंडी आहे.", "expected_cat": "Roads", "lang": "mr"},

    # Roads (Hindi)
    {"text": "सड़क पर गहरा गड्ढा है, तुरंत मरम्मत की जरूरत है।", "expected_cat": "Roads", "lang": "hi"},
    {"text": "सड़क पूरी तरह टूट चुकी है, गाड़ियां दुर्घटनाग्रस्त हो रही हैं।", "expected_cat": "Roads", "lang": "hi"},
    {"text": "रोड पर डामर उखड़ गया है और बड़े पत्थर निकले हैं।", "expected_cat": "Roads", "lang": "hi"},
    {"text": "मुख्य मार्ग क्षतिग्रस्त है, आने-जाने का रास्ता नहीं बचा।", "expected_cat": "Roads", "lang": "hi"},

    # Drainage (Marathi)
    {"text": "गटार तुंबले असून घाण पाणी रस्त्यावर आणि घरात शिरत आहे.", "expected_cat": "Drainage", "lang": "mr"},
    {"text": "ड्रेनेज पाइपलाइन चोक झाली आहे, दुर्गंधी पसरली आहे.", "expected_cat": "Drainage", "lang": "mr"},
    {"text": "पावसामुळे नाला ओसंडून वाहत असून कचरा साचला आहे.", "expected_cat": "Drainage", "lang": "mr"},
    {"text": "गटाराचे झाकण तुटले आहे, लहान मुले पडण्याचा धोका आहे.", "expected_cat": "Drainage", "lang": "mr"},

    # Drainage (Hindi)
    {"text": "नाली पूरी तरह से जाम हो गई है, गंदा पानी बह रहा है।", "expected_cat": "Drainage", "lang": "hi"},
    {"text": "सीवर लाइन ब्लॉक है, बदबू के कारण लोग परेशान हैं।", "expected_cat": "Drainage", "lang": "hi"},
    {"text": "गंदे नाले की सफाई कई महीनों से नहीं हुई है।", "expected_cat": "Drainage", "lang": "hi"},
    {"text": "नाली का पानी सड़क पर भर गया है और मच्छर पनप रहे हैं।", "expected_cat": "Drainage", "lang": "hi"},

    # Power (Marathi)
    {"text": "विजेच्या खांबावर स्पार्क होत आहे, मोठा धोका आहे.", "expected_cat": "Power", "lang": "mr"},
    {"text": "रात्रीपासून संपूर्ण गल्लीतील वीज पुरवठा खंडित झाला आहे.", "expected_cat": "Power", "lang": "mr"},
    {"text": "विजेचा पोल रस्त्यावर झुकला आहे, वायर तुटू शकते.", "expected_cat": "Power", "lang": "mr"},
    {"text": "स्ट्रीट लाइट बंद असल्याने सर्वत्र अंधार पसरला आहे.", "expected_cat": "Power", "lang": "mr"},

    # Power (Hindi)
    {"text": "ट्रांसफार्मर जल गया है और पूरी कॉलोनी की बिजली गुल है।", "expected_cat": "Power", "lang": "hi"},
    {"text": "बिजली का तार टूटकर सड़क पर गिर गया है, करंट का डर है।", "expected_cat": "Power", "lang": "hi"},
    {"text": "बिजली का खंभा झुक गया है, कभी भी गिर सकता है।", "expected_cat": "Power", "lang": "hi"},
    {"text": "दिन-रात लाइट कट रही है, वोल्टेज बहुत कम है।", "expected_cat": "Power", "lang": "hi"},

    # Garbage (Marathi)
    {"text": "कचरापेटी भरून वाहत आहे, कोणीही कचरा गाडी पाठवली नाही.", "expected_cat": "Garbage", "lang": "mr"},
    {"text": "उकिरड्यावर कचरा साचला असून भटक्या कुत्र्यांचा त्रास वाढला आहे.", "expected_cat": "Garbage", "lang": "mr"},
    {"text": "सफाई कामगार अनेक दिवसांपासून आलेले नाहीत, घाण साचली आहे.", "expected_cat": "Garbage", "lang": "mr"},
    {"text": "डंपिंग ग्राउंडची दुर्गंधी वस्तीमध्ये येत आहे.", "expected_cat": "Garbage", "lang": "mr"},

    # Garbage (Hindi)
    {"text": "कूड़ेदान पूरा भरा हुआ है, सड़कों पर कचरा फैला है।", "expected_cat": "Garbage", "lang": "hi"},
    {"text": "कचरा उठाने वाली गाड़ी एक हफ्ते से नहीं आई है।", "expected_cat": "Garbage", "lang": "hi"},
    {"text": "गली के मोड़ पर भारी कूड़े का ढेर लगा है, बदबू आ रही है।", "expected_cat": "Garbage", "lang": "hi"},
    {"text": "सफाई कर्मचारी कचरा नहीं उठा रहे, बहुत गंदगी है।", "expected_cat": "Garbage", "lang": "hi"}
]

def run_llm_schema_tests():
    total = len(TEST_SENTENCES)
    valid_schema_count = 0
    correct_category_count = 0
    failures = []

    for item in TEST_SENTENCES:
        parsed = parse_complaint(item["text"], item["lang"])
        try:
            # Validate through Pydantic model
            validated = GrievanceExtraction(**parsed)
            valid_schema_count += 1

            if validated.category == item["expected_cat"]:
                correct_category_count += 1
            else:
                failures.append({
                    "text": item["text"],
                    "expected": item["expected_cat"],
                    "predicted": validated.category
                })
        except Exception as e:
            failures.append({
                "text": item["text"],
                "schema_error": str(e)
            })

    valid_rate = (valid_schema_count / total) * 100.0
    cat_accuracy = (correct_category_count / total) * 100.0

    return {
        "test_name": "LLM Schema & Intent Parser",
        "total_sentences": total,
        "valid_json_count": valid_schema_count,
        "valid_schema_rate_pct": round(valid_rate, 2),
        "correct_category_count": correct_category_count,
        "category_accuracy_pct": round(cat_accuracy, 2),
        "failures": failures,
        "passed": valid_rate == 100.0 and cat_accuracy >= 95.0
    }

if __name__ == "__main__":
    res = run_llm_schema_tests()
    print("LLM Schema Results:", res)
