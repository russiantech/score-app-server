# ============================================================================
# BACKEND - MODEL (models/parents.py)
# ============================================================================

from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, Text, Enum as SQLAEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.schemas.parent import LinkStatus, RelationshipType

class ParentChildren(UUIDMixin, TimestampMixin, Base):
    """
    Represents the relationship between a parent/guardian and a child / student.
    Both are users in the system (self-referential many-to-many).
    """
    
    __tablename__ = "parent_children"

    # Foreign Keys
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID of the parent/guardian"
    )
    
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID of the child / student"
    )
    
    # Relationship Details
    
    # relationship = Column(
    #     SQLAEnum(RelationshipType),
    #     default=RelationshipType.GUARDIAN,
    #     nullable=False,
    #     comment="Type of relationship"
    # )
    # This avoids conflicts with sqlAlchemy's `relationship`
    relationship_type = Column(
        SQLAEnum(RelationshipType),
        default=RelationshipType.GUARDIAN,
        nullable=False,
        comment="Type of parent-child relationship"
    )
    
    status = Column(
        SQLAEnum(LinkStatus),
        default=LinkStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates if this is the primary guardian"
    )
    
    # Additional Fields
    notes = Column(Text, nullable=True)
    linked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    suspended_reason = Column(String(500), nullable=True)
    
    # Relationships
    parent = relationship(
        "User",
        foreign_keys=[parent_id],
        back_populates="children",
        lazy="joined"
    )
    
    child = relationship(
        "User",
        foreign_keys=[child_id],
        back_populates="parents",
        lazy="joined"
    )
    
    linker = relationship(
        "User",
        foreign_keys=[linked_by],
        lazy="select"
    )

    def __repr__(self):
        return f"<ParentChildren(id={self.id}, parent_id={self.parent_id}, child_id={self.child_id}, relationship={self.relationship_type})>"

    def get_summary(self, include_relations: bool = False) -> dict:
        """Get a summary representation of the link."""
        data = {
            "id": str(self.id),
            "parent_id": str(self.parent_id),
            "child_id": str(self.child_id),
            "relationship": self.relationship_type.value if self.relationship_type else None,
            "status": self.status.value if self.status else None,
            "is_primary": self.is_primary,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "suspended_at": self.suspended_at.isoformat() if self.suspended_at else None,
        }

        if include_relations:
            if self.parent:
                data["parent"] = {
                    "id": str(self.parent.id),
                    "names": self.parent.names,
                    "email": self.parent.email,
                    "is_active": self.parent.is_active,
                }
            
            if self.child:
                data["child"] = {
                    "id": str(self.child.id),
                    "names": self.child.names,
                    "email": self.child.email,
                    "is_active": self.child.is_active,
                }

        return data

    def is_active(self) -> bool:
        """Check if the link is active"""
        return self.status == LinkStatus.ACTIVE

    def activate(self):
        """Activate the link"""
        self.status = LinkStatus.ACTIVE
        self.suspended_at = None
        self.suspended_reason = None

    def suspend(self, reason: str = None):
        """Suspend the link"""
        self.status = LinkStatus.SUSPENDED
        self.suspended_at = datetime.now()
        self.suspended_reason = reason

    __table_args__ = (
        # Ensure only one primary guardian per student
        Index(
            'uq_one_primary_parent_per_child',
            child_id,
            is_primary,
            unique=True,
            postgresql_where=(is_primary == True)
        ),
        # Prevent duplicate links
        Index('uq_parent_child_pair', parent_id, child_id, unique=True),
    )



