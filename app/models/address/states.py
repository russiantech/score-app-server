from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class State(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "states"

    # id: Mapped[int] = mapped_column(primary_key=True)
    geoname_id: Mapped[Optional[int]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    country: Mapped["Country"] = relationship(back_populates="states")
    cities: Mapped[List["City"]] = relationship(
        back_populates="state",
        cascade="all, delete-orphan",
    )

    def get_summary(self, include_cities: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }
        if include_cities:
            data["cities"] = [city.get_summary() for city in self.cities]
        return data
