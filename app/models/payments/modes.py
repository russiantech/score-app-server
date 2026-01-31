import uuid
from sqlalchemy import (
    UUID,
    String,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class PaymentModes(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_modes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    method: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    details: Mapped[dict] = mapped_column(JSON, nullable=False)

    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ---------- RELATIONSHIPS ----------
    user: Mapped["User"] = relationship(
        "User", back_populates="payment_modes"
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="modes"
    )

    __table_args__ = (
        # Enforce only one primary method per user
        # (Handled carefully in business logic)
        {},
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod {self.method} | User {self.user_id}>"
    
    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "method": self.method,
            "details": self.details,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }