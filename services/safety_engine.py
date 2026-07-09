import logging
import math
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models import CommunityReport
from services.emergency_services import get_nearby_emergency_services, haversine_distance

logger = logging.getLogger(__name__)

def calculate_safety_score(event_time: datetime, police_count: int, hospital_count: int) -> Dict[str, Any]:
    """
    Simpler, backward-compatible helper for basic safety calculations.
    """
    # Base score
    score = 7.0
    threats = []

    # Time of day risk (10 PM to 4 AM is high risk)
    hour = event_time.hour
    if 22 <= hour or hour < 4:
        score -= 1.5
        threats.append("Unsafe late-night travel")
    elif 20 <= hour < 22 or 4 <= hour < 6:
        score -= 0.5

    # Emergency counts
    if police_count > 0:
        score += min(1.5, police_count * 0.75)
    else:
        score -= 1.0
        threats.append("Low police coverage")

    if hospital_count > 0:
        score += 0.5
    else:
        score -= 0.5
        threats.append("Limited emergency access")

    # Bound score between 0 and 10
    score = max(0.0, min(10.0, round(score, 1)))

    if score >= 7.5:
        risk_level = "Low"
    elif score >= 4.5:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "score": score,
        "risk_level": risk_level,
        "threats": threats
    }

def evaluate_location_safety(
    latitude: float,
    longitude: float,
    event_time: datetime,
    db: Session,
    radius_meters: float = 2000
) -> Dict[str, Any]:
    """
    A comprehensive geolocated safety scoring engine.
    Considers time, community reports (decayed by distance), and emergency services.
    Supports future-ready attributes (lighting, weather, crowd density placeholders).
    """
    base_score = 7.0
    threats = []
    
    # 1. Time of Day Penalty
    hour = event_time.hour
    time_penalty = 0.0
    if 22 <= hour or hour < 4:
        time_penalty = 1.5
        threats.append("Unsafe late-night travel")
    elif 20 <= hour < 22 or 4 <= hour < 6:
        time_penalty = 0.5
    base_score -= time_penalty

    # 2. Emergency Services Buffer
    emergency = get_nearby_emergency_services(latitude, longitude, radius_meters=2000)
    police_count = emergency["police_count"]
    hospital_count = emergency["hospital_count"]
    
    if police_count >= 2:
        base_score += 1.5
    elif police_count == 1:
        base_score += 0.75
    else:
        base_score -= 1.0
        threats.append("Low police coverage")
        
    if hospital_count >= 1:
        base_score += 0.5
    else:
        base_score -= 0.5
        threats.append("Limited emergency access")

    # 3. Community Reports Density Penalty
    # We construct a bounding box around (latitude, longitude) to run a fast indexed query
    # 1 deg lat = 111,000m. 1 deg lon = 111,000 * cos(lat)
    lat_delta = radius_meters / 111000.0
    rad_lat = math.radians(latitude)
    lon_delta = radius_meters / (111000.0 * abs(math.cos(rad_lat))) if abs(math.cos(rad_lat)) > 0.01 else 0.1
    
    nearby_reports = db.query(CommunityReport).filter(
        CommunityReport.latitude.between(latitude - lat_delta, latitude + lat_delta),
        CommunityReport.longitude.between(longitude - lon_delta, longitude + lon_delta)
    ).all()
    
    report_penalty = 0.0
    actual_reports_count = 0
    poor_lighting_reported = False
    
    for report in nearby_reports:
        dist = haversine_distance(latitude, longitude, report.latitude, report.longitude)
        if dist <= radius_meters:
            actual_reports_count += 1
            # Weight decays by distance (closer reports have higher impact)
            distance_weight = 1.0 / (1.0 + (dist / 500.0))
            
            # Severity weighting by report category
            severity = 0.5
            rtype = report.report_type.strip().lower()
            if rtype == "harassment":
                severity = 2.0
            elif rtype in ["theft", "unsafe area"]:
                severity = 1.5
            elif rtype == "poor lighting":
                severity = 1.0
                poor_lighting_reported = True
            elif rtype == "suspicious activity":
                severity = 1.0
            elif rtype == "road blockage":
                severity = 0.5
                
            report_penalty += severity * distance_weight
            
    # Cap total report penalty
    report_penalty = min(4.5, report_penalty)
    base_score -= report_penalty
    
    if report_penalty >= 1.5:
        threats.append("High report density")
    if poor_lighting_reported:
        threats.append("Poor lighting indicators")

    # 4. Future-Ready Architecture Placeholders
    # These represent default variables that could be connected to weather or iot APIs
    lighting_condition = "Dim" if (hour >= 18 or hour < 6) and poor_lighting_reported else "Well-lit"
    crowd_density = "Sparse" if (22 <= hour or hour < 5) else "Moderate"
    weather_condition = "Clear"
    
    # Apply minor adjustments
    if lighting_condition == "Dim":
        base_score -= 0.3
    if crowd_density == "Sparse":
        base_score -= 0.2
        
    # Bound final score
    final_score = max(0.0, min(10.0, round(base_score, 1)))
    
    if final_score >= 7.5:
        risk_level = "Low"
    elif final_score >= 4.5:
        risk_level = "Medium"
    else:
        risk_level = "High"
        
    return {
        "score": final_score,
        "risk_level": risk_level,
        "threats": threats,
        "police_count": police_count,
        "hospital_count": hospital_count,
        "reports_count": actual_reports_count,
        "nearby_resources": emergency["resources"][:5],  # Closest 5 emergency services
        "environment": {
            "lighting": lighting_condition,
            "crowd_density": crowd_density,
            "weather": weather_condition
        }
    }
