from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.config.database import get_database
from src.app.models.event import Event
from src.app.models.loket import Loket
from src.app.models.ticket import Ticket
from src.app.schema.event import EventCreate, EventRead, EventUpdate
from src.app.schema.loket import LoketState

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_database),
):
    # cek event code unik
    result = await db.execute(
        select(Event).where(Event.code == payload.code)
    )
    exist = result.scalar_one_or_none()
    if exist:
        raise HTTPException(status_code=400, detail="Event code already exists")

    ev = Event(name=payload.name, code=payload.code)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.get("", response_model=List[EventRead])
async def list_events(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Event))
    events = result.scalars().all()
    return events


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@router.put("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    # kalau code mau diubah, cek unik
    if payload.code and payload.code != ev.code:
        result_code = await db.execute(
            select(Event).where(Event.code == payload.code)
        )
        exist = result_code.scalar_one_or_none()
        if exist:
            raise HTTPException(
                status_code=400,
                detail="Event code already exists",
            )

    # update hanya field yang dikirim
    if payload.name is not None:
        ev.name = payload.name
    if payload.code is not None:
        ev.code = payload.code
    if payload.is_active is not None:
        ev.is_active = payload.is_active

    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    # Cek apakah masih ada loket di event ini
    result_count = await db.execute(
        select(func.count(Loket.id)).where(Loket.event_id == event_id)
    )
    loket_count = result_count.scalar_one() or 0

    if loket_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Tidak bisa menghapus event yang masih memiliki loket. Hapus loket-loketnya terlebih dahulu.",
        )

    await db.delete(ev)
    await db.commit()
    return


@router.get("/{event_id}/state", response_model=List[LoketState])
async def event_state(event_id: int, db: AsyncSession = Depends(get_database)):
    result_event = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    ev = result_event.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    result_lokets = await db.execute(
        select(Loket).where(Loket.event_id == event_id)
    )
    lokets = result_lokets.scalars().all()

    states: List[LoketState] = []

    for loket in lokets:
        result_count = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.loket_id == loket.id,
                Ticket.status == "waiting",
            )
        )
        waiting_count = result_count.scalar_one() or 0

        # ambil nomor tiket yang statusnya HOLD
        result_hold = await db.execute(
            select(Ticket.number)
            .where(
                Ticket.loket_id == loket.id,
                Ticket.status == "hold",
            )
            .order_by(Ticket.number)
        )
        hold_numbers = [row[0] for row in result_hold.all()]

        states.append(
            LoketState(
                loket_id=loket.id,
                loket_code=loket.code,
                loket_name=loket.name,
                loket_description=loket.description,
                current_number=loket.current_number or 0,
                queue_length=waiting_count,
                last_ticket_number=loket.last_ticket_number or 0,
                last_repeat_at=loket.last_repeat_at,
                hold_numbers=hold_numbers,
            )
        )

    return states
