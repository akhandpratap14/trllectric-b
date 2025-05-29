from sqlalchemy import select, func
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
import json

from src.database import get_async_session
from src.models import Telemetry, Alert, Discarded
from src.trillectric.schemas import TelemetryDataCreate, AlertResponse, DeviceStatsResponse
from src.trillectric.services import is_duplicate, check_alerts

trillectric_router = APIRouter(tags=["Trillectric"])


@trillectric_router.post("/ingest/", status_code=status.HTTP_201_CREATED)
async def ingest_data(
    data: TelemetryDataCreate,
    db: AsyncSession = Depends(get_async_session)
):
    # Parse timestamp early
    try:
        ts = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
    except ValueError:
        discarded = Discarded(
            device_id=data.device_id,
            timestamp=None,
            data=json.dumps(data.dict()),
            reason="invalid_timestamp"
        )
        db.add(discarded)
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Validate required fields except timestamp
    if None in [data.device_id, data.voltage, data.current, data.power]:
        discarded = Discarded(
            device_id=data.device_id,
            timestamp=ts,
            data=json.dumps(data.dict()),
            reason="malformed"
        )
        db.add(discarded)
        await db.commit()
        raise HTTPException(status_code=400, detail="Payload is missing required fields")

    # Check duplicate
    if await is_duplicate(data.device_id, ts, db):
        discarded = Discarded(
            device_id=data.device_id,
            timestamp=ts,
            data=json.dumps(data.dict()),
            reason="duplicate"
        )
        db.add(discarded)
        await db.commit()
        return {"status": "duplicate", "message": "Data already exists within 5-second window"}

    # Save telemetry
    telemetry = Telemetry(
        device_id=data.device_id,
        timestamp=ts,
        voltage=data.voltage,
        current=data.current,
        power=data.power
    )
    db.add(telemetry)
    await db.commit()

    await check_alerts(db, data.device_id, data.power, data.voltage)

    return {"status": "success", "message": "Data ingested successfully"}



@trillectric_router.get("/alerts/{device_id}", response_model=List[AlertResponse])
async def get_alerts(device_id: str, active_only: bool = True, db: AsyncSession = Depends(get_async_session)):
    stmt = select(Alert).where(Alert.device_id == device_id)
    if active_only:
        stmt = stmt.where(Alert.is_active == True)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return alerts


def serialize_telemetry(t):
    return {
        "device_id": t.device_id,
        "timestamp": t.timestamp.isoformat(),  # convert datetime to string
        "voltage": t.voltage,
        "current": t.current,
        "power": t.power,
        "is_duplicate": t.is_duplicate,
    }

@trillectric_router.get("/telemetry/{device_id}")
async def get_telemetry(device_id: str, db: AsyncSession = Depends(get_async_session)):
    stmt = select(Telemetry).where(Telemetry.device_id == device_id)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [serialize_telemetry(t) for t in records]


@trillectric_router.get("/stats/{device_id}", response_model=DeviceStatsResponse)
async def get_device_stats(device_id: str, db: AsyncSession = Depends(get_async_session)):
    total_entries_stmt = select(func.count()).select_from(Telemetry).where(Telemetry.device_id == device_id)
    duplicates_count_stmt = select(func.count()).select_from(Discarded).where(Discarded.device_id == device_id, Discarded.reason == "duplicate")
    discarded_count_stmt = select(func.count()).select_from(Discarded).where(Discarded.device_id == device_id, Discarded.reason != "duplicate")
    active_alerts_stmt = select(Alert).where(Alert.device_id == device_id, Alert.is_active == True)

    total_entries = (await db.execute(total_entries_stmt)).scalar_one()
    duplicates_count = (await db.execute(duplicates_count_stmt)).scalar_one()
    discarded_count = (await db.execute(discarded_count_stmt)).scalar_one()
    active_alerts_result = await db.execute(active_alerts_stmt)
    active_alerts = active_alerts_result.scalars().all()

    return DeviceStatsResponse(
        device_id=device_id,
        total_entries=total_entries,
        duplicates_count=duplicates_count,
        discarded_count=discarded_count,
        active_alerts=active_alerts
    )

@trillectric_router.post("/insert")
async def insert_dummy_data(session: AsyncSession = Depends(get_async_session)):
    now = datetime.utcnow()

    # Insert 1st telemetry (normal)
    t1 = Telemetry(
        device_id="SOL-XL1001",
        timestamp=now - timedelta(minutes=1),
        voltage=230.5,
        current=5.2,
        power=1197.6,
        is_duplicate=False
    )

    # Insert 2nd telemetry (for alert)
    t2 = Telemetry(
        device_id="SOL-XL1001",
        timestamp=now,
        voltage=400.0,
        current=6.0,
        power=2400.0,
        is_duplicate=False
    )

    # Flush telemetry to get IDs
    session.add_all([t1, t2])
    await session.flush()  # This populates t1.id and t2.id without committing

    # Create alert based on 2nd telemetry
    a1 = Alert(
        telemetry_id=t2.id,  # ✅ Use the flushed ID
        device_id="SOL-XL1001",
        alert_type="High Voltage",
        triggered_at=now,
        is_active=True,
        details="Voltage exceeded 380V"
    )

    # Discarded (duplicate of t1)
    d1 = Discarded(
        device_id="SOL-XL1001",
        timestamp=t1.timestamp,
        data=json.dumps({
            "device_id": "SOL-XL1001",
            "timestamp": t1.timestamp.isoformat(),
            "voltage": 230.5,
            "current": 5.2,
            "power": 1197.6,
        }),
        reason="duplicate"
    )

    session.add_all([a1, d1])
    await session.commit()

    return {"status": "Dummy data inserted"}
