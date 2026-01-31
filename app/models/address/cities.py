from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import (
    ForeignKey,
    String,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class City(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cities"

    geoname_id: Mapped[Optional[int]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    state_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("states.id"), nullable=False)

    state: Mapped["State"] = relationship(back_populates="cities")
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="city",
        cascade="all, delete-orphan",
    )

    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "geoname_id": self.geoname_id,
            "state_id": self.state_id,
            "created_at": self.created_at.isoformat(),
        }
