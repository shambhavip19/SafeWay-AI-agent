from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Integer, default=1)  # 1 for True, 0 for False (SQLite compatible)
    created_at = Column(DateTime, default=datetime.utcnow)

    saved_routes = relationship("SavedRoute", back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    safety_score = Column(Float, default=0.0)
    risk_level = Column(String, default="Unknown")
    recommendation = Column(Text)
    event_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    report_type = Column(String, nullable=False)  # Harassment, Poor Lighting, Unsafe Area, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmergencyResource(Base):
    __tablename__ = "emergency_resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)  # Police Station, Hospital, Emergency Services
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String)
    contact_info = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class RouteAnalysis(Base):
    __tablename__ = "route_analyses"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    safety_score = Column(Float, default=0.0)
    risk_level = Column(String, default="Unknown")
    route_geometry = Column(Text)  # GeoJSON string of the coordinates
    risk_segments = Column(Text)   # JSON string describing segments & their risk levels
    alternative_route_geometry = Column(Text)  # GeoJSON string of alternative route
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedRoute(Base):
    __tablename__ = "saved_routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    route_geometry = Column(Text)  # GeoJSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_routes")