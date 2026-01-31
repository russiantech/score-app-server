# app/db/mixins.py
from sqlalchemy import Column, DateTime, func

class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),      # DB default
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),      # DB default
        onupdate=func.now(),            # Auto-update on UPDATE
        nullable=False,
    )

# v2
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
import uuid

# -----------------------------------
# Base Mixins
# -----------------------------------

class UUIDMixin:
    """
    Adds a UUID primary key `id`.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

