"""
Database models and connection engine for Jan-Vani.
Uses SQLite with SQLAlchemy, easily swappable with PostgreSQL/PostGIS.
Includes index definitions on coordinates, status, ward, and timestamps.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import bcrypt

DB_PATH = Path(__file__).parent.parent / "data" / "jan_vani.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(32), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(32), default="Open", index=True)  # Open, In Progress, Resolved, Needs Review
    category = Column(String(64), nullable=False, index=True)
    sub_category = Column(String(64), nullable=False)
    urgency = Column(String(32), default="Medium", index=True)  # Low, Medium, High
    transcript = Column(Text, nullable=False)
    language = Column(String(16), default="mr", index=True)  # mr, hi, en
    summary_en = Column(Text, nullable=False)
    confidence = Column(Float, default=0.90)
    duration_text = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    ward_id = Column(String(32), nullable=False, index=True)
    ward_name = Column(String(64), nullable=False)
    zone = Column(Integer, default=1)
    duplicate_count = Column(Integer, default=1)
    merged_complaints = Column(Text, default="[]")  # JSON list
    audio_url = Column(String(256), nullable=True)
    image_url = Column(String(256), nullable=True)
    citizen_phone_masked = Column(String(32), nullable=True)
    status_history = Column(Text, default="[]")  # JSON timeline

    __table_args__ = (
        Index("idx_geo_spatial", "latitude", "longitude"),
        Index("idx_ward_category_status", "ward_id", "category", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "category": self.category,
            "sub_category": self.sub_category,
            "urgency": self.urgency,
            "transcript": self.transcript,
            "language": self.language,
            "summary_en": self.summary_en,
            "confidence": self.confidence,
            "duration_text": self.duration_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "ward_id": self.ward_id,
            "ward_name": self.ward_name,
            "zone": self.zone,
            "duplicate_count": self.duplicate_count,
            "merged_complaints": json.loads(self.merged_complaints or "[]"),
            "audio_url": self.audio_url,
            "image_url": self.image_url,
            "citizen_phone_masked": self.citizen_phone_masked,
            "status_history": json.loads(self.status_history or "[]")
        }

class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default="ward_officer")  # ward_officer or municipal_head
    assigned_ward = Column(String(32), nullable=True)  # WARD-02, WARD-04, or None for commissioner

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Creates tables and seeds initial officers and demo tickets.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed officers if not exist
        if db.query(Officer).count() == 0:
            def hash_pw(pw: str) -> str:
                return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

            officers = [
                Officer(
                    email="head@nmc.gov.in",
                    password_hash=hash_pw("admin123"),
                    full_name="Dr. Rajeshwar Rao (Commissioner)",
                    role="municipal_head",
                    assigned_ward=None
                ),
                Officer(
                    email="officer.dharampeth@nmc.gov.in",
                    password_hash=hash_pw("ward123"),
                    full_name="Pooja Sharma (Ward 2 Officer)",
                    role="ward_officer",
                    assigned_ward="WARD-02"
                ),
                Officer(
                    email="officer.dhantoli@nmc.gov.in",
                    password_hash=hash_pw("ward123"),
                    full_name="Sanjay Deshmukh (Ward 4 Officer)",
                    role="ward_officer",
                    assigned_ward="WARD-04"
                ),
                Officer(
                    email="officer.laxminagar@nmc.gov.in",
                    password_hash=hash_pw("ward123"),
                    full_name="Anita Patil (Ward 1 Officer)",
                    role="ward_officer",
                    assigned_ward="WARD-01"
                )
            ]
            db.add_all(officers)
            db.commit()

        # Seed sample tickets if empty
        if db.query(Ticket).count() == 0:
            from datetime import timedelta
            now = datetime.utcnow()

            sample_seed_tickets = [
                Ticket(
                    id="JV-2026-001",
                    created_at=now - timedelta(hours=36),
                    status="Open",
                    category="Water Supply",
                    sub_category="Leakage",
                    urgency="High",
                    transcript="आमच्या गल्लीत पिण्याच्या पाण्याची मुख्य पाइपलाइन फुटली आहे, तीन दिवसांपासून पाणी वाहत आहे.",
                    language="mr",
                    summary_en="Drinking water pipeline burst and leaking onto the street for 3 days.",
                    confidence=0.95,
                    duration_text="3 days",
                    latitude=21.1450,
                    longitude=79.0550,
                    ward_id="WARD-02",
                    ward_name="Dharampeth",
                    zone=2,
                    duplicate_count=4,
                    merged_complaints=json.dumps([
                        {"timestamp": (now - timedelta(hours=36)).isoformat(), "source": "Citizen Voice 1 (Marathi)", "note": "Pipeline burst"},
                        {"timestamp": (now - timedelta(hours=28)).isoformat(), "source": "Citizen Voice 2 (Marathi)", "note": "Heavy water flowing on road"},
                        {"timestamp": (now - timedelta(hours=14)).isoformat(), "source": "Citizen Voice 3 (Hindi)", "note": "Water wastage in Dharampeth"},
                        {"timestamp": (now - timedelta(hours=6)).isoformat(), "source": "Citizen Voice 4 (Marathi)", "note": "Water supply stopped in nearby houses"}
                    ]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=36)).isoformat(), "status": "Open", "note": "Complaint filed via vernacular voice assistant"},
                        {"time": (now - timedelta(hours=28)).isoformat(), "status": "Open", "note": "Merged complaint 2 from nearby citizen; escalated priority to High"}
                    ])
                ),
                Ticket(
                    id="JV-2026-002",
                    created_at=now - timedelta(hours=42),
                    status="In Progress",
                    category="Roads",
                    sub_category="Damage",
                    urgency="High",
                    transcript="धरमपेठ मुख्य रस्त्यावर मोठा खड्डा पडला आहे, काल रात्री दोन दुचाकींचा अपघात झाला.",
                    language="mr",
                    summary_en="Hazardous deep pothole on Dharampeth main road causing vehicle accidents.",
                    confidence=0.93,
                    duration_text="since yesterday",
                    latitude=21.1410,
                    longitude=79.0600,
                    ward_id="WARD-02",
                    ward_name="Dharampeth",
                    zone=2,
                    duplicate_count=2,
                    merged_complaints=json.dumps([
                        {"timestamp": (now - timedelta(hours=42)).isoformat(), "source": "Citizen Voice 1 (Marathi)", "note": "Pothole report"},
                        {"timestamp": (now - timedelta(hours=30)).isoformat(), "source": "Citizen Voice 2 (Hindi)", "note": "Accident danger"}
                    ]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=42)).isoformat(), "status": "Open", "note": "Filed by citizen"},
                        {"time": (now - timedelta(hours=12)).isoformat(), "status": "In Progress", "note": "Repair crew dispatched with asphalt patch"}
                    ])
                ),
                Ticket(
                    id="JV-2026-003",
                    created_at=now - timedelta(hours=18),
                    status="Open",
                    category="Drainage",
                    sub_category="Disruption",
                    urgency="Medium",
                    transcript="घरासमोरचे गटार तुंबले आहे आणि घाण पाणी रस्त्यावर येत आहे, दुर्गंधी सुटली आहे.",
                    language="mr",
                    summary_en="Clogged municipal drain overflowing foul sewage onto pedestrian road.",
                    confidence=0.91,
                    duration_text="2 days",
                    latitude=21.1390,
                    longitude=79.0880,
                    ward_id="WARD-04",
                    ward_name="Dhantoli",
                    zone=4,
                    duplicate_count=1,
                    merged_complaints=json.dumps([]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=18)).isoformat(), "status": "Open", "note": "Filed by citizen"}
                    ])
                ),
                Ticket(
                    id="JV-2026-004",
                    created_at=now - timedelta(hours=50),
                    status="Resolved",
                    category="Power",
                    sub_category="Disruption",
                    urgency="High",
                    transcript="ट्रांसफार्मर में आग लगने के बाद से पूरे इलाके की बिजली गुल है, भयंकर अंधेरा है।",
                    language="hi",
                    summary_en="Transformer fire resulting in complete power outage in locality.",
                    confidence=0.94,
                    duration_text="since night",
                    latitude=21.1150,
                    longitude=79.0650,
                    ward_id="WARD-01",
                    ward_name="Laxmi Nagar",
                    zone=1,
                    duplicate_count=3,
                    merged_complaints=json.dumps([
                        {"timestamp": (now - timedelta(hours=50)).isoformat(), "source": "Citizen 1 (Hindi)"},
                        {"timestamp": (now - timedelta(hours=48)).isoformat(), "source": "Citizen 2 (Hindi)"},
                        {"timestamp": (now - timedelta(hours=45)).isoformat(), "source": "Citizen 3 (Marathi)"}
                    ]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=50)).isoformat(), "status": "Open", "note": "Filed"},
                        {"time": (now - timedelta(hours=40)).isoformat(), "status": "In Progress", "note": "MSEDCL electrician team on-site"},
                        {"time": (now - timedelta(hours=15)).isoformat(), "status": "Resolved", "note": "Transformer replaced and power restored"}
                    ])
                ),
                Ticket(
                    id="JV-2026-005",
                    created_at=now - timedelta(hours=8),
                    status="Open",
                    category="Garbage",
                    sub_category="Disruption",
                    urgency="Low",
                    transcript="सड़क किनारे भारी कचरा जमा हो गया है, बदबू के कारण सांस लेना मुश्किल हो गया है।",
                    language="hi",
                    summary_en="Solid waste accumulation by roadside requiring sanitation vehicle pick-up.",
                    confidence=0.88,
                    duration_text="4 days",
                    latitude=21.1550,
                    longitude=79.1100,
                    ward_id="WARD-06",
                    ward_name="Gandhibagh",
                    zone=6,
                    duplicate_count=1,
                    merged_complaints=json.dumps([]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=8)).isoformat(), "status": "Open", "note": "Filed by citizen"}
                    ])
                ),
                Ticket(
                    id="JV-2026-006",
                    created_at=now - timedelta(hours=5),
                    status="Open",
                    category="Water Supply",
                    sub_category="Contamination",
                    urgency="High",
                    transcript="नळात गढूळ आणि घाण वास येणारे पाणी येत आहे, लहान मुले आजारी पडत आहेत.",
                    language="mr",
                    summary_en="Contaminated discolored drinking water supply from municipal tap posing health hazard.",
                    confidence=0.92,
                    duration_text="today",
                    latitude=21.1800,
                    longitude=79.1300,
                    ward_id="WARD-07",
                    ward_name="Satranjipura",
                    zone=7,
                    duplicate_count=2,
                    merged_complaints=json.dumps([
                        {"timestamp": (now - timedelta(hours=5)).isoformat(), "source": "Citizen 1 (Marathi)"},
                        {"timestamp": (now - timedelta(hours=2)).isoformat(), "source": "Citizen 2 (Hindi)"}
                    ]),
                    status_history=json.dumps([
                        {"time": (now - timedelta(hours=5)).isoformat(), "status": "Open", "note": "Filed by citizen"}
                    ])
                )
            ]
            db.add_all(sample_seed_tickets)
            db.commit()
    finally:
        db.close()
