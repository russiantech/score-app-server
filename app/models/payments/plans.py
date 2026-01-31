from sqlalchemy import (
    String,
    Numeric,
    Integer,
    Boolean,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class Plan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="NGN", nullable=False
    )

    description: Mapped[str | None] = mapped_column(Text)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    features: Mapped[list | None] = mapped_column(
        JSON, default=list
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

    # UI / Marketing metadata
    badge: Mapped[str | None] = mapped_column(String(50))
    badge_color: Mapped[str | None] = mapped_column(String(50))
    icon: Mapped[str | None] = mapped_column(String(50))

    # Plan configuration
    priority_level: Mapped[int] = mapped_column(
        Integer, default=1
    )

    max_boost_count: Mapped[int | None] = mapped_column(Integer)
    analytics_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    support_level: Mapped[str] = mapped_column(
        String(50), default="standard"
    )
    social_media_promotion: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )

    # ---------- RELATIONSHIPS ----------
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    # ---------- HELPERS ----------
    @classmethod
    def get_active(cls, db):
        return (
            db.query(cls)
            .filter(
                cls.is_active.is_(True),
                cls.is_deleted.is_(False),
            )
            .all()
        )

    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "price": float(self.price),
            "currency": self.currency,
            "description": self.description,
            "duration_days": self.duration_days,
            "duration_text": self.format_duration(),
            "features": self.features or [],
            "is_active": self.is_active,
            "badge": self.badge,
            "badge_color": self.badge_color,
            "icon": self.icon,
            "priority_level": self.priority_level,
            "max_boost_count": self.max_boost_count,
            "analytics_enabled": self.analytics_enabled,
            "support_level": self.support_level,
            "social_media_promotion": self.social_media_promotion,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def format_duration(self) -> str:
        days = self.duration_days
        if days == 1:
            return "1 day"
        if days == 7:
            return "1 week"
        if days == 30:
            return "1 month"
        if days < 7:
            return f"{days} days"
        if days < 30:
            weeks, rem = divmod(days, 7)
            return f"{weeks} week{'s' if weeks > 1 else ''}" + (
                f" {rem} day{'s' if rem > 1 else ''}" if rem else ""
            )
        months, rem = divmod(days, 30)
        return f"{months} month{'s' if months > 1 else ''}" + (
            f" {rem} day{'s' if rem > 1 else ''}" if rem else ""
        )

    def __repr__(self) -> str:
        return f"<PromotionPlan {self.slug} | ₦{self.price}>"
