"""
Pydantic API models for Jan-Vani FastAPI backend.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ComplaintSubmitRequest(BaseModel):
    raw_text: Optional[str] = None
    sample_id: Optional[str] = None  # preset demonstration voice
    language: Optional[str] = "auto"
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    citizen_phone: Optional[str] = None
    user_severity_pick: Optional[str] = "Medium"  # Low, Medium, High picked by user
    image_base64: Optional[str] = None

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Open, In Progress, Resolved, or Needs Review")
    note: Optional[str] = None

class OfficerLoginRequest(BaseModel):
    email: str
    password: str

class OfficerLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    officer: Optional[Dict[str, Any]] = None
    message: str
