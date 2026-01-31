from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
import uuid

class Location(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_location_coords", "latitude", "longitude"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_longitude"),
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    address: Mapped[Optional[str]] = mapped_column(Text)
    zoom_level: Mapped[int] = mapped_column(default=12)
    user: Mapped["User"] = relationship(back_populates="location_info", lazy="selectin")
    
    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "address": self.address,
            "zoom_level": self.zoom_level,
        }
    
    