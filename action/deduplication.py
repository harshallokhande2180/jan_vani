"""
Deduplication Engine for Jan-Vani.
Rule:
If an incoming complaint has:
1. The exact same category (e.g. 'Water Supply' == 'Water Supply')
2. Distance <= 50 meters from an open ticket
3. Time <= 48 hours (created within last 48 hours)
4. Status is currently 'Open' or 'In Progress'

Then:
- MERGE into the existing ticket!
- Increase duplicate_count (merged citizen complaints)
- Escalates priority / urgency if multiple citizens report the same issue (e.g. Low -> Medium -> High)
- Logs merged complaint in merged_complaints audit list
- Returns is_duplicate=True with parent ticket ID
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from action.ward_routing import haversine_distance_meters

DUPLICATE_DISTANCE_THRESHOLD_METERS = 50.0
DUPLICATE_TIME_THRESHOLD_HOURS = 48.0

def should_merge_tickets(
    existing_ticket: Dict[str, Any],
    new_lat: float,
    new_lon: float,
    new_category: str,
    new_timestamp: Optional[datetime] = None
) -> Tuple[bool, float, float]:
    """
    Checks if a new complaint should be merged with an existing ticket.
    Returns (should_merge, distance_meters, time_diff_hours).
    """
    # 1. Must be in Open or In Progress status
    status = existing_ticket.get("status", "Open")
    if status not in ["Open", "In Progress"]:
        return False, -1.0, -1.0

    # 2. Must match category
    if existing_ticket.get("category", "").lower() != new_category.lower():
        return False, -1.0, -1.0

    # 3. Distance check <= 50m
    dist = haversine_distance_meters(
        existing_ticket["latitude"],
        existing_ticket["longitude"],
        new_lat,
        new_lon
    )
    if dist > DUPLICATE_DISTANCE_THRESHOLD_METERS:
        return False, dist, -1.0

    # 4. Time check <= 48h
    if new_timestamp is None:
        new_timestamp = datetime.utcnow()

    created_at = existing_ticket.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            created_at = datetime.utcnow()
    elif not isinstance(created_at, datetime):
        created_at = datetime.utcnow()

    # Normalize tz
    if created_at.tzinfo is not None and new_timestamp.tzinfo is None:
        created_at = created_at.replace(tzinfo=None)
    elif new_timestamp.tzinfo is not None and created_at.tzinfo is None:
        new_timestamp = new_timestamp.replace(tzinfo=None)

    time_diff_hours = abs((new_timestamp - created_at).total_seconds()) / 3600.0
    if time_diff_hours > DUPLICATE_TIME_THRESHOLD_HOURS:
        return False, dist, time_diff_hours

    return True, dist, time_diff_hours

def escalate_urgency(current_urgency: str, current_count: int) -> str:
    """
    Escalates ticket urgency when multiple citizen complaints merge:
    - 1-2 duplicates: maintain or elevate to Medium
    - 3+ duplicates: elevate to High urgency
    """
    if current_count >= 3:
        return "High"
    if current_urgency == "Low" and current_count >= 1:
        return "Medium"
    return current_urgency
