from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from services.geocoding import get_coordinates
from database import get_db
from models import Analysis
from schemas import AnalysisCreate
from services.safety_engine import calculate_safety_score 

app = FastAPI()


@app.get("/")
def home():
    return {"message": "SafeWay backend is running"}


@app.post("/analysis")
def create_analysis(
    analysis: AnalysisCreate,
    db: Session = Depends(get_db)
):
    coords = get_coordinates(analysis.destination)
    safety = calculate_safety_score(
    analysis.event_time
)

    new_analysis = Analysis(
    origin=analysis.origin,
    destination=analysis.destination,
    latitude=coords["latitude"] if coords else None,
    longitude=coords["longitude"] if coords else None,
    safety_score=safety["score"],
    risk_level=safety["risk_level"],
    event_time=analysis.event_time
    )

    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    return {
    "id": new_analysis.id,
    "safety_score": new_analysis.safety_score,
    "risk_level": new_analysis.risk_level,
    "message": "Analysis created successfully"
    }