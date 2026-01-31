# # app/models/lesson.py
# from sqlalchemy import Boolean, Date, Integer, String, Text, ForeignKey, UniqueConstraint
# from sqlalchemy.orm import mapped_column, relationship
# from sqlalchemy import Uuid

# from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import Uuid
# from typing import Optional, List
# import uuid

# from app.db.mixins import TimestampMixin, UUIDMixin
# from app.db.base_class import Base

# # class Lesson(UUIDMixin, TimestampMixin, Base):
# #     __tablename__ = "lessons"
# #     __table_args__ = (
# #         UniqueConstraint("module_id", "lesson_number", name="uq_module_lesson_number"),
# #     )

# #     module_id = mapped_column(
# #         Uuid(as_uuid=True),
# #         ForeignKey("modules.id", ondelete="CASCADE"),
# #         nullable=False
# #     )

# #     lesson_number = mapped_column(Integer, nullable=False)
# #     title = mapped_column(String(200), nullable=False)
# #     description = mapped_column(Text)
# #     content = mapped_column(Text)

# #     lesson_date = mapped_column(Date, nullable=False)
# #     duration_minutes = mapped_column(Integer)
# #     is_published = mapped_column(Boolean, default=False)

# #     module = relationship("Module", back_populates="lessons")

# #     attendance = relationship(
# #         "Attendance",
# #         back_populates="lesson",
# #         cascade="all, delete-orphan"
# #     )

# #     # assessments = relationship(
# #     #     "LessonAssessment",
# #     #     back_populates="lesson",
# #     #     cascade="all, delete-orphan"
# #     # )
    
# #     assessments = relationship(
# #         "Assessment",
# #         back_populates="lesson",
# #         cascade="all, delete-orphan"
# #     )

# #     assignments = relationship(
# #         "LessonAssignment",
# #         back_populates="lesson",
# #         cascade="all, delete-orphan"
# #     )


# class Lesson(UUIDMixin, TimestampMixin, Base):
    
#     __tablename__ = "lessons"
#     __table_args__ = (UniqueConstraint('course_id', 'order', name='uq_course_lesson'),)
#     __table_args__ = (UniqueConstraint('module_id', 'order', name='uq_module_lesson'),)

#     course_id: Mapped[uuid.UUID] = mapped_column(
#         Uuid(as_uuid=True), 
#         ForeignKey('courses.id', ondelete='CASCADE'),
#         nullable=False,
#         index=True
#     )
    
#     module_id = mapped_column(
#         Uuid(as_uuid=True),
#         ForeignKey("modules.id", ondelete="CASCADE"),
#         nullable=False
#     )
    
#     # ✅ Optional creator
#     created_by = mapped_column(
#         Uuid(as_uuid=True),
#         ForeignKey("users.id", ondelete="SET NULL"),
#         nullable=True,      # 🔑 optional
#         index=True
#     )
    
#     # number = Column(Integer, nullable=False)
#     # order = mapped_column(Integer, nullable=False, index=True)
#     title: Mapped[str] = mapped_column(String(200), nullable=False)
#     description: Mapped[str | None] = mapped_column(Text)
#     content: Mapped[str | None] = mapped_column(Text)  # Main lesson content
    
#     # Lesson Details
#     date = mapped_column(Date, nullable=False)
#     order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # Order in course
#     duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
#     is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
#     # Assessment/Assignment Configuration
#     has_assessment: Mapped[bool] = mapped_column(Boolean, default=True)
#     has_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    
#     # Relationships
#     course: Mapped["Course"] = relationship(
#         "Course",
#         back_populates="lessons"
#     )
    
#     modules = relationship("Module", back_populates="lessons")

#     # for actual assessment content[assign, assess, exam]
#     assessments: Mapped[List["Assessment"]] = relationship(
#         "Assessment",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )
    
#     # for scoring
#     scores: Mapped[List["Score"]] = relationship(
#         "Score",
#         back_populates="lesson"
#     )
    
#     attendance: Mapped[List["Attendance"]] = relationship(
#         "Attendance",
#         back_populates="lesson"
#     )
    
#     reviews: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )
    
#     creator: Mapped["User"] = relationship(
#         "User",
#         foreign_keys=[created_by]
#     )

#     def get_summary(self, include_relations: bool = False):
#         data = {
#             "id": self.id,
#             "title": self.title,
#             "order": self.order,
#             "duration_minutes": self.duration_minutes,
#             # "is_active": self.is_active,
#             "created_at": self.created_at,
#         }

#         if include_relations:
#             data["course"] = {
#                 "id": self.course.id,
#                 "title": self.course.title,
#                 "description": self.course.description,
#             }

#         return data
    





# v2
# # FILE: app/models/lesson.py

# # MUST be first line
# from __future__ import annotations

# from sqlalchemy import String, Integer, Float, Date, Text, UniqueConstraint, Uuid
# from sqlalchemy import ForeignKey, CheckConstraint
# from sqlalchemy.orm import relationship, Mapped, mapped_column
# from datetime import date as Date
# from typing import Optional
# from uuid import UUID

# from app.db.base_class import Base
# from app.db.mixins import UUIDMixin, TimestampMixin

# class Lesson(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "lessons"
    
#     # Relationships
#     module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))
#     module: Mapped["Module"] = relationship("Module", back_populates="lessons")
    
#     # Lesson details
#     title: Mapped[str] = mapped_column(String(200), nullable=False)
#     order: Mapped[int] = mapped_column(Integer, nullable=False)
#     date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)  # Fix: Should be nullable
#     description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     assessment_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
#     assignment_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
#     # Status
#     status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    
#     # Relationships
#     scores: Mapped[list["Score"]] = relationship(
#         "Score",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )
    
#     attendance_records: Mapped[list["Attendance"]] = relationship(
#         "Attendance",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )
    
#     __table_args__ = (
#         CheckConstraint(
#             "assessment_max >= 0", 
#             name="check_assessment_max_positive"
#         ),
#         CheckConstraint(
#             "assignment_max >= 0", 
#             name="check_assignment_max_positive"
#         ),
#         CheckConstraint(
#             "number >= 1", 
#             name="check_lesson_number_positive"
#         ),
#     )
    
#     def get_summary(self, include_module: bool = False) -> dict:
#         """
#         Return lesson summary as dictionary.
#         """
#         data = {
#             "id": str(self.id),
#             "module_id": str(self.module_id),
#             "title": self.title,
#             "order": self.order,
#             "date": self.date.isoformat() if self.date else None,
#             "description": self.description,
#             "assessment_max": self.assessment_max,
#             "assignment_max": self.assignment_max,
#             "status": self.status,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#         }
        
#         if include_module and self.module:
#             data["module"] = {
#                 "id": str(self.module.id),
#                 "title": self.module.title,
#                 "course_id": str(self.module.course_id)
#             }
        
#         return data

# # FILE: app/models/lesson.py

# from datetime import date
# from typing import Optional
# from uuid import UUID

# from sqlalchemy import (
#     String,
#     Integer,
#     Float,
#     Text,
#     Date as SQLADate,
#     ForeignKey,
#     CheckConstraint,
# )
# from sqlalchemy.orm import relationship, Mapped, mapped_column

# from app.db.base_class import Base
# from app.db.mixins import UUIDMixin, TimestampMixin


# class Lesson(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "lessons"

#     # -------------------------
#     # Relationships
#     # -------------------------
#     __table_args__ = (UniqueConstraint('course_id', 'order', name='uq_course_lesson'),)
#     __table_args__ = (UniqueConstraint('module_id', 'order', name='uq_module_lesson'),)

#     course_id: Mapped[UUID] = mapped_column(
#         Uuid(as_uuid=True), 
#         ForeignKey('courses.id', ondelete='CASCADE'),
#         nullable=False,
#         index=True
#     )
#     course: Mapped["Course"] = relationship(
#         "Course",
#         back_populates="lessons"
#     )
    
#     module_id: Mapped[UUID] = mapped_column(
#         ForeignKey("modules.id", ondelete="CASCADE"),
#         nullable=False,
#     )

#     module: Mapped["Module"] = relationship(
#         "Module",
#         back_populates="lessons",
#     )
    
#     # Optional creator
#     created_by = mapped_column(
#         Uuid(as_uuid=True),
#         ForeignKey("users.id", ondelete="SET NULL"),
#         nullable=True,      # optional
#         index=True
#     )
#     creator: Mapped["User"] = relationship(
#         "User",
#         foreign_keys=[created_by]
#     )
#     # -------------------------
#     # Lesson details
#     # -------------------------
#     title: Mapped[str] = mapped_column(String(200), nullable=False)

#     order: Mapped[int] = mapped_column(
#         Integer,
#         nullable=False,
#     )

#     date: Mapped[Optional[date]] = mapped_column(
#         SQLADate,
#         nullable=True,
#     )

#     description: Mapped[Optional[str]] = mapped_column(
#         Text,
#         nullable=True,
#     )

#     assessment_max: Mapped[Optional[float]] = mapped_column(
#         Float,
#         nullable=True,
#     )

#     assignment_max: Mapped[Optional[float]] = mapped_column(
#         Float,
#         nullable=True,
#     )

#     # -------------------------
#     # Status
#     # -------------------------
#     status: Mapped[str] = mapped_column(
#         String(20),
#         default="draft",
#         nullable=False,
#     )

#     # -------------------------
#     # Related entities
#     # -------------------------
#     scores: Mapped[list["Score"]] = relationship(
#         "Score",
#         back_populates="lesson",
#         cascade="all, delete-orphan",
#     )

#     attendance: Mapped[list["Attendance"]] = relationship(
#         "Attendance",
#         back_populates="lesson",
#         cascade="all, delete-orphan",
#     )
    
#     # 
#     # for actual assessment content[assign, assess, exam]
#     assessments: Mapped[list["Assessment"]] = relationship(
#         "Assessment",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )
    
#     # for scoring
#     # scores: Mapped[List["Score"]] = relationship(
#     #     "Score",
#     #     back_populates="lesson"
#     # )
    
#     # attendance: Mapped[List["Attendance"]] = relationship(
#     #     "Attendance",
#     #     back_populates="lesson"
#     # )
    
#     reviews: Mapped[list["Review"]] = relationship(
#         "Review",
#         back_populates="lesson",
#         cascade="all, delete-orphan"
#     )


#     # -------------------------
#     # Constraints
#     # -------------------------
#     __table_args__ = (
#         CheckConstraint(
#             "assessment_max >= 0",
#             name="check_assessment_max_positive",
#         ),
#         CheckConstraint(
#             "assignment_max >= 0",
#             name="check_assignment_max_positive",
#         ),
#         CheckConstraint(
#             '"order" >= 1',
#             name="check_lesson_order_positive",
#         ),
#     )

#     # -------------------------
#     # Helpers
#     # -------------------------
#     def get_summary(self, include_module: bool = False) -> dict:
#         return {
#             "id": str(self.id),
#             "module_id": str(self.module_id),
#             "title": self.title,
#             "order": self.order,
#             "date": self.date.isoformat() if self.date else None,
#             "description": self.description,
#             "assessment_max": self.assessment_max,
#             "assignment_max": self.assignment_max,
#             "status": self.status,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#             **(
#                 {
#                     "module": {
#                         "id": str(self.module.id),
#                         "title": self.module.title,
#                         "course_id": str(self.module.course_id),
#                     }
#                 }
#                 if include_module and self.module
#                 else {}
#             ),
#         }






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
        
