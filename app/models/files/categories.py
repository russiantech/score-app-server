

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)

from app.models.files import FileUpload

class CategoryImage(FileUpload):
    __tablename__ = "category_images"

    id: Mapped[int] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id"),
        index=True,
    )

    category: Mapped[Optional["Category"] | None] = relationship(backref="images")

    __mapper_args__ = {
        "polymorphic_identity": "category_image",
    }
    
    @validates("file_path")
    def validate_file_path(self, key: str, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("File path must be a valid URL")

        if any(char in value for char in ("?", ":")):
            raise ValueError("Invalid characters in file path")

        return value

    def get_summary(self) -> dict:
        data = super().get_summary()
        data.update({
            "category_id": self.category_id,
        })
        return data

