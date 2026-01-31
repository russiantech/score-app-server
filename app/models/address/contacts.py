from __future__ import annotations

from typing import Optional
import uuid
from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class ContactInfo(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_infos"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    preferred_contact: Mapped[Optional[str]] = mapped_column(
        Enum("email", "phone", "both", name="preferred_contact")
    )

    user: Mapped["User"] = relationship(back_populates="contact_info")

    def get_summary(
        self,
        *,
        include_product: bool = False,
    ) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "email": self.email,
            "phone": self.phone,
            "preferred_contact": self.preferred_contact,
        }
        if include_product:
            data["user"] = self.user.get_summary()
        
        return data