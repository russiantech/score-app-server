from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    String,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class Address(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "addresses"
    names: Mapped[Optional[str]] = mapped_column(String(140))
    street: Mapped[str] = mapped_column(String(140), nullable=False)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    house: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(140))
    phone_number: Mapped[Optional[str]] = mapped_column(String(140))
    adrs_type: Mapped[str] = mapped_column(
        Enum("user", "store", name="address_type"),
        default="user",
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    city: Mapped["City"] = relationship(back_populates="addresses")
    user: Mapped[Optional["User"]] = relationship(back_populates="addresses")
    # orders: Mapped[List["Order"]] = relationship(
    #     back_populates="address",
    #     cascade="all, delete-orphan",
    # )
    
    def get_summary(
        self,
        *,
        include_city: bool = True,
        include_state: bool = False,
        include_country: bool = False,
        include_user: bool = False,
        include_store: bool = False,
    ) -> dict:
        data = {
            "id": self.id,
            "names": self.names,
            "street_address": self.street_address,
            "zip_code": self.zip_code,
            "phone_number": self.phone_number,
            "is_primary": self.is_primary,
            "type": self.adrs_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_city and self.city:
            city = {"id": self.city.id, "name": self.city.name}

            if include_state and self.city.state:
                state = {"id": self.city.state.id, "name": self.city.state.name}

                if include_country and self.city.state.country:
                    state["country"] = {
                        "id": self.city.state.country.id,
                        "name": self.city.state.country.name,
                        "code": self.city.state.country.code,
                    }

                city["state"] = state

            data["city"] = city

        if include_user and self.user:
            data["user"] = {"id": self.user.id, "username": self.user.username}

        if include_store and self.store:
            data["store"] = {
                "id": self.store.id,
                "name": self.store.name,
                "phone": self.store.phone,
                "email": self.store.email,
            }

        return data
