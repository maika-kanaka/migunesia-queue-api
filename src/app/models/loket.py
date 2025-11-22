from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Loket(Base):
    __tablename__ = "lokets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False)

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # nomor terakhir yang dipanggil di layar
    current_number = Column(Integer, default=0)
    # nomor tiket terakhir yang diterbitkan untuk loket ini
    last_ticket_number = Column(Integer, default=0)

    last_repeat_at = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="lokets")
    tickets = relationship(
        "Ticket", back_populates="loket", cascade="all, delete-orphan"
    )
