import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from src.database import async_session_maker  # Your session maker
from src.models import Telemetry, Discarded, Alert
import json


async def populate_dummy_data():
    async with async_session_maker() as session: 
        now = datetime.utcnow()

        # Normal telemetry
        t1 = Telemetry(
            device_id="SOL-XL1001",
            timestamp=now - timedelta(minutes=1),
            voltage=230.5,
            current=5.2,
            power=1197.6,
            is_duplicate=False
        )

        # Duplicate telemetry (same timestamp window as t1)
        t2 = Discarded(
            device_id="SOL-XL1001",
            timestamp=now - timedelta(minutes=1),
            data=json.dumps({
                "device_id": "SOL-XL1001",
                "timestamp": (now - timedelta(minutes=1)).isoformat(),
                "voltage": 230.5,
                "current": 5.2,
                "power": 1197.6,
            }),
            reason="duplicate"
        )

        # Alert-triggering telemetry (let’s assume some alert logic based on high voltage)
        t3 = Telemetry(
            device_id="SOL-XL1001",
            timestamp=now,
            voltage=400.0,
            current=6.0,
            power=2400.0,
            is_duplicate=False
        )

        alert = Alert(
            device_id="SOL-XL1001",
            alert_type="High Voltage",
            triggered_at=now,
            is_active=True,
            details="Voltage exceeded 380V"
        )

        # Add all
        session.add_all([t1, t2, t3, alert])
        await session.commit()
        print("Dummy data inserted.")


if __name__ == "__main__":
    asyncio.run(populate_dummy_data())
