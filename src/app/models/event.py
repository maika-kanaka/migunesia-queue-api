from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    lokets = relationship("Loket", back_populates="event")
    tickets = relationship("Ticket", back_populates="event")
    sound_sources = relationship("SoundSource", back_populates="event")
