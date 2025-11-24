from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from src.config.database import get_database
from src.app.models.event import Event
from src.app.models.loket import Loket
from src.app.models.ticket import Ticket
from src.app.schema.loket import LoketCreate, LoketRead, LoketUpdate

router = APIRouter(prefix="/events/{event_id}/lokets", tags=["lokets"])


@router.post("", response_model=LoketRead, status_code=status.HTTP_201_CREATED)
async def create_loket(
    event_id: int,
    payload: LoketCreate,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    loket = Loket(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        event_id=event_id,
    )
    db.add(loket)
    await db.commit()
    await db.refresh(loket)
    return loket


@router.get("", response_model=List[LoketRead])
async def list_lokets(
    event_id: int, db: AsyncSession = Depends(get_database)
):
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
    return lokets


@router.get("/{loket_id}", response_model=LoketRead)
async def get_loket(
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
    return loket


@router.put("/{loket_id}", response_model=LoketRead)
async def update_loket(
    event_id: int,
    loket_id: int,
    payload: LoketUpdate,
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

    if payload.name is not None:
        loket.name = payload.name
    if payload.code is not None:
        loket.code = payload.code
    if payload.description is not None:
        loket.description = payload.description

    db.add(loket)
    await db.commit()
    await db.refresh(loket)
    return loket


@router.delete("/{loket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loket(
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

    # Cek apakah masih ada tiket waiting di loket ini
    result_waiting = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.loket_id == loket_id,
            Ticket.status == "waiting",
        )
    )
    waiting_count = result_waiting.scalar_one() or 0

    if waiting_count > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Tidak bisa menghapus loket yang masih memiliki tiket waiting. "
                "Silakan reset antrian terlebih dahulu."
            ),
        )

    await db.delete(loket)
    await db.commit()
    return


@router.post("/{loket_id}/reset")
async def reset_loket(
    event_id: int,
    loket_id: int,
    db: AsyncSession = Depends(get_database),
):
    """
    Reset semua antrian di loket ini:
    - Hapus semua tiket
    - Set current_number = 0
    - Set last_ticket_number = 0
    """
    result = await db.execute(
        select(Loket).where(
            Loket.id == loket_id,
            Loket.event_id == event_id,
        )
    )
    loket = result.scalar_one_or_none()
    if not loket:
        raise HTTPException(status_code=404, detail="Loket not found")

    # Hapus semua tiket di loket ini
    await db.execute(
        delete(Ticket).where(Ticket.loket_id == loket_id)
    )

    loket.current_number = 0
    loket.last_ticket_number = 0

    db.add(loket)
    await db.commit()
    await db.refresh(loket)

    return {"message": "Antrian di loket ini berhasil direset."}
