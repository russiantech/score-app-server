# # app/models/lesson.py
# v3
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    String,
    Integer,
    Float,
    Text,
    Date as SQLADate,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import  Enum as SQLEnum, func, case, select
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin
from app.schemas.attendance import AttendanceStatus
from app.models.enums import LessonStatus


class Lesson(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "lessons"

    # -------------------------
    # Constraints
    # -------------------------
    __table_args__ = (
        UniqueConstraint("module_id", "order", name="uq_module_lesson_order"),
        CheckConstraint("assessment_max >= 0", name="check_assessment_max_positive"),
        CheckConstraint("assignment_max >= 0", name="check_assignment_max_positive"),
        CheckConstraint('"order" >= 1', name="check_lesson_order_positive"),
        CheckConstraint(
            "status IN ('completed', 'ongoing', 'upcoming', 'cancelled')",
            name="check_lesson_status_valid",
        )

    )

    # -------------------------
    # Relationships
    # -------------------------
    module_id: Mapped[UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="lessons",
    )

    created_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
    )

    # -------------------------
    # Lesson fields
    # -------------------------
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # Order in course

    date: Mapped[Optional[date]] = mapped_column(
        SQLADate,
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(Text)

    assessment_max: Mapped[Optional[float]] = mapped_column(Float)
    assignment_max: Mapped[Optional[float]] = mapped_column(Float)
    
    # 
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Assessment/Assignment Configuration
    has_assessment: Mapped[bool] = mapped_column(Boolean, default=True)
    has_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    

    # status: Mapped[str] = mapped_column(
    #     String(20),
    #     nullable=False,
    #     default="draft",
    # )
    status: Mapped[LessonStatus] = mapped_column(
        SQLEnum(
            LessonStatus,
            name="lesson_status_enum",
            native_enum=False,  # safer for Postgres + SQLite
            # native_enum=True, 
        ),
        nullable=False,
        default=LessonStatus.UPCOMING,
    )

    # -------------------------
    # Related entities
    # -------------------------
    scores: Mapped[list["Score"]] = relationship(
        "Score",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    score_columns: Mapped[list["ScoreColumn"]] = relationship(
        "ScoreColumn",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )

    attendance: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    
    @hybrid_property
    def attendance_count(self):
        """Total number of attendance records for this lesson."""
        if not hasattr(self, '_attendance_count'):
            return len(self.attendance) if self.attendance else 0
        return self._attendance_count
    
    @attendance_count.setter
    def attendance_count(self, value):
        self._attendance_count = value
    
    @hybrid_property
    def present_count(self):
        """Number of students marked present."""
        if not hasattr(self, '_present_count'):
            if self.attendance:
                return sum(1 for a in self.attendance if a.status == AttendanceStatus.PRESENT)
            return 0
        return self._present_count
    
    @present_count.setter
    def present_count(self, value):
        self._present_count = value
    
    @hybrid_property
    def attendance_rate(self):
        """Percentage of students present."""
        if not hasattr(self, '_attendance_rate'):
            total = self.attendance_count
            if total > 0:
                return round((self.present_count / total) * 100, 1)
            return 0
        return self._attendance_rate
    
    @attendance_rate.setter
    def attendance_rate(self, value):
        self._attendance_rate = value

    # -------------------------
    # Serializer
    # -------------------------
    # def get_summary(self, include_module: bool = False) -> dict:
    #     data = {
    #         "id": str(self.id),
    #         "module_id": str(self.module_id),
    #         "title": self.title,
    #         "order": self.order,
    #         "date": self.date.isoformat() if self.date else None,
    #         "description": self.description,
    #         "assessment_max": self.assessment_max,
    #         "assignment_max": self.assignment_max,
    #         "status": self.status,
    #         "created_at": self.created_at.isoformat() if self.created_at else None,
    #         "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    #     }

    #     if include_module and self.module:
    #         data["module"] = {
    #             "id": str(self.module.id),
    #             "title": self.module.title,
    #             "course_id": str(self.module.course_id),
    #         }

    #     return data

    # app/models/lesson.py - Updated get_summary method

    def get_summary(self, include_module: bool = False) -> dict:
        """
        Return lesson summary with all relevant data including attendance statistics.
        """
        data = {
            "id": str(self.id),
            "module_id": str(self.module_id),
            "title": self.title,
            "order": self.order,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "assessment_max": self.assessment_max,
            "assignment_max": self.assignment_max,
            "duration": f"{self.duration_minutes} mins" if self.duration_minutes else None,
            "status": self.status,
            "is_published": self.is_published,
            "has_assessment": self.has_assessment,
            "has_assignment": self.has_assignment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            
            # Attendance statistics (from hybrid properties)
            "attendance_count": self.attendance_count,
            "present_count": self.present_count,
            "attendance_rate": self.attendance_rate,
        }

        if include_module and self.module:
            data["module"] = {
                "id": str(self.module.id),
                "title": self.module.title,
                "order": self.module.order,
                "course_id": str(self.module.course_id),
            }

        return data
        
