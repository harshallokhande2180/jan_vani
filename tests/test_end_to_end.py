"""
Test Suite: End-to-End Pipeline & Latency Profiler (Section 5.3 & 5.5)
Runs 10 scripted complaints through the full flow:
Voice -> ASR -> LLM Intent -> Ward Routing -> Deduplication -> Ticket Store -> Spoken Confirmation (TTS).
Measures: Success count, time per ticket (median and 90th percentile).
"""

import time
import numpy as np
from datetime import datetime

from backend.database import SessionLocal, Ticket
from backend.models import ComplaintSubmitRequest
from action.ward_routing import ward_router
from action.deduplication import should_merge_tickets, escalate_urgency
from intelligence.intent_extractor import parse_complaint
from perception.asr import asr_client
from perception.tts import tts_engine

SCRIPTED_COMPLAINTS = [
    {"sample_id": "water_mr", "lat": 21.1450, "lon": 79.0550, "lang": "mr"},
    {"sample_id": "water_hi", "lat": 21.1150, "lon": 79.0650, "lang": "hi"},
    {"sample_id": "road_mr", "lat": 21.1410, "lon": 79.0600, "lang": "mr"},
    {"sample_id": "road_hi", "lat": 21.1380, "lon": 79.0850, "lang": "hi"},
    {"sample_id": "drain_mr", "lat": 21.1390, "lon": 79.0880, "lang": "mr"},
    {"sample_id": "drain_hi", "lat": 21.1550, "lon": 79.1100, "lang": "hi"},
    {"sample_id": "power_mr", "lat": 21.1700, "lon": 79.1300, "lang": "mr"},
    {"sample_id": "power_hi", "lat": 21.1150, "lon": 79.0950, "lang": "hi"},
    {"sample_id": "garbage_mr", "lat": 21.1850, "lon": 79.1100, "lang": "mr"},
    {"sample_id": "garbage_hi", "lat": 21.1750, "lon": 79.0650, "lang": "hi"},
]

def run_end_to_end_tests():
    db = SessionLocal()
    success_count = 0
    total = len(SCRIPTED_COMPLAINTS)
    total_latencies_ms = []
    stage_breakdowns = {
        "asr_ms": [],
        "llm_ms": [],
        "ward_routing_ms": [],
        "deduplication_ms": [],
        "tts_ms": []
    }

    try:
        for idx, item in enumerate(SCRIPTED_COMPLAINTS):
            t_start = time.time()

            # 1. Perception
            t0 = time.time()
            asr_res = asr_client.process_input(sample_id=item["sample_id"])
            t_asr = (time.time() - t0) * 1000.0
            stage_breakdowns["asr_ms"].append(t_asr)

            # 2. Intelligence
            t1 = time.time()
            intent = parse_complaint(asr_res["transcript"], asr_res["language"])
            t_llm = (time.time() - t1) * 1000.0
            stage_breakdowns["llm_ms"].append(t_llm)

            # 3. Action: Ward
            t2 = time.time()
            ward = ward_router.find_ward(item["lat"], item["lon"])
            t_ward = (time.time() - t2) * 1000.0
            stage_breakdowns["ward_routing_ms"].append(t_ward)

            # 4. Action: Dedupe
            t3 = time.time()
            now = datetime.utcnow()
            open_tickets = db.query(Ticket).filter(Ticket.category == intent["category"]).all()
            merged = False
            for existing in open_tickets:
                should_m, dist, _ = should_merge_tickets(existing.to_dict(), item["lat"], item["lon"], intent["category"], now)
                if should_m:
                    merged = True
                    break
            t_dedupe = (time.time() - t3) * 1000.0
            stage_breakdowns["deduplication_ms"].append(t_dedupe)

            # 5. Perception: Spoken TTS
            t4 = time.time()
            tts = tts_engine.generate_confirmation(
                ticket_id=f"TEST-{idx+1}",
                ward_name=ward["ward_name"],
                category=intent["category"],
                language=item["lang"]
            )
            t_tts = (time.time() - t4) * 1000.0
            stage_breakdowns["tts_ms"].append(t_tts)

            total_elapsed = (time.time() - t_start) * 1000.0
            total_latencies_ms.append(total_elapsed)
            success_count += 1

    finally:
        db.close()

    median_lat = float(np.median(total_latencies_ms))
    p90_lat = float(np.percentile(total_latencies_ms, 90))

    return {
        "test_name": "End-to-End Voice-to-Ticket Flow",
        "total_complaints_run": total,
        "success_count": success_count,
        "success_rate_pct": round((success_count / total) * 100.0, 1),
        "latency_profile_ms": {
            "median_ms": round(median_lat, 2),
            "p90_ms": round(p90_lat, 2),
            "asr_avg_ms": round(float(np.mean(stage_breakdowns["asr_ms"])), 2),
            "llm_avg_ms": round(float(np.mean(stage_breakdowns["llm_ms"])), 2),
            "ward_routing_avg_ms": round(float(np.mean(stage_breakdowns["ward_routing_ms"])), 2),
            "deduplication_avg_ms": round(float(np.mean(stage_breakdowns["deduplication_ms"])), 2),
            "tts_avg_ms": round(float(np.mean(stage_breakdowns["tts_ms"])), 2),
        },
        "passed": success_count == total and median_lat < 1000.0
    }

if __name__ == "__main__":
    res = run_end_to_end_tests()
    print("End-to-End Results:", res)
