
# # v2
# # app/models/enrollment.py
# from sqlalchemy import Column, DateTime, String, Enum, ForeignKey, func, UniqueConstraint
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import Uuid
# from typing import List, Optional
# import enum
# import uuid
# from datetime import datetime

# from app.db.base_class import Base
# from app.db.mixins import TimestampMixin, UUIDMixin

# class EnrollmentStatus(enum.Enum):
#     PENDING = "pending"
#     ACTIVE = "active"
#     COMPLETED = "completed"
#     WITHDRAWN = "withdrawn"
#     SUSPENDED = "suspended"

# class Enrollment(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "enrollments"
#     __table_args__ = (
#         UniqueConstraint("student_id", "course_id", name="uq_student_course"),
#     )

#     student_id = mapped_column(
#         Uuid(as_uuid=True),
#         ForeignKey("users.id", ondelete="CASCADE"),
#         nullable=False
#     )

#     course_id = mapped_column(
#         Uuid(as_uuid=True),
#         ForeignKey("courses.id", ondelete="CASCADE"),
#         nullable=False
#     )

#     # status = mapped_column(
#     #     Enum("active", "completed", "withdrawn", name="enrollment_status"),
#     #     default="active"
#     # )
#     status: Mapped[EnrollmentStatus] = mapped_column(
#         Enum(EnrollmentStatus), 
#         default=EnrollmentStatus.ACTIVE
#     )
    
#     # Session/Term Information
#     # session: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Fall 2024"
#     # term: Mapped[str | None] = mapped_column(String(50))

#     enrolled_by = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
#     enrolled_at = mapped_column(DateTime, server_default=func.now())

#     student = relationship("User", back_populates="enrollments")
#     course = relationship("Course", back_populates="enrollments")

#     attendance = relationship(
#         "Attendance",
#         back_populates="enrollment",
#         cascade="all, delete-orphan"
#     )

#     certificates: Mapped[List["Certificate"]] = relationship(
#         "Certificate",
#         back_populates="enrollment",
#         cascade="all, delete-orphan"
#     )
    
#     review: Mapped[Optional["Review"]] = relationship(
#         "Review",
#         back_populates="enrollment",
#         uselist=False,
#         cascade="all, delete-orphan"
#     )
     
#     def get_summary(self, **args):
#         data = {
#             'id': self.id,
#         }
#         return data

    

# app/models/enrollment.py
from sqlalchemy import Column, DateTime, String, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import List, Optional
import enum
import uuid
from datetime import datetime

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.scores import Score
# from app.models.attendance import Attendance
# from app.models.certificate import Certificate
# from app.models.course import Course
# from app.models.user import User

class EnrollmentStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    SUSPENDED = "suspended"

class Enrollment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "enrollments"
    
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), 
        default=EnrollmentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    
    # Session/Term Information
    session: Mapped[str] = mapped_column(String(50), nullable=False, default="2026/2027")
    term: Mapped[str] = mapped_column(String(50), nullable=False, default="Q1.2026")
    
    # Enrollment Dates
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # The real relationship (FK → users)
    student: Mapped["User"] = relationship(
        "User",
        back_populates="enrollments",
        foreign_keys=[student_id]
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="enrollments"
    )
    
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    
    attendance: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    
    certificates: Mapped[List["Certificate"]] = relationship(
        "Certificate",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    
    review: Mapped[Optional["Review"]] = relationship(
        "Review",
        back_populates="enrollment",
        uselist=False,
        cascade="all, delete-orphan"
    )
     
    # def get_summary(self, **args):
    #     data = {
    #         'id': self.id,
    #         'enrolled_at': self.enrolled_at,
    #     }
    #     return data
    
    def get_summary(self, include_relations=False) -> dict:
        """
        Return enrollment data as a dictionary.
        Set include_relations=True to include student/course summaries.
        """
        data = {
            "id": str(self.id),
            "student_id": str(self.student_id),
            "course_id": str(self.course_id),
            "session": self.session,
            "term": self.term,
            "status": self.status.value if self.status else None,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "completed_date": (
                self.completed_date.isoformat() if self.completed_date else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Optionally include related objects (avoid circular refs)
        if include_relations:
            if self.student:
                data["student"] = {
                    "id": str(self.student.id),
                    "names": self.student.names,
                    "email": self.student.email,
                }
            if self.course:
                data["course"] = {
                    "id": str(self.course.id),
                    "code": self.course.code,
                    "title": self.course.title,
                }
        
        return data

