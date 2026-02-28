
# v2
# app/models/association_tables.py
"""
Association tables for many-to-many relationships.
All tables use UUID for foreign keys and include proper cascade behavior.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, DateTime
from sqlalchemy import Uuid
from sqlalchemy.sql import func

from app.db.base_class import Base


# ============================================================================
# USER ROLES ASSOCIATION
# ============================================================================
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", 
        Uuid(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "role_id", 
        Uuid(as_uuid=True), 
        ForeignKey("roles.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "created_at", 
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    ),
)


# ============================================================================
# ROLE PERMISSIONS ASSOCIATION
# ============================================================================
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", 
        Uuid(as_uuid=True), 
        ForeignKey("roles.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "permission_id", 
        Uuid(as_uuid=True), 
        ForeignKey("permissions.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "granted_at", 
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    ),
)

# ============================================================================
# COURSE CATEGORIES ASSOCIATION
# ============================================================================
course_categories = Table(
    "course_categories",
    Base.metadata,
    Column(
        "course_id", 
        Uuid(as_uuid=True), 
        ForeignKey("courses.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "category_id", 
        Uuid(as_uuid=True), 
        ForeignKey("categories.id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False
    ),
    Column(
        "created_at", 
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    ),
)


# ============================================================================
# INDEX DEFINITIONS (Optional but recommended for performance)
# ============================================================================
# SQLAlchemy will automatically create indexes on foreign keys,
# but you can add additional indexes if needed:

# Example:
# from sqlalchemy import Index
# 
# Index('idx_parent_students_parent', parent_students.c.parent_id)
# Index('idx_parent_students_student', parent_students.c.student_id)
# Index('idx_course_instructors_course', course_tutors.c.course_id)
# Index('idx_course_instructors_instructor', course_tutors.c.instructor_id)

