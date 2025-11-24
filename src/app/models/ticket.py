from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    loket_id = Column(Integer, ForeignKey("lokets.id"), nullable=False)

    number = Column(Integer, nullable=False)
    status = Column(String(20), default="waiting")  # waiting, called, hold, done
    created_at = Column(DateTime, default=func.now())
    called_at = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="tickets")
    loket = relationship("Loket", back_populates="tickets")
