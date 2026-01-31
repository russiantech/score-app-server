import uuid
from sqlalchemy import (
    String,
    Numeric,
    Boolean,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin
from app.models.enums import PaymentStatus


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    # ---------- FOREIGN KEYS ----------
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        index=True,
    )

    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        index=True,
    )

    payment_mode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_modes.id", ondelete="SET NULL"),
        index=True,
    )

    # ---------- PAYMENT DETAILS ----------
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="NGN", nullable=False
    )

    channel: Mapped[str | None] = mapped_column(String(50))
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)

    reference_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(255), index=True
    )

    meta_data: Mapped[dict | None] = mapped_column(JSON)

    # ---------- STATE ----------
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.pending,
        nullable=False,
        index=True,
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    lock_reason: Mapped[str | None] = mapped_column(String(255))

    # ---------- RELATIONSHIPS ----------
    user: Mapped["User"] = relationship(
        "User", back_populates="payments"
    )

    course: Mapped["Course"] = relationship(
        "Course", back_populates="payments"
    )

    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="payments"
    )
    
    modes: Mapped["PaymentModes"] = relationship(
        "PaymentModes", back_populates="payments"
    )

    # ---------- HELPERS ----------
    @classmethod
    def get_by_reference(cls, db, reference: str):
        if not reference:
            raise ValueError("Reference cannot be empty")

        return (
            db.query(cls)
            .filter(
                (cls.reference_id == reference)
                | (cls.transaction_id == reference)
                | (cls.id == reference)
            )
            .first()
        )

    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "subscription_id": self.subscription_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "channel": self.channel,
            "gateway": self.gateway,
            "status": self.status.value,
            "reference_id": self.reference_id,
            "transaction_id": self.transaction_id,
            "meta_data": self.meta_data,
            "is_locked": self.is_locked,
            "lock_reason": self.lock_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<Payment {self.id} | "
            f"{self.amount} {self.currency} | "
            f"{self.status.value}>"
        )

