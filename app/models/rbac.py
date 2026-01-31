# app/models/rbac.py
from typing import List
from sqlalchemy import (
    Column, String, Boolean, Text
)

from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import List, Optional

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
# from app.models.user import User  # partially initialized
from app.models.association_tables import user_roles, role_permissions

# Optional: organization-level role membership
class Role(UUIDMixin, TimestampMixin, Base): # ← INHERIT mixin first
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # e.g. "admin", "instructor"
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Optional org fields if you want tenant-aware roles
    org_id = Column(Uuid(as_uuid=True), nullable=True, index=True)  # null => global role

    # Relationships
    user: Mapped[List["User"]] = relationship(
        "User", 
        secondary=user_roles,
        back_populates="roles"
    )
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    
    def get_summary(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class Permission(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "permissions"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., 'user', 'course', 'score'
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., 'create', 'read', 'update', 'delete'
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin"
    )

# Association tables are defined in app/models/association_tables.py