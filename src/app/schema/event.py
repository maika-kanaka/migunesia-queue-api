from pydantic import BaseModel
from typing import Optional


class EventCreate(BaseModel):
    name: str
    code: str


class EventUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class EventRead(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    class Config:
        from_attributes = True
