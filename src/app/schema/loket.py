from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoketCreate(BaseModel):
    name: str
    code: str


class LoketUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class LoketRead(BaseModel):
    id: int
    name: str
    code: str
    event_id: int
    current_number: int
    last_ticket_number: int

    class Config:
        from_attributes = True


class LoketState(BaseModel):
    loket_id: int
    loket_code: str
    loket_name: str
    current_number: int
    queue_length: int
    last_ticket_number: int
    last_repeat_at: Optional[datetime] = None


class LoketInfo(BaseModel):
    loket_id: int
    loket_name: str
    loket_code: str
    current_number: Optional[int]
    queue_length: int
    last_repeat_at: Optional[datetime] = None

    class Config:
        from_attributes = True
