"""
Ward routing module for Jan-Vani.
Maps citizen GPS coordinates (latitude, longitude) to the corresponding
Nagpur Municipal Corporation (NMC) administrative ward polygon.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

GEOJSON_PATH = Path(__file__).parent.parent / "data" / "sample" / "nagpur_wards.geojson"

def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    """
    Ray-casting algorithm to test whether point (lon, lat) lies inside polygon.
    polygon is a list of [lon, lat] vertices.
    """
    x, y = point
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two points in meters using Haversine formula.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class WardRouter:
    def __init__(self, geojson_path: Path = GEOJSON_PATH):
        self.wards = []
        self._load_wards(geojson_path)

    def _load_wards(self, path: Path):
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [[]])[0]
                # calculate centroid
                avg_lon = sum(c[0] for c in coords) / len(coords)
                avg_lat = sum(c[1] for c in coords) / len(coords)
                self.wards.append({
                    "ward_id": props.get("ward_id"),
                    "ward_name": props.get("ward_name"),
                    "zone": props.get("zone"),
                    "officer_email": props.get("officer_email"),
                    "polygon": coords,
                    "centroid": (avg_lat, avg_lon)
                })

    def find_ward(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Returns the matching ward dictionary for a given (lat, lon).
        Falls back to closest ward centroid if slightly outside borders.
        """
        # Exact point-in-polygon check
        for ward in self.wards:
            if point_in_polygon((lon, lat), ward["polygon"]):
                return {
                    "ward_id": ward["ward_id"],
                    "ward_name": ward["ward_name"],
                    "zone": ward["zone"],
                    "officer_email": ward["officer_email"],
                    "matched_by": "polygon_containment"
                }

        # Fallback to closest centroid if nearby
        closest_ward = None
        min_dist = float("inf")
        for ward in self.wards:
            c_lat, c_lon = ward["centroid"]
            dist = haversine_distance_meters(lat, lon, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist
                closest_ward = ward

        if closest_ward and min_dist < 20000:  # within 20km
            return {
                "ward_id": closest_ward["ward_id"],
                "ward_name": closest_ward["ward_name"],
                "zone": closest_ward["zone"],
                "officer_email": closest_ward["officer_email"],
                "matched_by": "nearest_centroid",
                "distance_to_centroid_meters": round(min_dist, 1)
            }

        return {
            "ward_id": "WARD-02",
            "ward_name": "Dharampeth (Default)",
            "zone": 2,
            "officer_email": "officer.dharampeth@nmc.gov.in",
            "matched_by": "default_fallback"
        }

# Global singleton
ward_router = WardRouter()
