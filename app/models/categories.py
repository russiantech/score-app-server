from __future__ import annotations

from typing import Optional
import uuid

from app.db.base_class import Base

from slugify import slugify
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    event,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.mixins import TimestampMixin, UUIDMixin

class Category(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_created_at", "created_at"),
    )

    # id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)

    description: Mapped[str | None] = mapped_column(String(255))

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Handled by TimestampMixin inherited
    # created_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     server_default=func.now(),
    #     nullable=False,
    # )

    # updated_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     server_default=func.now(),
    #     onupdate=func.now(),
    #     nullable=False,
    # )

    # -------------------------
    # Relationships
    # -------------------------

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
        index=True
    )

    # -------------------------
    # Validation
    # -------------------------

    # -------------------------
    # Serialization helpers
    # -------------------------

    def summary(self, include_products: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "parent_id": self.parent_id,
        }

        if include_products:
            data["products"] = [
                {"id": p.id, "name": p.name, "slug": p.slug}
                for p in self.products
            ]

        return data

    def __repr__(self) -> str:
        return f"<Category {self.name}>"

@event.listens_for(Category.name, "set", propagate=True)
def set_category_slug(target: Category, value: str, oldvalue, initiator):
    if value and value != oldvalue:
        target.slug = slugify(value)
