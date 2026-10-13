"""
TTS (Text to Speech) Perception module for Jan-Vani.
Generates spoken confirmations in Marathi, Hindi, English, Bengali, Gujarati,
Kannada, Malayalam, Punjabi, Tamil, and Telugu so citizens who cannot read
can hear ticket confirmation and ward assignment clearly.
"""

import os
from typing import Dict, Any

BHASHINI_TTS_KEY = os.getenv("BHASHINI_TTS_KEY", "")

class SpokenFeedbackEngine:
    def __init__(self, api_key: str = BHASHINI_TTS_KEY):
        self.api_key = api_key

    def generate_confirmation(
        self,
        ticket_id: str,
        ward_name: str,
        category: str,
        language: str = "mr",
        is_duplicate: bool = False,
        duplicate_count: int = 1
    ) -> Dict[str, Any]:
        """
        Creates spoken confirmation text and synthesis configuration.
        """
        if language == "mr":
            if is_duplicate:
                spoken_text = (
                    f"धन्यवाद! तुमच्या परिसरातील ही {category} ची समस्या आधीच नोंदवलेली आहे. "
                    f"आम्ही तुमची तक्रार तिकीट क्रमांक {ticket_id} मध्ये जोडली असून प्राधान्य वाढवले आहे. "
                    f"एकूण {duplicate_count} नागरिकांनी ही तक्रार केली आहे. {ward_name} प्रभाग अधिकारी तात्काळ कारवाई करत आहेत."
                )
            else:
                spoken_text = (
                    f"नमस्कार! तुमची {category} ची तक्रार नोंदवली गेली आहे. "
                    f"तुमचा तिकीट क्रमांक {ticket_id} आहे. "
                    f"तुमच्या {ward_name} प्रभाग अधिकाऱ्यांना तातडीने सूचना पाठवण्यात आली आहे."
                )
            lang_code = "mr-IN"
            voice_name = "mr_female_clear"

        elif language == "hi":
            if is_duplicate:
                spoken_text = (
                    f"धन्यवाद! आपके क्षेत्र में {category} की यह समस्या पहले से दर्ज है। "
                    f"आपकी शिकायत को टिकट संख्या {ticket_id} में जोड़कर प्राथमिकता बढ़ा दी गई है। "
                    f"अब तक {duplicate_count} नागरिकों ने इसकी सूचना दी है। {ward_name} वार्ड अधिकारी काम शुरू कर रहे हैं।"
                )
            else:
                spoken_text = (
                    f"नमस्ते! आपकी {category} की शिकायत सफलतापूर्वक दर्ज कर ली गई है। "
                    f"आपकी टिकट संख्या {ticket_id} है। "
                    f"{ward_name} वार्ड अधिकारी को कार्रवाई के लिए भेज दिया गया है।"
                )
            lang_code = "hi-IN"
            voice_name = "hi_female_clear"

        elif language == "bn":
            if is_duplicate:
                spoken_text = (
                    f"ধন্যবাদ! আপনার এলাকার {category} সমস্যাটি আগেই নথিভুক্ত ছিল। "
                    f"আমরা আপনার অভিযোগটি টিকিট নম্বর {ticket_id}-এ যুক্ত করেছি এবং অগ্রাধিকার বাড়িয়েছি। "
                    f"মোট {duplicate_count} জন নাগরিক এটি জানিয়েছেন। {ward_name} ওয়ার্ড অফিসার কাজ করছেন।"
                )
            else:
                spoken_text = (
                    f"নমস্কার! আপনার {category} সংক্রান্ত অভিযোগ নথিভুক্ত করা হয়েছে। "
                    f"আপনার টিকিট নম্বর {ticket_id}। "
                    f"{ward_name} ওয়ার্ডের আধিকারিককে ব্যবস্থা নেওয়ার নির্দেশ দেওয়া হয়েছে।"
                )
            lang_code = "bn-IN"
            voice_name = "bn_female_clear"

        elif language == "gu":
            if is_duplicate:
                spoken_text = (
                    f"આભાર! તમારા વિસ્તારની આ {category} સમસ્યા પહેલેથી જ નોંધાયેલી છે. "
                    f"અમે તમારી ફરિયાદ ટિકિટ નંબર {ticket_id} માં જોડી છે અને પ્રાથમિકતા વધારી છે. "
                    f"કુલ {duplicate_count} નાગરિકોએ આ ફરિયાદ કરી છે. {ward_name} વોર્ડ અધિકારી કાર્યવાહી કરી રહ્યા છે."
                )
            else:
                spoken_text = (
                    f"નમસ્તે! તમારી {category} અંગેની ફરિયાદ નોંધાઈ ગઈ છે. "
                    f"તમારો ટિકિટ નંબર {ticket_id} છે. "
                    f"{ward_name} વોર્ડ અધિકારીને ત્વરિત કાર્યવાહી માટે મોકલવામાં આવી છે."
                )
            lang_code = "gu-IN"
            voice_name = "gu_female_clear"

        elif language == "kn":
            if is_duplicate:
                spoken_text = (
                    f"ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಪ್ರದೇಶದ {category} ಸಮಸ್ಯೆಯನ್ನು ಈಗಾಗಲೇ ದಾಖಲಿಸಲಾಗಿದೆ. "
                    f"ನಿಮ್ಮ ದೂರನ್ನು ಟಿಕೆಟ್ ಸಂಖ್ಯೆ {ticket_id} ನಲ್ಲಿ ಸೇರಿಸಲಾಗಿದೆ ಮತ್ತು ಆದ್ಯತೆಯನ್ನು ಹೆಚ್ಚಿಸಲಾಗಿದೆ. "
                    f"ಒಟ್ಟು {duplicate_count} ನಾಗರಿಕರು ವರದಿ ಮಾಡಿದ್ದಾರೆ. {ward_name} ವಾರ್ಡ್ ಅಧಿಕಾರಿಗಳು ಕ್ರಮ ಕೈಗೊಳ್ಳುತ್ತಿದ್ದಾರೆ."
                )
            else:
                spoken_text = (
                    f"ನಮಸ್ಕಾರ! ನಿಮ್ಮ {category} ದೂರು ದಾಖಲಾಗಿದೆ. "
                    f"ನಿಮ್ಮ ಟಿಕೆಟ್ ಸಂಖ್ಯೆ {ticket_id}. "
                    f"{ward_name} ವಾರ್ಡ್ ಅಧಿಕಾರಿಗೆ ಸೂಕ್ತ ಕ್ರಮಕ್ಕಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ."
                )
            lang_code = "kn-IN"
            voice_name = "kn_female_clear"

        elif language == "ml":
            if is_duplicate:
                spoken_text = (
                    f"നന്ദി! നിങ്ങളുടെ പ്രദേശത്തെ ഈ {category} പരാതി നേരത്തെ തന്നെ രേഖപ്പെടുത്തിയിട്ടുണ്ട്. "
                    f"നിങ്ങളുടെ പരാതി ടിക്കറ്റ് നമ്പർ {ticket_id}-ലേക്ക് ചേർക്കുകയും മുൻഗണന ഉയർത്തുകയും ചെയ്തു. "
                    f"ആകെ {duplicate_count} പൗരന്മാർ റിപ്പോർട്ട് ചെയ്തിട്ടുണ്ട്. {ward_name} വാർഡ് ഓഫീസർ നടപടി സ്വീകരിക്കുന്നു."
                )
            else:
                spoken_text = (
                    f"നമസ്കാരം! നിങ്ങളുടെ {category} പരാതി വിജയകരമായി രജിസ്റ്റർ ചെയ്തു. "
                    f"നിങ്ങളുടെ ടിക്കറ്റ് നമ്പർ {ticket_id} ആണ്. "
                    f"{ward_name} വാർഡ് ഓഫീസർക്ക് തുടർനടപടികൾക്കായി കൈമാറി."
                )
            lang_code = "ml-IN"
            voice_name = "ml_female_clear"

        elif language == "pa":
            if is_duplicate:
                spoken_text = (
                    f"ਧੰਨਵਾਦ! ਤੁਹਾਡੇ ਇਲਾਕੇ ਦੀ {category} ਦੀ ਸਮੱਸਿਆ ਪਹਿਲਾਂ ਹੀ ਦਰਜ ਹੈ। "
                    f"ਅਸੀਂ ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਨੂੰ ਟਿਕਟ ਨੰਬਰ {ticket_id} ਵਿੱਚ ਜੋੜ ਕੇ ਤਰਜੀਹ ਵਧਾ ਦਿੱਤੀ ਹੈ। "
                    f"ਕੁੱਲ {duplicate_count} ਨਾਗਰਿਕਾਂ ਨੇ ਇਹ ਦੱਸਿਆ ਹੈ। {ward_name} ਵਾਰਡ ਅਫ਼ਸਰ ਕਾਰਵਾਈ ਕਰ ਰਹੇ ਹਨ।"
                )
            else:
                spoken_text = (
                    f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਹਾਡੀ {category} ਦੀ ਸ਼ਿਕਾਇਤ ਦਰਜ ਕਰ ਲਈ ਗਈ ਹੈ। "
                    f"ਤੁਹਾਡਾ ਟਿਕਟ ਨੰਬਰ {ticket_id} ਹੈ। "
                    f"{ward_name} ਵਾਰਡ ਅਫ਼ਸਰ ਨੂੰ ਕਾਰਵਾਈ ਲਈ ਭੇਜ ਦਿੱਤਾ ਗਿਆ ਹੈ।"
                )
            lang_code = "pa-IN"
            voice_name = "pa_female_clear"

        elif language == "ta":
            if is_duplicate:
                spoken_text = (
                    f"நன்றி! உங்கள் பகுதியில் இந்த {category} பிரச்சனை ஏற்கனவே பதிவு செய்யப்பட்டுள்ளது. "
                    f"உங்கள் புகாரை டிக்கெட் எண் {ticket_id}-ல் இணைத்து முன்னுரிமையை உயர்த்தியுள்ளோம். "
                    f"மொத்தம் {duplicate_count} குடிமக்கள் தெரிவித்துள்ளனர். {ward_name} வார்டு அதிகாரி நடவடிக்கை எடுக்கிறார்."
                )
            else:
                spoken_text = (
                    f"வணக்கம்! உங்கள் {category} புகார் வெற்றிகரமாகப் பதிவு செய்யப்பட்டது. "
                    f"உங்கள் டிக்கெட் எண் {ticket_id}. "
                    f"{ward_name} வார்டு அதிகாரிக்கு உடனடி நடவடிக்கைக்காக அனுப்பப்பட்டுள்ளது."
                )
            lang_code = "ta-IN"
            voice_name = "ta_female_clear"

        elif language == "te":
            if is_duplicate:
                spoken_text = (
                    f"ధన్యవాదాలు! మీ ప్రాంతంలో ఈ {category} సమస్య ఇప్పటికే నమోదు చేయబడింది. "
                    f"మేము మీ ఫిర్యాదును టికెట్ సంఖ్య {ticket_id} కు జతచేసి ప్రాధాన్యతను పెంచాము. "
                    f"మొత్తం {duplicate_count} మంది పౌరులు నివేదించారు. {ward_name} వార్డు అధికారి చర్యలు తీసుకుంటున్నారు."
                )
            else:
                spoken_text = (
                    f"నమస్కారం! మీ {category} ఫిర్యాదు నమోదు చేయబడింది. "
                    f"మీ టికెట్ సంఖ్య {ticket_id}. "
                    f"{ward_name} వార్డు అధికారికి చర్యల కోసం పంపబడింది."
                )
            lang_code = "te-IN"
            voice_name = "te_female_clear"

        else:  # English
            if is_duplicate:
                spoken_text = (
                    f"Thank you. This {category} grievance was already registered. "
                    f"We have merged your report into ticket {ticket_id} and escalated its priority. "
                    f"A total of {duplicate_count} citizens have reported this. Ward officer for {ward_name} is on it."
                )
            else:
                spoken_text = (
                    f"Greetings. Your {category} complaint has been registered. "
                    f"Ticket number is {ticket_id}. "
                    f"Assigned to {ward_name} ward officer for prompt action."
                )
            lang_code = "en-IN"
            voice_name = "en_female_clear"

        return {
            "ticket_id": ticket_id,
            "language": language,
            "lang_code": lang_code,
            "voice_name": voice_name,
            "spoken_text": spoken_text,
            "speech_rate": 0.95,
            "provider": "bhashini_tts_ready"
        }

tts_engine = SpokenFeedbackEngine()
