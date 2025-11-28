from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import csv
import io
from datetime import datetime

from src.config.database import get_database
from src.app.models.event import Event
from src.app.models.loket import Loket
from src.app.models.ticket import Ticket


router = APIRouter(tags=["export"])


# ============================================================
# Utility CSV functions
# ============================================================

def _rows_to_csv(headers: List[str], rows: List[List[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def _csv_response(filename: str, csv_str: str) -> StreamingResponse:
    return StreamingResponse(
        iter([csv_str]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


# ============================================================
# 1) EXPORT ALL EVENTS
# ============================================================

@router.get("/events/export")
async def export_events_csv(
    db: AsyncSession = Depends(get_database)
):
    result = await db.execute(select(Event))
    events: List[Event] = result.scalars().all()

    headers = ["id", "name", "code", "is_active"]

    rows = [
        [
            str(e.id),
            e.name,
            e.code,
            "1" if e.is_active else "0",
        ]
        for e in events
    ]

    csv_str = _rows_to_csv(headers, rows)
    filename = f"events-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return _csv_response(filename, csv_str)


# ============================================================
# 2) EXPORT LOKETS BY EVENT
# ============================================================

@router.get("/events/{event_id}/lokets/export")
async def export_lokets_csv(
    event_id: int,
    db: AsyncSession = Depends(get_database)
):
    result_event = await db.execute(select(Event).where(Event.id == event_id))
    event = result_event.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")

    result = await db.execute(select(Loket).where(Loket.event_id == event_id))
    lokets: List[Loket] = result.scalars().all()

    headers = [
        "id",
        "event_id",
        "name",
        "code",
        "current_number",
        "last_ticket_number",
        "last_repeat_at",
        "description",
    ]

    rows = []
    for l in lokets:
        rows.append([
            str(l.id),
            str(l.event_id),
            l.name,
            l.code,
            str(l.current_number),
            str(l.last_ticket_number),
            l.last_repeat_at.isoformat() if l.last_repeat_at else "",
            (l.description or "").replace("\n", " "),
        ])

    csv_str = _rows_to_csv(headers, rows)
    filename = f"event-{event_id}-lokets-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return _csv_response(filename, csv_str)


# ============================================================
# 3) EXPORT TICKETS BY EVENT (with optional filters)
# ============================================================

@router.get("/events/{event_id}/tickets/export")
async def export_tickets_csv(
    event_id: int,
    loket_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_database)
):
    result_event = await db.execute(select(Event).where(Event.id == event_id))
    event = result_event.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")

    query = select(Ticket).where(Ticket.event_id == event_id)

    if loket_id:
        query = query.where(Ticket.loket_id == loket_id)

    if status:
        query = query.where(Ticket.status == status)

    result = await db.execute(query)
    tickets: List[Ticket] = result.scalars().all()

    headers = [
        "id",
        "event_id",
        "loket_id",
        "number",
        "status",
        "created_at",
        "called_at",
    ]

    rows = []
    for t in tickets:
        rows.append([
            str(t.id),
            str(t.event_id),
            str(t.loket_id),
            str(t.number),
            t.status,
            t.created_at.isoformat() if t.created_at else "",
            t.called_at.isoformat() if t.called_at else "",
        ])

    csv_str = _rows_to_csv(headers, rows)
    filename = f"event-{event_id}-tickets-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return _csv_response(filename, csv_str)


# ============================================================
# 4) EXPORT TICKETS BY LOKET
# ============================================================

@router.get("/lokets/{loket_id}/tickets/export")
async def export_tickets_by_loket_csv(
    loket_id: int,
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_database),
):
    result_loket = await db.execute(select(Loket).where(Loket.id == loket_id))
    loket = result_loket.scalar_one_or_none()

    if not loket:
        raise HTTPException(404, "Loket not found")

    query = select(Ticket).where(Ticket.loket_id == loket_id)

    if status:
        query = query.where(Ticket.status == status)

    result = await db.execute(query)
    tickets: List[Ticket] = result.scalars().all()

    headers = [
        "id",
        "event_id",
        "loket_id",
        "number",
        "status",
        "created_at",
        "called_at",
    ]

    rows = []
    for t in tickets:
        rows.append([
            str(t.id),
            str(t.event_id),
            str(t.loket_id),
            str(t.number),
            t.status,
            t.created_at.isoformat() if t.created_at else "",
            t.called_at.isoformat() if t.called_at else "",
        ])

    csv_str = _rows_to_csv(headers, rows)
    filename = f"loket-{loket_id}-tickets-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return _csv_response(filename, csv_str)
