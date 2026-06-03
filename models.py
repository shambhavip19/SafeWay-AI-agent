from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)

    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)

    latitude = Column(Float)
    longitude = Column(Float)

    safety_score = Column(Float, default=0)

    risk_level = Column(String, default="Unknown")

    event_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)