from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class FileUpload(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "file_uploads"

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

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


class ProductImage(FileUpload):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("products.id"),
        index=True,
    )

    is_cover: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    product: Mapped[Optional["Product"]] = relationship(
        back_populates="images"
    )

    __mapper_args__ = {
        "polymorphic_identity": "product_image",
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
            "product_id": self.product_id,
            "is_cover": self.is_cover,
        })
        return data


class CategoryImage(FileUpload):
    __tablename__ = "category_images"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id"),
        index=True,
    )

    category: Mapped[Optional["Category"]] = relationship(backref="images")

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

class OfferImage(FileUpload):
    __tablename__ = "offer_images"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    offer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("offers.id"),
        index=True,
    )

    offer: Mapped[Optional["Offer"]] = relationship(
        back_populates="images"
    )

    __mapper_args__ = {
        "polymorphic_identity": "offer_image",
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
            "offer_id": self.offer_id,
        })
        return data

class UserAvatar(FileUpload):
    __tablename__ = "user_avatars"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_uploads.id"),
        primary_key=True,
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        index=True,
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