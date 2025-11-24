from pydantic import BaseModel
from typing import Optional


class TicketRead(BaseModel):
    id: int
    event_id: int
    loket_id: int
    number: int
    status: str

    class Config:
        from_attributes = True


class TicketCreateResponse(BaseModel):
    ticket_id: int
    loket_id: int
    loket_name: str
    loket_description: Optional[str] = None
    loket_code: str
    event_id: int
    event_name: str
    number: int


class NextTicketResponse(BaseModel):
    loket_id: int
    loket_code: str
    called_number: Optional[int]
    message: str
