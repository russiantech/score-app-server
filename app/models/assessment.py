from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    Integer,
    Float,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from sqlalchemy import Enum as SQLEnum

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.enums import AssessmentType


# -------------------------------------------------------------------------
# ENUM DEFINITIONS
# -------------------------------------------------------------------------

# class AssessmentType(str, Enum):
#     ASSIGNMENT = "assignment"
#     ASSESSMENT = "assessment"
#     QUIZ = "quiz"
#     EXAM = "exam"
#     PROJECT = "project"
#     HOMEWORK = "homework"
#     CLASSWORK = "classwork"
#     LAB = "lab"
#     PRESENTATION = "presentation"
#     OTHER = "other"


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    GRADED = "graded"


class SubmissionStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    RETURNED = "returned"


# -------------------------------------------------------------------------
# TYPE CHECKING IMPORTS (Prevents Circular Imports)
# -------------------------------------------------------------------------

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.user import User
    from app.models.score import Score
    from app.models.student import Student


# -------------------------------------------------------------------------
# ASSESSMENT MODEL (SQLAlchemy 2.0 typed)
# -------------------------------------------------------------------------

class Assessment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessments"

    # Foreign Keys
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Basic Info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)

    # Assessment Details
    type: Mapped[AssessmentType] = mapped_column(
        SQLEnum(AssessmentType), nullable=False, default=AssessmentType.CLASSWORK
    )
    # type = Column(String(50), nullable=False, default=AssessmentType.CLASSWORK.value)
    status: Mapped[AssessmentStatus] = mapped_column(
        SQLEnum(AssessmentStatus), nullable=False, default=AssessmentStatus.DRAFT
    )

    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Grading
    total_points: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    passing_score: Mapped[Optional[float]] = mapped_column(Float)

    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Settings
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=True)
    late_penalty_percent: Mapped[float] = mapped_column(Float, default=0.0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Files
    attachment_urls: Mapped[Optional[str]] = mapped_column(Text)

    # Visibility
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # ---------------------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------------------

    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="assessments",
        lazy="selectin",
    )

    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_assessments",
        lazy="selectin",
        foreign_keys=[creator_id],
    )

    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="assessment",
        lazy="selectin",
    )

    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ---------------------------------------------------------------------
    # PROPERTIES
    # ---------------------------------------------------------------------

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return datetime.now() > self.due_date

    @property
    def is_available(self) -> bool:
        now = datetime.now()

        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False

        return self.is_published

    @property
    def submission_count(self) -> int:
        return len(self.submissions) if self.submissions else 0

    @property
    def graded_count(self) -> int:
        return (
            len([s for s in self.submissions if s.status == SubmissionStatus.GRADED])
            if self.submissions
            else 0
        )

    def get_summary(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "lesson_id": str(self.lesson_id),
            "total_points": self.total_points,
            "passing_score": self.passing_score,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_until": self.available_until.isoformat() if self.available_until else None,
            "is_published": self.is_published,
            "is_overdue": self.is_overdue,
            "is_available": self.is_available,
            "allow_late_submission": self.allow_late_submission,
            "max_attempts": self.max_attempts,
            "time_limit_minutes": self.time_limit_minutes,
            "submission_count": self.submission_count,
            "graded_count": self.graded_count,
            "creator_id": str(self.creator_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# -------------------------------------------------------------------------
# SUBMISSION MODEL (SQLAlchemy 2.0 typed)
# -------------------------------------------------------------------------

class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign Keys
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Submission content
    content: Mapped[Optional[str]] = mapped_column(Text)
    attachment_urls: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.NOT_SUBMITTED,
    )

    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Scoring
    score: Mapped[Optional[float]] = mapped_column(Float)
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    graded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Late submission
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    late_penalty_applied: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="submissions",
        lazy="selectin",
    )

    student: Mapped["Student"] = relationship(
        "User",
        back_populates="submissions",
        foreign_keys=[student_id],
        lazy="selectin",
    )

    grader: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[graded_by],
    )

    # Computed properties
    @property
    def final_score(self) -> Optional[float]:
        if self.score is None:
            return None
        return max(0, self.score - self.late_penalty_applied)

    @property
    def percentage(self) -> Optional[float]:
        if self.score is None or not self.assessment:
            return None
        if self.assessment.total_points == 0:
            return 0
        return (self.final_score / self.assessment.total_points) * 100

    def get_summary(self) -> dict:
        return {
            "id": str(self.id),
            "assessment_id": str(self.assessment_id),
            "student_id": str(self.student_id),
            "status": self.status.value,
            "attempt_number": self.attempt_number,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "score": self.score,
            "final_score": self.final_score,
            "percentage": self.percentage,
            "feedback": self.feedback,
            "is_late": self.is_late,
            "late_penalty_applied": self.late_penalty_applied,
            "graded_by": str(self.graded_by) if self.graded_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
