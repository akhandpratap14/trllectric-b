from sqlalchemy import String, Float, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from src.database import BaseModel


class Telemetry(BaseModel):
    __tablename__ = "telemetry"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    voltage: Mapped[float] = mapped_column(Float)
    current: Mapped[float] = mapped_column(Float)
    power: Mapped[float] = mapped_column(Float)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    discarded_records = relationship(
        "Discarded",
        back_populates="telemetry",
        lazy="selectin"
    )
    alerts = relationship(
        "Alert",
        back_populates="telemetry",
        lazy="selectin"
    )


class Discarded(BaseModel):
    __tablename__ = "discarded"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telemetry_id: Mapped[int] = mapped_column(ForeignKey("telemetry.id"), index=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    telemetry_id: Mapped[int] = mapped_column(ForeignKey("trillectric.telemetry.id"), nullable=True)
    data: Mapped[str] = mapped_column(String) 
    reason: Mapped[str] = mapped_column(String) 
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    telemetry = relationship(
        "Telemetry",
        back_populates="discarded_records",
        lazy="noload"
    )


class Alert(BaseModel):
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telemetry_id: Mapped[int] = mapped_column(ForeignKey("telemetry.id"), index=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    alert_type: Mapped[str] = mapped_column(String)  
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[str] = mapped_column(String) 
    telemetry_id: Mapped[int] = mapped_column(ForeignKey("trillectric.telemetry.id"), nullable=False)
    
    telemetry = relationship(
        "Telemetry",
        back_populates="alerts",
        lazy="noload"
    )
