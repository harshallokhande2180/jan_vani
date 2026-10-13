"""
Pydantic schema for Grievance Intent Extraction.
Strictly enforced as per Section 3.3 of Jan-Vani Specification.
Rejects malformed LLM outputs and assigns fallback 'needs review'.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

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

class GrievanceExtraction(BaseModel):
    category: CategoryType = Field(description="Civic category")
    sub_category: SubCategoryType = Field(description="Civic sub-category")
    urgency: UrgencyType = Field(description="Urgency assessment")
    duration_text: Optional[str] = Field(default=None, description="Free text duration mentioned or null")
    summary_en: str = Field(description="One English sentence describing the problem")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(float(v), 3)

class FallbackExtraction(BaseModel):
    category: CategoryType = "Other"
    sub_category: SubCategoryType = "Other"
    urgency: UrgencyType = "Medium"
    duration_text: Optional[str] = None
    summary_en: str = "Uncertain complaint requiring manual officer review"
    confidence: float = 0.35
    needs_review: bool = True
