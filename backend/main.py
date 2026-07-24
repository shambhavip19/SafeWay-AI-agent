from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging
import json
import math
from typing import List, Dict, Any, Optional

from database import get_db
from models import Analysis, CommunityReport, EmergencyResource, RouteAnalysis
from schemas import (
    AnalysisCreate, AnalysisResponse,
    CommunityReportCreate, CommunityReportResponse,
    EmergencyResourceCreate, EmergencyResourceResponse,
    RouteAnalysisCreate, RouteAnalysisResponse
)
from services.geocoding import get_coordinates
from services.emergency_services import get_nearby_emergency_services
from services.safety_engine import evaluate_location_safety, calculate_safety_score
from services.ai_recommendation import generate_recommendation
from services.route_intelligence import analyze_route_safety
from fastapi.middleware.cors import CORSMiddleware

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafeWay API",
    description="AI-powered travel safety assistant backend",
    version="1.0.0"
)

# CORS middleware for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "SafeWay backend is running",
        "docs_url": "/docs"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }


# --- SAFETY ANALYSIS ENDPOINTS ---

@app.post("/analysis", response_model=Dict[str, Any])
@app.post("/api/analysis", response_model=Dict[str, Any])
def create_analysis(
    analysis: AnalysisCreate,
    db: Session = Depends(get_db)
):
    """
    Perform travel safety analysis for a destination location.
    Converts name to coordinates, analyzes emergency services and reports,
    generates safety score, and writes results to database.
    """
    logger.info(f"Received safety analysis request for destination: {analysis.destination}")
    
    # 1. Geocode Destination
    coords = get_coordinates(analysis.destination)
    if not coords:
        raise HTTPException(
            status_code=400,
            detail=f"Could not resolve the destination location '{analysis.destination}'. Try a more specific place name such as 'Baner, Pune' or 'Shivajinagar, Pune'."
        )
    
    # 2. Evaluate Safety using Scoring Engine
    safety_details = evaluate_location_safety(
        latitude=coords["latitude"],
        longitude=coords["longitude"],
        event_time=analysis.event_time,
        db=db
    )
    
    # 3. Generate Personalization recommendation
    recommendation = generate_recommendation(
        score=safety_details["score"],
        risk_level=safety_details["risk_level"],
        threats=safety_details["threats"],
        emergency_resources=safety_details["nearby_resources"],
        origin=analysis.origin,
        destination=analysis.destination
    )
    
    # 4. Save to Database
    new_analysis = Analysis(
        origin=analysis.origin,
        destination=analysis.destination,
        latitude=coords["latitude"],
        longitude=coords["longitude"],
        safety_score=safety_details["score"],
        risk_level=safety_details["risk_level"],
        recommendation=recommendation,
        event_time=analysis.event_time
    )
    
    try:
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed for Analysis: {e}")
        raise HTTPException(status_code=500, detail="Database write failure")
        
    return {
        "id": new_analysis.id,
        "origin": new_analysis.origin,
        "destination": new_analysis.destination,
        "latitude": new_analysis.latitude,
        "longitude": new_analysis.longitude,
        "safety_score": new_analysis.safety_score,
        "risk_level": new_analysis.risk_level,
        "police_count": safety_details["police_count"],
        "hospital_count": safety_details["hospital_count"],
        "reports_count": safety_details["reports_count"],
        "threats": safety_details["threats"],
        "environment": safety_details["environment"],
        "nearby_resources": safety_details["nearby_resources"],
        "recommendation": recommendation,
        "message": "Analysis created successfully"
    }


# --- ROUTE SAFETY ANALYSIS ENDPOINTS ---

@app.post("/api/route", response_model=Dict[str, Any])
@app.post("/route", response_model=Dict[str, Any])
def create_route_analysis(
    route_in: RouteAnalysisCreate,
    db: Session = Depends(get_db)
):
    """
    Analyze safety along a route between origin and destination.
    Uses OSRM to generate the route geometry, splits it into segments,
    and runs the safety calculations segment-by-segment.
    """
    logger.info(f"Received route safety request from {route_in.origin} to {route_in.destination}")
    
    route_safety = analyze_route_safety(
        origin=route_in.origin,
        destination=route_in.destination,
        event_time=route_in.event_time,
        db_session=db
    )
    
    if not route_safety.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=route_safety.get("error", "Route analysis failed. Try using a more specific origin and destination such as 'Baner, Pune' to 'Shivajinagar, Pune'.")
        )

    # Prepare DB Record for route analysis
    primary_route = route_safety["primary_route"]
    alternative_route = route_safety.get("alternative_route")
    
    new_route_analysis = RouteAnalysis(
        origin=route_in.origin,
        destination=route_in.destination,
        safety_score=primary_route["overall_score"],
        risk_level=primary_route["risk_level"],
        route_geometry=json.dumps(primary_route["geometry"]),
        risk_segments=json.dumps(primary_route["segments"]),
        alternative_route_geometry=json.dumps(alternative_route["geometry"]) if alternative_route else None
    )

    try:
        db.add(new_route_analysis)
        db.commit()
        db.refresh(new_route_analysis)
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed for RouteAnalysis: {e}")
        # Continue and return the route info even if DB write fails
        pass

    # Call recommendation engine for the route
    recommendation = generate_recommendation(
        score=primary_route["overall_score"],
        risk_level=primary_route["risk_level"],
        threats=primary_route["threats"],
        emergency_resources=primary_route["segments"][0]["threats"] if primary_route["segments"] else [],
        origin=route_in.origin,
        destination=route_in.destination,
        alternative_recommendation=route_safety.get("alternative_recommendation")
    )

    return {
        "id": new_route_analysis.id if new_route_analysis.id else None,
        "origin": route_in.origin,
        "destination": route_in.destination,
        "origin_coords": route_safety["origin_coords"],
        "destination_coords": route_safety["destination_coords"],
        "primary_route": primary_route,
        "alternative_route": alternative_route,
        "safer_alternative_found": route_safety["safer_alternative_found"],
        "recommendation": recommendation
    }


# --- COMMUNITY REPORTS ENDPOINTS ---

@app.post("/report", response_model=Dict[str, Any])
@app.post("/api/reports", response_model=Dict[str, Any])
def create_report(
    report: CommunityReportCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a community safety report (Harassment, Theft, Poor Lighting, etc.).
    Saves coordinate information for proximity scoring.
    """
    logger.info(f"Received community report at: {report.location} ({report.report_type})")
    
    new_report = CommunityReport(
        location=report.location,
        latitude=report.latitude,
        longitude=report.longitude,
        report_type=report.report_type,
        description=report.description
    )

    try:
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit community report: {e}")
        raise HTTPException(status_code=500, detail="Database write failure")

    return {
        "id": new_report.id,
        "message": "Report submitted successfully",
        "report": {
            "id": new_report.id,
            "location": new_report.location,
            "latitude": new_report.latitude,
            "longitude": new_report.longitude,
            "report_type": new_report.report_type,
            "description": new_report.description,
            "created_at": new_report.created_at
        }
    }


@app.get("/api/reports", response_model=List[CommunityReportResponse])
def get_reports(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: Optional[float] = Query(3000, description="Radius in meters"),
    db: Session = Depends(get_db)
):
    """
    List community safety reports. Can optionally filter reports
    lying within a coordinate radius buffer.
    """
    if lat is not None and lon is not None:
        # Construct bounding box filter
        lat_delta = radius / 111000.0
        rad_lat = math.radians(lat) if hasattr(math, "radians") else 0.0
        lon_delta = radius / (111000.0 * abs(math.cos(rad_lat))) if abs(math.cos(rad_lat)) > 0.01 else 0.1
        
        raw_reports = db.query(CommunityReport).filter(
            CommunityReport.latitude.between(lat - lat_delta, lat + lat_delta),
            CommunityReport.longitude.between(lon - lon_delta, lon + lon_delta)
        ).all()
        
        filtered_reports = []
        from services.emergency_services import haversine_distance
        for rep in raw_reports:
            if haversine_distance(lat, lon, rep.latitude, rep.longitude) <= radius:
                filtered_reports.append(rep)
        return filtered_reports
        
    return db.query(CommunityReport).order_by(CommunityReport.created_at.desc()).limit(50).all()


# --- EMERGENCY RESOURCES ENDPOINTS ---

@app.get("/api/emergency", response_model=Dict[str, Any])
def get_emergency_resources(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(3000, description="Radius in meters"),
    db: Session = Depends(get_db)
):
    """
    Find nearby emergency facilities (hospitals, police stations).
    """
    try:
        emergency = get_nearby_emergency_services(lat, lon, radius_meters=radius)
        return emergency
    except Exception as e:
        logger.error(f"Error resolving emergency services: {e}")
        raise HTTPException(status_code=500, detail="Error fetching emergency services")


# --- ADMIN ANALYTICS DASHBOARD ---

@app.get("/api/analytics", response_model=Dict[str, Any])
def get_analytics(db: Session = Depends(get_db)):
    """
    Fetch consolidated analytics metrics for the SafeWay admin dashboard.
    """
    # 1. Total count of reports
    total_reports = db.query(CommunityReport).count()
    
    # 2. Daily analyses performed
    # SQLite uses strftime or date, Postgres uses date. Standard Python/SQL group by
    analyses = db.query(Analysis.created_at).all()
    daily_counts = {}
    for a in analyses:
        date_str = a.created_at.strftime("%Y-%m-%d")
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    daily_analyses = [{"date": k, "count": v} for k, v in sorted(daily_counts.items())]

    # 3. Most common reports categories
    categories = db.query(
        CommunityReport.report_type, 
        func.count(CommunityReport.id)
    ).group_by(CommunityReport.report_type).all()
    
    report_categories = [{"category": cat, "count": count} for cat, count in categories]

    # 4. Safety Score distribution
    all_scores = [round(a.safety_score) for a in db.query(Analysis.safety_score).all()]
    score_buckets = {i: 0 for i in range(11)}
    for s in all_scores:
        val = int(s)
        if 0 <= val <= 10:
            score_buckets[val] += 1
            
    safety_distribution = [{"score": k, "count": v} for k, v in score_buckets.items()]

    # 5. Hotspot Locations
    hotspots_query = db.query(
        CommunityReport.location, 
        func.count(CommunityReport.id)
    ).group_by(CommunityReport.location).order_by(func.count(CommunityReport.id).desc()).limit(5).all()
    
    hotspots = [{"location": loc, "count": count} for loc, count in hotspots_query]

    # 6. Common Threats Detected in analyses
    analyses_records = db.query(Analysis.recommendation).all()
    threat_counts = {
        "Unsafe late-night travel": 0,
        "Low police coverage": 0,
        "Limited emergency access": 0,
        "High report density": 0,
        "Poor lighting indicators": 0
    }
    
    for record in analyses_records:
        rec = record.recommendation or ""
        for threat in threat_counts.keys():
            if threat.lower() in rec.lower():
                threat_counts[threat] += 1
                
    common_threats = [{"threat": k, "count": v} for k, v in threat_counts.items()]

    return {
        "total_reports": total_reports,
        "daily_analyses": daily_analyses,
        "report_categories": report_categories,
        "safety_score_distribution": safety_distribution,
        "hotspot_locations": hotspots,
        "common_threats": common_threats
    }