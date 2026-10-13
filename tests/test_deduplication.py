"""
Test Suite: Deduplication Engine (Section 5.3)
Checks 30+ hand-made pairs (near, far, old, new, same category, different category).
Measures: False merges and Missed merges.
Target: 0 false merges.
"""

from datetime import datetime, timedelta
from action.deduplication import should_merge_tickets

def generate_deduplication_pairs():
    base_time = datetime(2026, 10, 1, 10, 0, 0)
    base_lat = 21.14580
    base_lon = 79.08820
    category = "Water Supply"

    pairs = []

    # 1. NEAR & NEW (<= 50m, <= 48h, same category) -> SHOULD MERGE (True)
    for i in range(10):
        # vary distance between 5m and 45m (~0.00005 to 0.00035 degrees)
        lat_offset = (i * 3.5) / 111111.0
        time_offset_hrs = 2.0 + (i * 3.5)  # 2h to 33.5h
        pairs.append({
            "name": f"near_new_case_{i+1}",
            "existing": {
                "latitude": base_lat,
                "longitude": base_lon,
                "category": category,
                "status": "Open",
                "created_at": base_time
            },
            "new_lat": base_lat + lat_offset,
            "new_lon": base_lon,
            "new_category": category,
            "new_time": base_time + timedelta(hours=time_offset_hrs),
            "expected_merge": True
        })

    # 2. FAR & NEW (> 50m, <= 48h, same category) -> SHOULD NOT MERGE (False)
    for i in range(8):
        # vary distance between 70m and 350m
        lat_offset = (70.0 + i * 35.0) / 111111.0
        pairs.append({
            "name": f"far_new_case_{i+1}",
            "existing": {
                "latitude": base_lat,
                "longitude": base_lon,
                "category": category,
                "status": "Open",
                "created_at": base_time
            },
            "new_lat": base_lat + lat_offset,
            "new_lon": base_lon,
            "new_category": category,
            "new_time": base_time + timedelta(hours=10),
            "expected_merge": False
        })

    # 3. NEAR & OLD (<= 50m, > 48h, same category) -> SHOULD NOT MERGE (False)
    for i in range(6):
        # time difference > 48 hours (e.g. 52h to 100h)
        time_offset_hrs = 50.0 + (i * 10.0)
        pairs.append({
            "name": f"near_old_case_{i+1}",
            "existing": {
                "latitude": base_lat,
                "longitude": base_lon,
                "category": category,
                "status": "Open",
                "created_at": base_time
            },
            "new_lat": base_lat + 0.0001,
            "new_lon": base_lon,
            "new_category": category,
            "new_time": base_time + timedelta(hours=time_offset_hrs),
            "expected_merge": False
        })

    # 4. NEAR & NEW BUT DIFFERENT CATEGORY (<= 50m, <= 48h, diff category) -> SHOULD NOT MERGE (False)
    diff_cats = ["Roads", "Drainage", "Power", "Garbage", "Other", "Roads"]
    for i, cat in enumerate(diff_cats):
        pairs.append({
            "name": f"near_diff_cat_case_{i+1}",
            "existing": {
                "latitude": base_lat,
                "longitude": base_lon,
                "category": category,
                "status": "Open",
                "created_at": base_time
            },
            "new_lat": base_lat + 0.0001,
            "new_lon": base_lon,
            "new_category": cat,
            "new_time": base_time + timedelta(hours=5),
            "expected_merge": False
        })

    return pairs

def run_deduplication_tests():
    pairs = generate_deduplication_pairs()
    false_merges = 0
    missed_merges = 0
    total = len(pairs)

    for case in pairs:
        should_merge, dist, time_diff = should_merge_tickets(
            case["existing"],
            case["new_lat"],
            case["new_lon"],
            case["new_category"],
            case["new_time"]
        )

        expected = case["expected_merge"]
        if should_merge and not expected:
            false_merges += 1
        elif not should_merge and expected:
            missed_merges += 1

    accuracy = ((total - false_merges - missed_merges) / total) * 100.0

    return {
        "test_name": "Deduplication Engine",
        "total_pairs": total,
        "false_merges": false_merges,
        "missed_merges": missed_merges,
        "accuracy_pct": round(accuracy, 2),
        "passed": false_merges == 0 and missed_merges == 0
    }

if __name__ == "__main__":
    result = run_deduplication_tests()
    print("Deduplication Results:", result)
