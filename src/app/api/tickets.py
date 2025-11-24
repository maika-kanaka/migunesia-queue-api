from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

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
        select(Loket)
        .options(selectinload(Loket.event))
        .where(
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
        loket_description=loket.description,
        loket_code=loket.code,
        event_id=event_id,
        event_name=loket.event.name,
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

    # ambil tiket waiting paling kecil nomornya
    result_ticket = await db.execute(
        select(Ticket)
        .where(
            Ticket.loket_id == loket_id,
            Ticket.status == "waiting",
        )
        .order_by(Ticket.number)
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
    ticket.called_at = datetime.now(timezone.utc)
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

    # ambil nomor tiket yang statusnya HOLD
    result_hold = await db.execute(
        select(Ticket.number)
        .where(
            Ticket.loket_id == loket_id,
            Ticket.status == "hold",
        )
        .order_by(Ticket.number)
    )
    hold_numbers = [row[0] for row in result_hold.all()]

    return LoketInfo(
        loket_id=loket.id,
        loket_name=loket.name,
        loket_code=loket.code,
        loket_description=loket.description,
        current_number=loket.current_number,
        queue_length=waiting_count,
        last_ticket_number=loket.last_ticket_number or 0,
        last_repeat_at=loket.last_repeat_at,
        hold_numbers=hold_numbers,
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
    loket.last_repeat_at = datetime.now(timezone.utc)
    db.add(loket)
    await db.commit()
    await db.refresh(loket)

    return {
      "message": "Repeat requested",
      "loket_name": loket.name,
      "loket_description": loket.description,
      "loket_code": loket.code,
      "current_number": loket.current_number,
      "last_repeat_at": loket.last_repeat_at,
    }


@router.post("/lokets/{loket_id}/hold")
async def hold_current_ticket(
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    # ambil loket
    result = await db.execute(select(Loket).where(Loket.id == loket_id))
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    if not loket.current_number:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada nomor aktif untuk di-hold",
        )

    # cari tiket dengan nomor = current_number
    result_ticket = await db.execute(
        select(Ticket).where(
            Ticket.loket_id == loket_id,
            Ticket.number == loket.current_number,
        )
    )
    ticket = result_ticket.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket untuk nomor saat ini tidak ditemukan",
        )

    # opsional: validasi status sebelumnya
    if ticket.status not in ("waiting", "called"):
        raise HTTPException(
            status_code=400,
            detail=f"Tidak dapat hold ticket dengan status {ticket.status}",
        )

    # set status hold & kosongkan current_number di loket
    ticket.status = "hold"
    loket.current_number = None

    db.add_all([ticket, loket])
    await db.commit()
    await db.refresh(loket)
    await db.refresh(ticket)

    return {
        "message": "Ticket di-hold",
        "hold_number": ticket.number,
        "loket_id": loket.id,
        "loket_code": loket.code,
    }


@router.post("/lokets/{loket_id}/hold/{number}/call")
async def call_held_ticket(
    loket_id: int,
    number: int,
    db: AsyncSession = Depends(get_database),
):
    # Ambil loket
    result_loket = await db.execute(select(Loket).where(Loket.id == loket_id))
    loket = result_loket.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    # Ambil ticket yang di-HOLD
    result_ticket = await db.execute(
        select(Ticket).where(
            Ticket.loket_id == loket_id,
            Ticket.number == number,
            Ticket.status == "hold",
        )
    )
    ticket = result_ticket.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket HOLD tidak ditemukan untuk nomor tersebut",
        )

    # (Opsional) kalau masih ada current_number aktif,
    # bisa kamu putuskan mau diapakan:
    # - Di-set DONE, atau
    # - Tetap dibiarkan (ganti saja ke nomor HOLD).
    # Di sini kita langsung ganti current_number ke nomor HOLD.
    loket.current_number = ticket.number
    ticket.status = "called"

    db.add_all([loket, ticket])
    await db.commit()
    await db.refresh(ticket)

    return {
        "loket_id": loket.id,
        "loket_code": loket.code,
        "called_number": ticket.number,
        "message": "Ticket HOLD dipanggil kembali",
    }

