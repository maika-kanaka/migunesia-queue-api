from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.config.database import get_database
from src.app.models.sound_source import SoundSource
from src.app.models.event import Event
from src.app.schema.sound_source import SoundSourceConfig, SoundConfigUpdate, SoundConfigAll

router = APIRouter(tags=["sound"])

@router.get("/events/{event_id}/sound-config", response_model=SoundSourceConfig)
async def get_sound_config(
    event_id: int,
    role: str = Query(..., description="Halaman role, misal: multi_display, multi_display_led, loket_display, loket_display_led, loket_admin"),
    db: AsyncSession = Depends(get_database),
):
    # pastikan event ada
    result_event = await db.execute(select(Event).where(Event.id == event_id))
    event = result_event.scalar_one_or_none()
    if not event:
      raise HTTPException(status_code=404, detail="Event not found")


    # kalau tidak ada spesifik → pakai default per event
    result_default = await db.execute(
        select(SoundSource).where(
            SoundSource.event_id == event_id,
            SoundSource.role == role,
        )
    )
    default = result_default.scalar_one_or_none()

    if default:
        enabled = default.enabled
    else:
        # fallback: misal default suara ON di display, OFF di admin
        if role in ("multi_display", "loket_display"):
            enabled = True
        else:
            enabled = False

    return SoundSourceConfig(
        event_id=event_id,
        role=role,
        enabled=enabled,
    )


@router.put("/events/{event_id}/sound-config", response_model=SoundConfigAll)
async def update_sound_config(
    event_id: int,
    body: SoundConfigUpdate,
    db: AsyncSession = Depends(get_database),
):
    # pastikan event ada
    result_event = await db.execute(select(Event).where(Event.id == event_id))
    event = result_event.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # mapping role -> enabled dari body
    role_map = {
      "multi_display": body.multi_display,
      "multi_display_led": body.multi_display_led,
      "loket_display": body.loket_display,
      "loket_display_led": body.loket_display_led,
      "loket_admin": body.loket_admin,
    }

    for role, enabled in role_map.items():
        result = await db.execute(
            select(SoundSource).where(
                SoundSource.event_id == event_id,
                SoundSource.role == role,
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.enabled = enabled
        else:
            record = SoundSource(
                event_id=event_id,
                role=role,
                enabled=enabled,
            )
        db.add(record)

    await db.commit()

    return SoundConfigAll(
        event_id=event_id,
        multi_display=body.multi_display,
        multi_display_led=body.multi_display_led,
        loket_display=body.loket_display,
        loket_display_led=body.loket_display_led,
        loket_admin=body.loket_admin,
    )

