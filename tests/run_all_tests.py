"""
Master Test Runner for Jan-Vani Test Suites (Section 5.3 & 12).
Executes Deduplication, Ward Routing, LLM Schema, ASR Quality, and End-to-End benchmarks.
Generates dated results in tests/results/ and terminal summary.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
from datetime import datetime, timezone

from tests.test_deduplication import run_deduplication_tests
from tests.test_ward_routing import run_ward_routing_tests
from tests.test_llm_schema import run_llm_schema_tests
from tests.test_asr_quality import run_asr_quality_tests
from tests.test_end_to_end import run_end_to_end_tests

def run_all():
    print("=" * 70)
    print("   JAN-VANI VERIFIABLE BENCHMARK SUITE - SECTION 5.3 RUNNER")
    print("=" * 70)

    run_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Deduplication
    print("\n[1/5] Running Deduplication Tests (30 pairs: near, far, old, new)...")
    dedupe_res = run_deduplication_tests()
    print(f"  -> Accuracy: {dedupe_res['accuracy_pct']}% | False Merges: {dedupe_res['false_merges']} | Missed: {dedupe_res['missed_merges']}")

    # 2. Ward Routing
    print("\n[2/5] Running Ward GPS Routing Tests (21 known points)...")
    ward_res = run_ward_routing_tests()
    print(f"  -> Accuracy: {ward_res['accuracy_rate_pct']}% ({ward_res['correct_points']}/{ward_res['total_test_points']} points)")

    # 3. LLM Schema
    print("\n[3/5] Running LLM Schema Validation (40 Hindi & Marathi sentences)...")
    schema_res = run_llm_schema_tests()
    print(f"  -> Valid Schema: {schema_res['valid_schema_rate_pct']}% | Category Accuracy: {schema_res['category_accuracy_pct']}%")

    # 4. ASR Quality
    print("\n[4/5] Running ASR Quality & WER Tests (20 regional speech samples)...")
    asr_res = run_asr_quality_tests()
    print(f"  -> Average WER: {asr_res['average_wer_pct']}% | Transcript Accuracy: {asr_res['transcript_accuracy_pct']}%")

    # 5. End-to-End Latency
    print("\n[5/5] Running End-to-End Voice-to-Ticket Pipeline (10 complaints)...")
    e2e_res = run_end_to_end_tests()
    lat = e2e_res["latency_profile_ms"]
    print(f"  -> Success: {e2e_res['success_rate_pct']}% | Median Latency: {lat['median_ms']}ms | P90: {lat['p90_ms']}ms")

    report = {
        "run_date": run_timestamp,
        "results": {
            "deduplication": dedupe_res,
            "ward_routing": ward_res,
            "llm_schema": schema_res,
            "asr_quality": asr_res,
            "end_to_end": e2e_res
        }
    }

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_file = results_dir / "benchmark_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"[SUCCESS] All test suites completed! Results saved to:\n   {report_file}")
    print("=" * 70)

    return report

if __name__ == "__main__":
    run_all()
