

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

class UserAvatar(FileUpload):
    __tablename__ = "user_avatars"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    # user_id: Mapped[Optional[int]] = mapped_column(
    #     ForeignKey("users.id"),
    #     index=True,
    # )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
    )
    
    user: Mapped[Optional["User"]] = relationship(back_populates="avatar")

    __mapper_args__ = {
        "polymorphic_identity": "user_avatar",
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
            "user_id": self.user_id,
        })
        return data

