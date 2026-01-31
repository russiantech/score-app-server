# ============================================================================
# MODEL - Tutor Assignment
# FILE: app/models/tutors.py
# ============================================================================

from sqlalchemy import Boolean, Column, Index, DateTime, ForeignKey, Text, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.schemas.tutors import CourseTutorStatus

class CourseTutor(UUIDMixin, TimestampMixin, Base):
    """
    Represents the assignment of a tutor to a course.
    A tutor can be assigned to multiple courses.
    A course can have multiple tutors assigned.
    """
    
    __tablename__ = "course_tutors"

    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    tutor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status = Column(
        SQLAEnum(CourseTutorStatus),
        default=CourseTutorStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Timestamps
    revoked_at = Column(DateTime, nullable=True)
    
    # Additional fields
    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates if this tutor is the primary instructor for the course"
    )
    notes = Column(Text, nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tutor = relationship(
        "User",
        foreign_keys=[tutor_id],
        back_populates="courses_assigned",
        lazy="joined"
    )
    course = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="tutors_assigned",
        lazy="joined"
    )
    
    assigner = relationship(
        "User",
        foreign_keys=[assigned_by],
        lazy="select"
    )

    def __repr__(self):
        return f"<CourseTutor(id={self.id}, tutor_id={self.tutor_id}, course_id={self.course_id}, status={self.status})>"

    def get_summary(self, include_relations: bool = False) -> dict:
        """
        Get a summary representation of the assignment.
        
        Args:
            include_relations: Whether to include full tutor and course details
        """
        data = {
            "id": str(self.id),
            "tutor_id": str(self.tutor_id),
            "course_id": str(self.course_id),
            "status": self.status.value,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }

        if include_relations:
            if self.tutor:
                data["tutor"] = {
                    "id": str(self.tutor.id),
                    "names": self.tutor.names,
                    "email": self.tutor.email,
                    "is_active": self.tutor.is_active,
                }
            
            if self.course:
                data["course"] = {
                    "id": str(self.course.id),
                    "code": self.course.code,
                    "title": self.course.title,
                    "description": self.course.description,
                    "is_active": self.course.is_active,
                    "enrolledStudents": len(self.course.enrollments) if hasattr(self.course, 'enrollments') else 0,
                }

        return data

    def is_active(self) -> bool:
        """Check if the assignment is active"""
        return self.status == CourseTutorStatus.ACTIVE

    def activate(self):
        """Activate the assignment"""
        self.status = CourseTutorStatus.ACTIVE
        self.revoked_at = None

    def deactivate(self):
        """Deactivate the assignment"""
        self.status = CourseTutorStatus.INACTIVE

    def revoke(self):
        """Revoke the assignment"""
        self.status = CourseTutorStatus.REVOKED
        self.revoked_at = datetime.now()
    
     # We might want to add a constraint that only one tutor per course can be primary.
    # This can be done with a unique constraint on (course_id, is_primary) where is_primary=True.
    # However, note that the condition in the unique constraint is not supported by all databases.
    # Alternatively, we can handle it in the application logic or use a partial index (if using PostgreSQL).

    __table_args__ = (
        # This creates a partial unique index for PostgreSQL, ensuring only one primary tutor per course.
        # For other databases, we might need a different approach.
        Index(
            'uq_one_primary_tutor_per_course',
            course_id,
            is_primary,
            unique=True,
            postgresql_where=(is_primary == True)
        ),
    )
    


