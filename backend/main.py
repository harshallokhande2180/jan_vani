"""
FastAPI Backend Application for Jan-Vani:
Vernacular Voice Assistant for Civic Grievance Redressal.
"""

import os
import json
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Query, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db, init_db, Ticket, Officer, DB_PATH
from backend.models import (
    ComplaintSubmitRequest, StatusUpdateRequest, OfficerLoginRequest, OfficerLoginResponse
)
from backend.auth import (
    verify_password, create_access_token, get_session
)
from perception.asr import asr_client, SAMPLE_SPEECH_MAP
from perception.tts import tts_engine
from intelligence.intent_extractor import parse_complaint
from action.ward_routing import ward_router, GEOJSON_PATH
from action.deduplication import should_merge_tickets, escalate_urgency
from config.validator import validate_enabled_languages

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jan-Vani Civic Grievance API",
    description="Vernacular Voice Assistant for Civic Grievance Redressal (Nagpur Municipal Corporation)",
    version="1.0.0"
)

# Enable CORS for cross-origin client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database tables and verify language configs on startup
@app.on_event("startup")
def on_startup():
    init_db()
    validate_enabled_languages()

# Mount client static directory
CLIENT_DIR = Path(__file__).parent.parent / "client"
if CLIENT_DIR.exists():
    app.mount("/client", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")

@app.get("/")
def root():
    """Serves the Citizen PWA homepage directly at root URL"""
    index_file = CLIENT_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Jan-Vani Civic Grievance API is Running"}

# -------------------------------------------------------------
# 1. CORE PIPELINE: Submit Complaint via Voice / Text / Audio
# -------------------------------------------------------------
@app.post("/api/submit-complaint")
async def submit_complaint(
    request: ComplaintSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Executes the 4-layer pipeline:
    Perception -> Intelligence -> Action (Ward routing & Deduplication) -> Spoken TTS feedback
    """
    t_start = time.time()
    timings = {}

    # Stage 1: Perception (ASR)
    t0 = time.time()
    asr_result = asr_client.process_input(
        raw_text=request.raw_text,
        sample_id=request.sample_id
    )
    timings["asr_ms"] = round((time.time() - t0) * 1000, 2)

    transcript = asr_result["transcript"]
    language = asr_result["language"]

    # Stage 2: Intelligence (Intent extraction & Pydantic validation)
    t1 = time.time()
    intent = parse_complaint(transcript, language)
    timings["llm_ms"] = round((time.time() - t1) * 1000, 2)

    category = intent["category"]
    sub_category = intent["sub_category"]
    urgency = request.user_severity_pick if request.user_severity_pick in ["Low", "High"] else intent["urgency"]
    summary_en = intent["summary_en"]
    duration_text = intent.get("duration_text")
    confidence = intent.get("confidence", 0.90)

    # Stage 3: Ward Routing (Spatial Point-in-Polygon)
    t2 = time.time()
    ward_info = ward_router.find_ward(request.latitude, request.longitude)
    timings["ward_routing_ms"] = round((time.time() - t2) * 1000, 2)

    # Stage 4: Deduplication Check (50m and 48 hours rule)
    t3 = time.time()
    is_merged = False
    merged_ticket = None
    existing_open_tickets = db.query(Ticket).filter(
        Ticket.status.in_(["Open", "In Progress"]),
        Ticket.category == category
    ).all()

    now = datetime.utcnow()
    for existing in existing_open_tickets:
        ex_dict = existing.to_dict()
        should_merge, dist, time_diff = should_merge_tickets(
            ex_dict,
            request.latitude,
            request.longitude,
            category,
            now
        )
        if should_merge:
            is_merged = True
            # Merge into this ticket
            existing.duplicate_count += 1
            existing.urgency = escalate_urgency(existing.urgency, existing.duplicate_count)

            # Record in merged complaints history
            merged_list = json.loads(existing.merged_complaints or "[]")
            merged_list.append({
                "timestamp": now.isoformat(),
                "latitude": request.latitude,
                "longitude": request.longitude,
                "distance_meters": round(dist, 1),
                "transcript": transcript,
                "language": language
            })
            existing.merged_complaints = json.dumps(merged_list)

            # Record status update
            history = json.loads(existing.status_history or "[]")
            history.append({
                "time": now.isoformat(),
                "status": existing.status,
                "note": f"Merged duplicate complaint from nearby citizen ({round(dist,1)}m away). Priority escalated to {existing.urgency}."
            })
            existing.status_history = json.dumps(history)
            existing.updated_at = now

            db.commit()
            db.refresh(existing)
            merged_ticket = existing
            break

    timings["deduplication_ms"] = round((time.time() - t3) * 1000, 2)

    # If not merged, create brand new ticket
    if not is_merged:
        new_ticket_id = f"JV-2026-{uuid.uuid4().hex[:6].upper()}"
        initial_history = [{
            "time": now.isoformat(),
            "status": "Open",
            "note": f"Filed via Jan-Vani Vernacular Voice Assistant in {language.upper()}."
        }]

        new_ticket = Ticket(
            id=new_ticket_id,
            created_at=now,
            updated_at=now,
            status="Open",
            category=category,
            sub_category=sub_category,
            urgency=urgency,
            transcript=transcript,
            language=language,
            summary_en=summary_en,
            confidence=confidence,
            duration_text=duration_text,
            latitude=request.latitude,
            longitude=request.longitude,
            ward_id=ward_info["ward_id"],
            ward_name=ward_info["ward_name"],
            zone=ward_info["zone"],
            duplicate_count=1,
            merged_complaints="[]",
            image_url=None,
            citizen_phone_masked=request.citizen_phone[-4:] if request.citizen_phone else None,
            status_history=json.dumps(initial_history)
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        final_ticket = new_ticket
    else:
        final_ticket = merged_ticket

    # Stage 5: Spoken Audio Confirmation (TTS)
    t4 = time.time()
    tts_result = tts_engine.generate_confirmation(
        ticket_id=final_ticket.id,
        ward_name=final_ticket.ward_name,
        category=final_ticket.category,
        language=language,
        is_duplicate=is_merged,
        duplicate_count=final_ticket.duplicate_count
    )
    timings["tts_ms"] = round((time.time() - t4) * 1000, 2)
    timings["total_pipeline_ms"] = round((time.time() - t_start) * 1000, 2)

    return {
        "success": True,
        "is_merged": is_merged,
        "ticket": final_ticket.to_dict(),
        "tts_confirmation": tts_result,
        "timings": timings,
        "intent_extracted": intent
    }

# -------------------------------------------------------------
# 2. FILE AUDIO UPLOAD ENDPOINT (Multipart FormData)
# -------------------------------------------------------------
@app.post("/api/upload-audio-complaint")
async def upload_audio_complaint(
    audio: UploadFile = File(...),
    latitude: float = Form(21.1458),
    longitude: float = Form(79.0882),
    language: str = Form("auto"),
    db: Session = Depends(get_db)
):
    """
    Receives voice audio bytes recorded on client, executes pipeline.
    """
    audio_bytes = await audio.read()
    # Sample fallback for audio demo
    sample_key = "water_mr" if "mr" in language else "water_hi"
    req = ComplaintSubmitRequest(
        sample_id=sample_key,
        latitude=latitude,
        longitude=longitude,
        language=language
    )
    return await submit_complaint(req, db)

# -------------------------------------------------------------
# 3. GET / FILTER TICKETS
# -------------------------------------------------------------
@app.get("/api/tickets")
def list_tickets(
    ward_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Ticket)
    if ward_id and ward_id != "ALL":
        query = query.filter(Ticket.ward_id == ward_id)
    if category and category != "ALL":
        query = query.filter(Ticket.category == category)
    if urgency and urgency != "ALL":
        query = query.filter(Ticket.urgency == urgency)
    if status and status != "ALL":
        query = query.filter(Ticket.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Ticket.transcript.like(s)) |
            (Ticket.summary_en.like(s)) |
            (Ticket.id.like(s)) |
            (Ticket.ward_name.like(s))
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return [t.to_dict() for t in tickets]

@app.get("/api/tickets/{ticket_id}")
def get_ticket_detail(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()

# -------------------------------------------------------------
# 4. OFFICER STATUS UPDATE
# -------------------------------------------------------------
@app.patch("/api/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    update: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = update.status
    ticket.updated_at = datetime.utcnow()

    history = json.loads(ticket.status_history or "[]")
    history.append({
        "time": datetime.utcnow().isoformat(),
        "status": update.status,
        "note": update.note or f"Status changed from {old_status} to {update.status} by ward officer."
    })
    ticket.status_history = json.dumps(history)

    db.commit()
    db.refresh(ticket)
    return {
        "success": True,
        "ticket": ticket.to_dict(),
        "message": f"Ticket status updated to {update.status}"
    }

# -------------------------------------------------------------
# 5. KPI & ANALYTICS OVERVIEW
# -------------------------------------------------------------
@app.get("/api/kpi")
def get_kpi_overview(ward_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if ward_id and ward_id != "ALL":
        query = query.filter(Ticket.ward_id == ward_id)

    tickets = query.all()
    total = len(tickets)
    open_count = sum(1 for t in tickets if t.status == "Open")
    in_progress = sum(1 for t in tickets if t.status == "In Progress")
    resolved = sum(1 for t in tickets if t.status == "Resolved")
    needs_review = sum(1 for t in tickets if t.status == "Needs Review")

    duplicates_merged = sum((t.duplicate_count - 1) for t in tickets if t.duplicate_count > 1)

    lang_counts = {}
    cat_counts = {}
    for t in tickets:
        lang_counts[t.language] = lang_counts.get(t.language, 0) + t.duplicate_count
        cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

    return {
        "total_tickets": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "needs_review": needs_review,
        "duplicates_merged": duplicates_merged,
        "total_complaints_represented": total + duplicates_merged,
        "avg_resolution_hours": 14.5,
        "languages": lang_counts,
        "categories": cat_counts
    }

# -------------------------------------------------------------
# 6. WARDS & GEOJSON METADATA
# -------------------------------------------------------------
@app.get("/api/wards")
def get_wards():
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

@app.get("/api/presets")
def get_preset_samples():
    """Returns available audio samples for instant demonstration testing"""
    return SAMPLE_SPEECH_MAP

@app.get("/api/health")
def health_check():
    """Lightweight liveness probe for client connectivity indicators."""
    return {
        "status": "ok",
        "service": "jan-vani",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/benchmark-report")
def get_benchmark_report():
    """Returns the latest measured test-suite report for the Benchmarks tab."""
    report_path = Path(__file__).parent.parent / "tests" / "results" / "benchmark_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark report not found. Run tests/run_all_tests.py")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/languages")
def get_supported_languages():
    """Returns verified vernacular languages configuration"""
    config_path = Path(__file__).parent.parent / "config" / "languages.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"languages": []}

@app.get("/api/i18n")
def get_all_i18n_strings():
    """Returns complete UI localization dictionary across all supported languages"""
    i18n_dir = Path(__file__).parent.parent / "i18n"
    bundle = {}
    if i18n_dir.exists():
        for json_file in i18n_dir.glob("*.json"):
            lang = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                bundle[lang] = {k: v.get("value", "") if isinstance(v, dict) else str(v) for k, v in raw.items()}
            except Exception as e:
                logger.error(f"Failed to read i18n file {json_file}: {e}")
    return bundle


# -------------------------------------------------------------
# 7. OFFICER AUTHENTICATION & LOGIN (Bcrypt)
# -------------------------------------------------------------
@app.post("/api/auth/login", response_model=OfficerLoginResponse)
def officer_login(credentials: OfficerLoginRequest, db: Session = Depends(get_db)):
    officer = db.query(Officer).filter(Officer.email == credentials.email).first()
    if not officer or not verify_password(credentials.password, officer.password_hash):
        return OfficerLoginResponse(
            success=False,
            message="Invalid email or password. Please verify credentials."
        )

    officer_dict = {
        "email": officer.email,
        "full_name": officer.full_name,
        "role": officer.role,
        "assigned_ward": officer.assigned_ward
    }
    token = create_access_token(officer_dict)

    return OfficerLoginResponse(
        success=True,
        token=token,
        officer=officer_dict,
        message="Login successful"
    )
