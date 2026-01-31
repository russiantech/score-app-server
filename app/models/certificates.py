
# app/models/certificate.py
from datetime import date
from typing import Optional
import uuid
from sqlalchemy import Boolean, Date, Float, String, ForeignKey, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import mapped_column, relationship, Mapped
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class Certificate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("student_id", "enrollment_id", name="uq_certificate"),
    )
    
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('enrollments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Certificate Details
    certificate_number: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Digital Certificate
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500))
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Verification
    verification_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Performance Information (optional)
    final_score: Mapped[Optional[float]] = mapped_column(Float)
    overall_grade: Mapped[Optional[str]] = mapped_column(String(5))
    completion_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        back_populates="certificates"
    )
    
    student: Mapped["User"] = relationship(
        "User",
        back_populates="certificates",
        foreign_keys=[student_id]
    )
    
    issuer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[issued_by]
    )
    

# class Certificate(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "certificates"
#     __table_args__ = (
#         UniqueConstraint("student_id", "course_id", name="uq_certificate"),
#     )

#     student_id = mapped_column(ForeignKey("users.id"), nullable=False)
#     course_id = mapped_column(ForeignKey("courses.id"), nullable=False)

#     issued_at = mapped_column(DateTime, server_default=func.now())
#     certificate_url = mapped_column(String(500))

#     student = relationship("User", back_populates="certificates")
#     course = relationship("Course")

