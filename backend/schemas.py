from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Dict, Any, Optional


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# Analysis schemas
class AnalysisCreate(BaseModel):
    origin: str
    destination: str
    event_time: datetime


class AnalysisResponse(BaseModel):
    id: int
    origin: str
    destination: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    safety_score: float
    risk_level: str
    recommendation: Optional[str] = None
    event_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Community Report schemas
class CommunityReportCreate(BaseModel):
    location: str
    latitude: float
    longitude: float
    report_type: str
    description: Optional[str] = None


class CommunityReportResponse(BaseModel):
    id: int
    location: str
    latitude: float
    longitude: float
    report_type: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Emergency Resource schemas
class EmergencyResourceCreate(BaseModel):
    name: str
    resource_type: str  # Police Station, Hospital, Emergency Services
    latitude: float
    longitude: float
    address: Optional[str] = None
    contact_info: Optional[str] = None


class EmergencyResourceResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    contact_info: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Route Analysis schemas
class RouteAnalysisCreate(BaseModel):
    origin: str
    destination: str
    event_time: datetime


class RouteAnalysisResponse(BaseModel):
    id: int
    origin: str
    destination: str
    safety_score: float
    risk_level: str
    route_geometry: Optional[str] = None  # GeoJSON string
    risk_segments: Optional[str] = None   # JSON string list
    alternative_route_geometry: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Saved Route schemas
class SavedRouteCreate(BaseModel):
    name: str
    origin: str
    destination: str
    route_geometry: str


class SavedRouteResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    origin: str
    destination: str
    route_geometry: str
    created_at: datetime

    class Config:
        from_attributes = True