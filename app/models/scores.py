from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, String, Float, Text, 
    ForeignKey, UniqueConstraint, func, Enum as SQLEnum, 
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.assessment import Assessment
from app.models.enums import AssessmentScope, AssessmentType

class Score(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint('enrollment_id', 'lesson_id', name='uq_enrollment_lesson'),
        CheckConstraint('score >= 0 AND score <= 100', name='check_assessment'),
    )
    
    enrollment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('enrollments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    lesson_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('lessons.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    column_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('score_columns.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    recorder_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Score Details - FIXED: Pass the enum CLASS, not a specific value
    # type: Mapped[AssessmentType] = mapped_column(
    #     Enum(AssessmentType, name='assessmenttype'),  # Pass the class, not AssessmentType.CLASSWORK
    #     nullable=False,
    #     server_default=text("'assessment'::assessmenttype")  # PostgreSQL default
    # )
    
    type: Mapped[AssessmentType] = mapped_column(
        SQLEnum(AssessmentType), nullable=False, default=AssessmentType.CLASSWORK
    )
    
    # Foreign keys to assessment or assignment
    assessment_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('assessments.id', ondelete='CASCADE')
    )
    
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Grading Details
    grade: Mapped[Optional[str]] = mapped_column(String(5))  # A, B, C, etc.
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Recording Information
    recorded_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        back_populates="scores"
    )
    
    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="scores"
    )
    
    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="scores"
    )
    
    column: Mapped[List["ScoreColumn"]] = relationship(
        "ScoreColumn",
        back_populates="scores",
        # cascade="all, delete-orphan" # cascade should be on the one side in a many-many relationship
    )

    recorder: Mapped["User"] = relationship(
        "User",
        back_populates="recorded_scores",
        foreign_keys=[recorder_id]
    )
    
    assessment: Mapped[Optional["Assessment"]] = relationship(
        "Assessment",
        back_populates="scores"
    )
    
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="score",
        cascade="all, delete-orphan"
    )
    
    # Calculate percentage automatically
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'score') and hasattr(self, 'max_score'):
            self.percentage = self.calculate_percentage()
            
    # @hybrid_property
    # def percentage(self) -> float:
    #     if self.max_score > 0:
    #         return (self.score / self.max_score) * 100
    #     return 0.0
    
    def calculate_percentage(self) -> float:
        """Calculate percentage from score and max_score."""
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0.0

    def get_summary(self) -> dict:
        """Get score summary for API responses."""
        return {
            "id": str(self.id),
            "enrollment_id": str(self.enrollment_id),
            "lesson_id": str(self.lesson_id),
            "type": self.type.value,
            "assessment_id": str(self.assessment_id) if self.assessment_id else None,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "grade": self.grade,
            "weight": self.weight,
            "is_final": self.is_final,
            "notes": self.notes,
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
            "recorded_by": str(self.recorder_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }




# ============================================================================
# UPDATED SCORE COLUMN MODEL
# ============================================================================

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import Optional, List
from uuid import UUID
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class ScoreColumn(UUIDMixin, TimestampMixin, Base):
    """
    Score columns with standardized hierarchy:
    - LESSON: Homework (required), Classwork (required), Quiz/Test (optional)
    - MODULE: Exam (standard)
    - COURSE: Project (standard)
    """
    __tablename__ = "score_columns"
    
    # Scope (only ONE should be set)
    lesson_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('lessons.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    module_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    course_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )

    # Column configuration
    type: Mapped[AssessmentType] = mapped_column(
        SQLEnum(AssessmentType), 
        nullable=False
    )
    scope: Mapped[AssessmentScope] = mapped_column(
        SQLEnum(AssessmentScope),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Standardization flags
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-created
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    lesson: Mapped[Optional["Lesson"]] = relationship(
        "Lesson",
        back_populates="score_columns"
    )
    module: Mapped[Optional["Module"]] = relationship(
        "Module",
        back_populates="score_columns"
    )
    course: Mapped[Optional["Course"]] = relationship(
        "Course",
        back_populates="score_columns"
    )
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="column",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    def get_scope_id(self) -> Optional[UUID]:
        """Get the ID of the scope this column belongs to"""
        if self.lesson_id:
            return self.lesson_id
        if self.module_id:
            return self.module_id
        if self.course_id:
            return self.course_id
        return None
    
    def get_summary(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "scope": self.scope.value,
            "title": self.title,
            "description": self.description,
            "max_score": float(self.max_score),
            "weight": float(self.weight),
            "order": self.order,
            "is_required": self.is_required,
            "is_active": self.is_active,
            "lesson_id": str(self.lesson_id) if self.lesson_id else None,
            "module_id": str(self.module_id) if self.module_id else None,
            "course_id": str(self.course_id) if self.course_id else None,
        }


# ============================================================================
# SCORE MODEL (Reference previous implementation)
# See: score_types_enums artifact for full Score model or add following relationships
# ============================================================================


# ============================================================================
# Update existing models to include score_columns relationship
# ============================================================================

# Add to Lesson model:
# score_columns: Mapped[List["ScoreColumn"]] = relationship(
#     "ScoreColumn",
#     back_populates="lesson",
#     cascade="all, delete-orphan"
# )

# Add to Module model:
# score_columns: Mapped[List["ScoreColumn"]] = relationship(
#     "ScoreColumn",
#     back_populates="module",
#     cascade="all, delete-orphan"
# )

# Add to Course model:
# score_columns: Mapped[List["ScoreColumn"]] = relationship(
#     "ScoreColumn",
#     back_populates="course",
#     cascade="all, delete-orphan"
# )