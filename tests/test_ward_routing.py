"""
Test Suite: Ward Routing by GPS (Section 5.3)
Tests 20+ known coordinate locations across Nagpur Municipal Corporation (NMC)
administrative wards (Dharampeth, Dhantoli, Laxmi Nagar, Gandhibagh, etc.).
Measures: Correct ward assignment rate.
"""

from action.ward_routing import ward_router

KNOWN_NAGPUR_POINTS = [
    # WARD-02: Dharampeth
    {"lat": 21.1450, "lon": 79.0550, "expected_ward": "WARD-02", "name": "Dharampeth Coffee House"},
    {"lat": 21.1400, "lon": 79.0500, "expected_ward": "WARD-02", "name": "Ram Nagar Square"},
    {"lat": 21.1500, "lon": 79.0600, "expected_ward": "WARD-02", "name": "Gokulpeth Market"},
    {"lat": 21.1350, "lon": 79.0450, "expected_ward": "WARD-02", "name": "Shankar Nagar"},

    # WARD-04: Dhantoli
    {"lat": 21.1380, "lon": 79.0850, "expected_ward": "WARD-04", "name": "Dhantoli Hospital Belt"},
    {"lat": 21.1420, "lon": 79.0820, "expected_ward": "WARD-04", "name": "Mehadia Square"},
    {"lat": 21.1480, "lon": 79.0900, "expected_ward": "WARD-04", "name": "Congress Nagar"},

    # WARD-01: Laxmi Nagar
    {"lat": 21.1150, "lon": 79.0650, "expected_ward": "WARD-01", "name": "Laxmi Nagar Square"},
    {"lat": 21.1200, "lon": 79.0700, "expected_ward": "WARD-01", "name": "Bajaj Nagar"},
    {"lat": 21.1080, "lon": 79.0580, "expected_ward": "WARD-01", "name": "Pratap Nagar"},

    # WARD-03: Hanuman Nagar
    {"lat": 21.1150, "lon": 79.0950, "expected_ward": "WARD-03", "name": "Medical College Square"},
    {"lat": 21.1220, "lon": 79.1050, "expected_ward": "WARD-03", "name": "Reshimbagh Ground"},

    # WARD-05: Nehru Nagar
    {"lat": 21.1180, "lon": 79.1300, "expected_ward": "WARD-05", "name": "Sakkardara Lake"},
    {"lat": 21.1250, "lon": 79.1400, "expected_ward": "WARD-05", "name": "Dighori Naka"},

    # WARD-06: Gandhibagh
    {"lat": 21.1550, "lon": 79.1050, "expected_ward": "WARD-06", "name": "Gandhibagh Garden"},
    {"lat": 21.1600, "lon": 79.1150, "expected_ward": "WARD-06", "name": "Itwari Wholesale Market"},

    # WARD-07: Satranjipura
    {"lat": 21.1700, "lon": 79.1300, "expected_ward": "WARD-07", "name": "Satranjipura Central"},
    {"lat": 21.1750, "lon": 79.1400, "expected_ward": "WARD-07", "name": "Mehndibagh Road"},

    # WARD-08: Lakadganj
    {"lat": 21.1480, "lon": 79.1450, "expected_ward": "WARD-08", "name": "Lakadganj Timber Market"},

    # WARD-09: Ashi Nagar
    {"lat": 21.1850, "lon": 79.1100, "expected_ward": "WARD-09", "name": "Kamgar Nagar Square"},

    # WARD-10: Mangalwari
    {"lat": 21.1750, "lon": 79.0650, "expected_ward": "WARD-10", "name": "Sadar Residency Road"}
]

def run_ward_routing_tests():
    total = len(KNOWN_NAGPUR_POINTS)
    correct = 0
    failures = []

    for pt in KNOWN_NAGPUR_POINTS:
        matched = ward_router.find_ward(pt["lat"], pt["lon"])
        matched_ward_id = matched["ward_id"]
        if matched_ward_id == pt["expected_ward"]:
            correct += 1
        else:
            failures.append({
                "location": pt["name"],
                "coords": (pt["lat"], pt["lon"]),
                "expected": pt["expected_ward"],
                "got": matched_ward_id,
                "matched_by": matched.get("matched_by")
            })

    rate = (correct / total) * 100.0
    return {
        "test_name": "Ward GPS Routing",
        "total_test_points": total,
        "correct_points": correct,
        "accuracy_rate_pct": round(rate, 2),
        "failures": failures,
        "passed": rate >= 90.0
    }

if __name__ == "__main__":
    res = run_ward_routing_tests()
    print("Ward Routing Results:", res)
