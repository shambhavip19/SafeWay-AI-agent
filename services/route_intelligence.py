import httpx
import logging
import json
from typing import List, Dict, Any, Tuple
from services.geocoding import get_coordinates
from services.emergency_services import haversine_distance

logger = logging.getLogger(__name__)

def fetch_osrm_routes(origin_coords: Tuple[float, float], dest_coords: Tuple[float, float]) -> List[Dict[str, Any]]:
    """
    Fetch routing geometry from the public Open Source Routing Machine (OSRM) API.
    Returns a list of routes with coordinates.
    """
    origin_lat, origin_lon = origin_coords
    dest_lat, dest_lon = dest_coords
    
    # OSRM expects coordinates in lon,lat format
    url = f"http://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson&alternatives=true"
    
    try:
        logger.info(f"Calling OSRM API from ({origin_lat}, {origin_lon}) to ({dest_lat}, {dest_lon})")
        response = httpx.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("routes", [])
        else:
            logger.error(f"OSRM API returned status code {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling OSRM API: {e}")
        return []

def divide_route_into_segments(coordinates: List[List[float]], num_segments: int = 5) -> List[Dict[str, Any]]:
    """
    Divide a list of coordinates [[lon, lat], ...] into N equal-sized segments.
    Computes a midpoint and representative coordinate for each segment.
    """
    if not coordinates or len(coordinates) < 2:
        return []
        
    num_coords = len(coordinates)
    chunk_size = max(1, num_coords // num_segments)
    
    segments = []
    for i in range(num_segments):
        start_idx = i * chunk_size
        # For the last segment, take all remaining coordinates
        end_idx = num_coords if i == num_segments - 1 else (i + 1) * chunk_size + 1
        
        # Ensure we don't go out of bounds or create empty segments
        if start_idx >= num_coords - 1:
            break
            
        segment_coords = coordinates[start_idx:end_idx]
        if not segment_coords:
            continue
            
        # Midpoint index
        mid_idx = len(segment_coords) // 2
        mid_lon, mid_lat = segment_coords[mid_idx]
        
        segments.append({
            "segment_index": i,
            "coordinates": segment_coords,
            "midpoint": {"latitude": mid_lat, "longitude": mid_lon},
            "start_point": {"latitude": segment_coords[0][1], "longitude": segment_coords[0][0]},
            "end_point": {"latitude": segment_coords[-1][1], "longitude": segment_coords[-1][0]}
        })
        
    return segments

def analyze_route_safety(
    origin: str, 
    destination: str, 
    event_time: Any,
    db_session: Any
) -> Dict[str, Any]:
    """
    Main orchestrator for route safety. Geocodes locations, fetches routes, 
    segments routes, scores each segment, and returns safety profiles.
    """
    # 1. Resolve coordinates
    origin_data = get_coordinates(origin)
    dest_data = get_coordinates(destination)
    
    if not origin_data or not dest_data:
        return {
            "success": False,
            "error": "Could not resolve origin or destination coordinates"
        }
        
    origin_coords = (origin_data["latitude"], origin_data["longitude"])
    dest_coords = (dest_data["latitude"], dest_data["longitude"])
    
    # Import safety calculations here to avoid circular imports
    from services.safety_engine import evaluate_location_safety
    
    # 2. Fetch routes from OSRM
    routes = fetch_osrm_routes(origin_coords, dest_coords)
    
    if not routes:
        # Fallback to direct line segment if OSRM is down
        fallback_coordinates = [
            [origin_coords[1], origin_coords[0]],
            [dest_coords[1], dest_coords[0]]
        ]
        routes = [{"geometry": {"coordinates": fallback_coordinates, "type": "LineString"}, "distance": 0, "duration": 0}]
        
    # We will score the primary route (index 0) and alternatives (index 1+)
    analyzed_routes = []
    
    for idx, route in enumerate(routes):
        geometry = route.get("geometry", {})
        coords = geometry.get("coordinates", [])
        
        if not coords:
            continue
            
        # Divide into segments
        segments = divide_route_into_segments(coords, num_segments=5)
        
        route_safety_scores = []
        scored_segments = []
        threats_detected = []
        
        for seg in segments:
            mid = seg["midpoint"]
            # Evaluate safety at the midpoint of this segment
            seg_safety = evaluate_location_safety(
                latitude=mid["latitude"],
                longitude=mid["longitude"],
                event_time=event_time,
                db=db_session
            )
            
            seg_score = seg_safety["score"]
            route_safety_scores.append(seg_score)
            
            # Identify threats on this segment
            seg_threats = seg_safety.get("threats", [])
            for t in seg_threats:
                threat_with_seg = f"Segment {seg['segment_index'] + 1}: {t}"
                if threat_with_seg not in threats_detected:
                    threats_detected.append(threat_with_seg)
            
            scored_segments.append({
                "segment_index": seg["segment_index"],
                "coordinates": seg["coordinates"],
                "safety_score": seg_score,
                "risk_level": seg_safety["risk_level"],
                "threats": seg_threats,
                "midpoint": seg["midpoint"]
            })
            
        # Overall route safety score is the average of segment scores
        overall_score = round(sum(route_safety_scores) / len(route_safety_scores), 1) if route_safety_scores else 5.0
        
        # Risk level determination
        if overall_score >= 7.5:
            risk_level = "Low"
        elif overall_score >= 4.5:
            risk_level = "Medium"
        else:
            risk_level = "High"
            
        analyzed_routes.append({
            "route_index": idx,
            "overall_score": overall_score,
            "risk_level": risk_level,
            "geometry": geometry,
            "segments": scored_segments,
            "threats": threats_detected,
            "distance_meters": route.get("distance", 0),
            "duration_seconds": route.get("duration", 0),
        })
        
    # Sort analyzed routes by route index
    primary_route = analyzed_routes[0]
    alternative_route = analyzed_routes[1] if len(analyzed_routes) > 1 else None
    
    # Highlight safer alternatives
    safer_alternative_found = False
    recommendation_message = ""
    
    if alternative_route:
        score_diff = alternative_route["overall_score"] - primary_route["overall_score"]
        # If alternative is safer by 0.5 points or more, suggest it!
        if score_diff >= 0.5:
            safer_alternative_found = True
            recommendation_message = f"Alternative route is safer (Score: {alternative_route['overall_score']}/10) compared to the primary route (Score: {primary_route['overall_score']}/10)."
        else:
            recommendation_message = "Primary route is currently the safest option."
    else:
        recommendation_message = "No alternative routes found."

    return {
        "success": True,
        "origin_coords": {"latitude": origin_coords[0], "longitude": origin_coords[1]},
        "destination_coords": {"latitude": dest_coords[0], "longitude": dest_coords[1]},
        "primary_route": primary_route,
        "alternative_route": alternative_route,
        "safer_alternative_found": safer_alternative_found,
        "alternative_recommendation": recommendation_message
    }
