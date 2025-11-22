from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.config.database import get_database

from src.app.models.loket import Loket
from src.app.models.ticket import Ticket

from src.app.schema.ticket import TicketCreateResponse, NextTicketResponse
from src.app.schema.loket import LoketInfo

router = APIRouter(tags=["tickets"])


@router.post(
    "/events/{event_id}/lokets/{loket_id}/tickets",
    response_model=TicketCreateResponse,
)
async def create_ticket(
    event_id: int,
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Loket).where(
            Loket.id == loket_id,
            Loket.event_id == event_id,
        )
    )
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    new_number = (loket.last_ticket_number or 0) + 1
    loket.last_ticket_number = new_number

    ticket = Ticket(
        event_id=event_id,
        loket_id=loket_id,
        number=new_number,
        status="waiting",
    )

    db.add(ticket)
    db.add(loket)
    await db.commit()
    await db.refresh(ticket)
    await db.refresh(loket)

    return TicketCreateResponse(
        ticket_id=ticket.id,
        loket_id=loket.id,
        loket_name=loket.name,
        loket_code=loket.code,
        event_id=event_id,
        number=ticket.number,
    )


@router.post("/lokets/{loket_id}/next", response_model=NextTicketResponse)
async def next_ticket(
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Loket).where(Loket.id == loket_id)
    )
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    result_ticket = await db.execute(
        select(Ticket)
        .where(
            Ticket.loket_id == loket_id,
            Ticket.status == "waiting",
        )
        .order_by(Ticket.created_at.asc())
        .limit(1)
    )
    ticket = result_ticket.scalar_one_or_none()

    if not ticket:
        return NextTicketResponse(
            loket_id=loket.id,
            loket_code=loket.code,
            called_number=None,
            message="Tidak ada antrian.",
        )

    ticket.status = "called"
    ticket.called_at = datetime.utcnow()
    loket.current_number = ticket.number

    db.add(ticket)
    db.add(loket)
    await db.commit()
    await db.refresh(ticket)
    await db.refresh(loket)

    return NextTicketResponse(
        loket_id=loket.id,
        loket_code=loket.code,
        called_number=ticket.number,
        message="Memanggil nomor antrian.",
    )


@router.get("/lokets/{loket_id}/info", response_model=LoketInfo)
async def loket_info(
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    # ambil loket
    result = await db.execute(
        select(Loket).where(Loket.id == loket_id)
    )
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    # hitung tiket waiting
    result_count = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.loket_id == loket_id,
            Ticket.status == "waiting",
        )
    )
    waiting_count = result_count.scalar_one() or 0

    return LoketInfo(
        loket_id=loket.id,
        loket_name=loket.name,
        loket_code=loket.code,
        current_number=loket.current_number,
        queue_length=waiting_count,
        last_repeat_at=loket.last_repeat_at,
    )


@router.post("/lokets/{loket_id}/repeat")
async def repeat_call(
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(select(Loket).where(Loket.id == loket_id))
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    # update waktu repeat
    loket.last_repeat_at = datetime.utcnow()
    db.add(loket)
    await db.commit()
    await db.refresh(loket)

    return {
      "message": "Repeat requested",
      "loket_name": loket.name,
      "loket_code": loket.code,
      "current_number": loket.current_number,
      "last_repeat_at": loket.last_repeat_at,
    }
