
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

