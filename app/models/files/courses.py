

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Uuid,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)

from app.models.files import FileUpload

class CourseImage(FileUpload):
    __tablename__ = "course_images"

    # ID already in inherited FileUpload as UUID primary key
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("courses.id"),
        index=True,
    )

    is_cover: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    course: Mapped[Optional["Course"]] = relationship(
        back_populates="images"
    )

    __mapper_args__ = {
        "polymorphic_identity": "course_image",
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
            "course_id": self.course_id,
            "is_cover": self.is_cover,
        })
        return data

