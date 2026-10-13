from datetime import date, datetime, timezone
from enum import Enum

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from app.api.auth import get_current_user

router = APIRouter(prefix="/prayers", tags=["Prayer tracking"])


class PrayerName(str, Enum):
    fajr = "fajr"
    dhuhr = "dhuhr"
    asr = "asr"
    maghrib = "maghrib"
    isha = "isha"


class PrayerStatus(str, Enum):
    on_time = "on_time"
    late = "late"
    missed = "missed"
    qaza = "qaza"
    excused = "excused"


class PrayerLogInput(BaseModel):
    prayer_date: date
    prayer: PrayerName
    status: PrayerStatus
    note: str | None = Field(default=None, max_length=300)


class PrayerLogResponse(BaseModel):
    prayer_date: date
    prayer: PrayerName
    status: PrayerStatus
    note: str | None = None
    updated_at: datetime


def _public_log(doc: dict) -> PrayerLogResponse:
    return PrayerLogResponse(
        prayer_date=doc["prayer_date"],
        prayer=doc["prayer"],
        status=doc["status"],
        note=doc.get("note"),
        updated_at=doc["updated_at"],
    )


@router.put("/logs", response_model=PrayerLogResponse)
async def save_prayer_log(
    payload: PrayerLogInput,
    user: dict = Depends(get_current_user),
) -> PrayerLogResponse:
    """Create or update one prayer status for the authenticated user and date."""
    from app.core.database import get_database

    now = datetime.now(timezone.utc)
    query = {
        "user_id": user["_id"],
        "prayer_date": payload.prayer_date.isoformat(),
        "prayer": payload.prayer.value,
    }
    document = await get_database().prayer_logs.find_one_and_update(
        query,
        {
            "$set": {
                "status": payload.status.value,
                "note": payload.note,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return _public_log(document)


@router.get("/logs", response_model=list[PrayerLogResponse])
async def list_prayer_logs(
    start_date: date,
    end_date: date,
    user: dict = Depends(get_current_user),
) -> list[PrayerLogResponse]:
    """List only the signed-in user's prayer records within an inclusive date range."""
    from app.core.database import get_database

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date.",
        )
    if (end_date - start_date).days > 366:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date range cannot exceed 367 calendar days.",
        )
    cursor = get_database().prayer_logs.find(
        {
            "user_id": user["_id"],
            "prayer_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()},
        },
        {"_id": 0},
    ).sort([("prayer_date", 1), ("prayer", 1)])
    return [_public_log(item) async for item in cursor]
