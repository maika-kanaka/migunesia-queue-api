from pydantic import BaseModel

class SoundSourceConfig(BaseModel):
    event_id: int
    role: str        # "multi_display" | "loket_display" | ...
    enabled: bool

class SoundConfigUpdate(BaseModel):
    multi_display: bool
    loket_display: bool
    loket_display_led: bool
    loket_admin: bool

class SoundConfigAll(BaseModel):
    event_id: int
    multi_display: bool
    loket_display: bool
    loket_display_led: bool
    loket_admin: bool

