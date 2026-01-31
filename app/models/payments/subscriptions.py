from datetime import datetime, timezone, timedelta
import uuid
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.enums import SubscriptionStatus


class Subscription(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id"), index=True
    )

    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    entity_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    start_date: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    end_date: Mapped[datetime] = mapped_column(nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status_enum"),
        default=SubscriptionStatus.pending,
        index=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        default=False, index=True
    )

    # ---------- RELATIONSHIPS ----------
    user: Mapped["User"] = relationship(
        "User", back_populates="subscriptions"
    )

    plan: Mapped["Plan"] = relationship(
        "Plan", back_populates="subscriptions"
    )

    payments: Mapped["Payment"] = relationship(
        "Payment", back_populates="subscription", uselist=False
    )

    # ---------- STATE ----------
    @property
    def is_active(self) -> bool:
        return (
            self.status == SubscriptionStatus.active
            and datetime.now(timezone.utc) < self.end_date
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.end_date

    @property
    def days_remaining(self) -> int:
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    @property
    def hours_remaining(self) -> int:
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds() // 3600))

    # ---------- ACTIONS ----------
    def activate(self):
        if self.status != SubscriptionStatus.pending:
            return
        now = datetime.now(timezone.utc)
        self.start_date = now
        self.end_date = now + timedelta(
            days=self.promotion_plan.duration_days
        )
        self.status = SubscriptionStatus.active

    def cancel(self):
        if self.status in {
            SubscriptionStatus.pending,
            SubscriptionStatus.active,
        }:
            self.status = SubscriptionStatus.canceled

    def expire_if_needed(self):
        if self.status == SubscriptionStatus.active and self.is_expired:
            self.status = SubscriptionStatus.expired

    # ---------- SERIALIZATION ----------
    def get_summary(self, *, include_plan=True) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value,
            "is_active": self.is_active,
            "days_remaining": self.days_remaining,
            "hours_remaining": self.hours_remaining,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_plan and self.plan:
            data["plan"] = self.plan.get_summary()

        return data

    def __repr__(self) -> str:
        return (
            f"<Subscription {self.id} | "
            f"{self.entity_type}:{self.entity_id} | "
            f"{self.status.value}>"
        )

