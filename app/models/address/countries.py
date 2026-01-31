from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    String,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class Country(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "countries"

    geoname_id: Mapped[Optional[int]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    languages: Mapped[Optional[str]] = mapped_column(String(255))
    iso_numeric: Mapped[Optional[str]] = mapped_column(String(10), unique=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(50))
    currency_symbol: Mapped[Optional[str]] = mapped_column(String(10))
    logo_url: Mapped[Optional[str]] = mapped_column(String(255))
    flag_url: Mapped[Optional[str]] = mapped_column(String(255))

    states: Mapped[List["State"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan",
    )

    def get_summary(self, include_states: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "created_at": self.created_at.isoformat(),
        }
        if include_states:
            data["states"] = [state.get_summary() for state in self.states]
        return data
