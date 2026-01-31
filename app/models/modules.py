# app/models/modules.py
from typing import List
from sqlalchemy import Date, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.mixins import TimestampMixin, UUIDMixin
from app.db.base_class import Base


# app/models/lesson.py
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
import uuid

class Module(UUIDMixin, TimestampMixin, Base):
    
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint('course_id', 'order', name='uq_module_order'),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Details
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # Order in course
    start_date = mapped_column(Date)
    end_date = mapped_column(Date)
    
    # Relationships
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="modules"
    )
    
    lessons = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order"
    )
    
    
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="module"
    )
    
    score_columns: Mapped[List["ScoreColumn"]] = relationship(
        "ScoreColumn",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    def get_summary(self, include_relations: bool = False):
        data = {
            "id": self.id,
            "title": self.title,
            "order": self.order,
            "description": self.description,
            "course_id": self.course_id,
            "created_at": self.created_at,
        }

        if include_relations:
            data["lessons"] = [
                {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "description": lesson.description,
                    "order": lesson.order,
                    "date": lesson.date.isoformat() if lesson.date else None,
                    "duration_minutes": lesson.duration_minutes,
                    "is_published": lesson.is_published,
                }
                for lesson in self.lessons
            ]

            data["lessons_count"] = len(self.lessons)

        return data

