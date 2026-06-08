from pydantic import BaseModel
from datetime import datetime


class AnalysisCreate(BaseModel):
    origin: str
    destination: str
    event_time: datetime


class AnalysisResponse(BaseModel):
    id: int
    origin: str
    destination: str
    safety_score: float | None = None
    risk_level: str | None = None

    class Config:
        from_attributes = True

class CommunityReportCreate(BaseModel):
    location: str
    report_type: str
    description: str | None = None