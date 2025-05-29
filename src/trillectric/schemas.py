from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class TelemetryDataCreate(BaseModel):
    device_id: str
    timestamp: datetime  # or use `datetime` if you want automatic parsing
    voltage: float
    current: float
    power: float

class AlertResponse(BaseModel):
    id: int
    device_id: str
    alert_type: str
    triggered_at: datetime
    is_active: bool
    resolved_at: Optional[datetime]
    details: str

    model_config = ConfigDict(from_attributes=True)

class DeviceStatsResponse(BaseModel):
    device_id: str
    total_entries: int
    duplicates_count: int
    discarded_count: int
    active_alerts: List[AlertResponse]

    model_config = ConfigDict(from_attributes=True)
