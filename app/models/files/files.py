from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class FileUpload(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "file_uploads"

    # Handled by UUIDMixin inherited as UUID primary key
    # id: Mapped[int] = mapped_column(primary_key=True)

    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="Polymorphic discriminator",
    )

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(140), nullable=False)
    original_name: Mapped[str] = mapped_column(String(140), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Handled by TimestampMixin inherited
    # created_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     server_default=func.now(),
    #     index=True,
    # )
    # updated_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     server_default=func.now(),
    #     onupdate=func.now(),
    # )

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "file",
    }

    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "original_name": self.original_name,
            "file_size": self.file_size,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
