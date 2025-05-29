from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
from src.database import get_async_session
from src.models import Telemetry, Alert

async def is_duplicate(
    device_id: str,
    timestamp: datetime,   
    db_session: AsyncSession
) -> bool:
   

    start_window = timestamp - timedelta(seconds=5)
    end_window = timestamp + timedelta(seconds=5)

    stmt = select(Telemetry).where(
        Telemetry.device_id == device_id,
        Telemetry.timestamp.between(start_window, end_window)
    )
    result = await db_session.execute(stmt)
    existing = result.scalars().first()

    return existing is not None


async def check_alerts(
    db: AsyncSession,
    device_id: str,
    power: float,
    voltage: float
):
    stmt = (
        select(Telemetry)
        .where(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(6)
    )
    result = await db.execute(stmt)
    recent_readings = result.scalars().all()

    if len(recent_readings) == 6 and all(r.power < 10 for r in recent_readings):
        stmt = select(Alert).where(
            Alert.device_id == device_id,
            Alert.alert_type == "low_power",
            Alert.is_active.is_(True)
        )
        result = await db.execute(stmt)
        existing_alert = result.scalars().first()

        if not existing_alert:
            alert = Alert(
                device_id=device_id,
                alert_type="low_power",
                details=f"Power below 10W for 6 consecutive readings (last reading: {power}W)",
                is_active=True
            )
            db.add(alert)
            await db.commit()

    if voltage > 270:
        stmt = select(Alert).where(
            Alert.device_id == device_id,
            Alert.alert_type == "high_voltage",
            Alert.is_active.is_(True)
        )
        result = await db.execute(stmt)
        existing_alert = result.scalars().first()

        if not existing_alert:
            alert = Alert(
                device_id=device_id,
                alert_type="high_voltage",
                details=f"Voltage exceeded 270V (current: {voltage}V)",
                is_active=True
            )
            db.add(alert)
            await db.commit()
