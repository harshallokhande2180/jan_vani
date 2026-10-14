"""
Pydantic schemas and strict types for Jan-Vani Intent Classification and Dialogue.
Strictly conforms to allowed intent types and extracted fields.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

# Allowed intents - strictly enforced list:
# COMPLAINT, GREETING, YES, NO, CORRECTION, THANKS, HELP, OFF_TOPIC, UNCLEAR
IntentType = Literal[
    "COMPLAINT",
    "GREETING",
    "YES",
    "NO",
    "CORRECTION",
    "THANKS",
    "HELP",
    "OFF_TOPIC",
    "UNCLEAR"
]

CategoryType = Literal[
    "Water Supply",
    "Roads",
    "Drainage",
    "Power",
    "Garbage",
    "Other"
]

SubCategoryType = Literal[
    "Disruption",
    "Leakage",
    "Contamination",
    "Damage",
    "Other"
]

UrgencyType = Literal[
    "Low",
    "Medium",
    "High"
]

# Approved canonical category mapping for placeholder filling
APPROVED_CATEGORIES = {
    "Water Supply": {"en": "water supply problem", "mr": "पाणीपुरवठा समस्या", "hi": "पानी सप्लाई की समस्या"},
    "Roads": {"en": "road problem", "mr": "रस्त्याची समस्या", "hi": "सड़क की समस्या"},
    "Drainage": {"en": "drainage / sewer problem", "mr": "ड्रेनेज / गटार समस्या", "hi": "नाली / सीवर की समस्या"},
    "Power": {"en": "electricity problem", "mr": "वीज पुरवठा समस्या", "hi": "बिजली की समस्या"},
    "Garbage": {"en": "garbage disposal problem", "mr": "कचरा समस्या", "hi": "कचरे की समस्या"},
    "Other": {"en": "civic problem", "mr": "नागरी समस्या", "hi": "नागरिक समस्या"}
}

class ExtractedFields(BaseModel):
    """
    Extracted fields for COMPLAINT / CORRECTION.
    Fields are extracted ONLY if they appear in the transcript.
    Missing fields remain None / null. Never invented.
    """
    problem_category: Optional[CategoryType] = Field(default=None, description="Civic category or null")
    sub_category: Optional[SubCategoryType] = Field(default=None, description="Civic sub-category or null")
    problem: Optional[str] = Field(default=None, description="Problem words from transcript or approved category name")
    place: Optional[str] = Field(default=None, description="Location mentioned in transcript or null")
    duration: Optional[str] = Field(default=None, description="Duration mentioned in transcript or null")
    corrected_field: Optional[Literal["place", "duration", "problem", "problem_category"]] = Field(
        default=None, description="Field being corrected if intent is CORRECTION"
    )

class IntentClassificationResult(BaseModel):
    """
    Strict intent classification model.
    The LLM may only choose from the allowed IntentType list and match this schema.
    """
    intent: IntentType = Field(description="Strict intent from allowed enum")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score")
    fields: ExtractedFields = Field(default_factory=ExtractedFields, description="Extracted problem/place/duration fields")
    summary_en: Optional[str] = Field(default=None, description="Brief English summary if complaint")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(float(v), 3)

class DialogueTurnRecord(BaseModel):
    """
    Stores turn history: transcript, intent, extracted fields, reply.
    """
    turn_id: int
    transcript: str
    intent: IntentType
    extracted_fields: dict
    spoken_reply: str
    state_before: str
    state_after: str
    ticket_created: bool
    ticket_id: Optional[str] = None
