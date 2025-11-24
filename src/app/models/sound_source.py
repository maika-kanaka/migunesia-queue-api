from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class SoundSource(Base):
    __tablename__ = "sound_sources"

    id = Column(Integer, primary_key=True, index=True)

    # event wajib, karena konfigurasi minimal per event
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # role halaman yang boleh jadi sumber suara
    # contoh: "multi_display", "loket_display", "loket_display_led", "loket_admin"
    role = Column(String(50), nullable=False)

    # aktif / tidak
    enabled = Column(Boolean, nullable=False, default=True)

    event = relationship("Event", back_populates="sound_sources")
