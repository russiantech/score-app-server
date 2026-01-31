# # app/models/attendance.py
# from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# import enum

# from app.db.base_class import Base
# from app.db.mixins import TimestampMixin

# class AttendanceStatus(str, enum.Enum):
#     PRESENT = "present"
#     ABSENT = "absent"
#     LATE = "late"
#     EXCUSED = "excused"

# class Attendance(TimestampMixin, Base):
#     __tablename__ = "attendance"
#     __table_args__ = (UniqueConstraint('enrollment_id', 'lesson_id', 'date', name='uq_attendance'),)
    
#     id = Column(Integer, primary_key=True, index=True)
#     enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
#     lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
#     status = Column(SQLEnum(AttendanceStatus), nullable=False)
#     date = Column(Date, nullable=False, index=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
#     # Relationships
#     enrollment = relationship("Enrollment", back_populates="attendance")
#     lesson = relationship("Lesson", back_populates="attendance")

# v2

# app/models/attendance.py
from sqlalchemy import DateTime, Enum, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import Optional
import uuid
from datetime import datetime

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.schemas.attendance import AttendanceStatus

class Attendance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("lesson_id", "student_id", name="uq_lesson_student_attendance"),
    )
    
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('enrollments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('lessons.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), 
        nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Additional Information
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        back_populates="attendance"
    )
    
    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="attendance"
    )
    
    student: Mapped["User"] = relationship(
        "User",
        back_populates="attendance_records",
        foreign_keys=[student_id]
    )
    
    recorder: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recorded_by]
    )

