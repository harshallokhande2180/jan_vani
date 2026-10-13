"""
TTS (Text to Speech) Perception module for Jan-Vani.
Generates spoken confirmations in Marathi, Hindi, and English so citizens
who cannot read can hear ticket confirmation and ward assignment clearly.
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
            voice_name = "marathi_female_clear"

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
            voice_name = "hindi_female_clear"

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
            voice_name = "english_female_clear"

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
