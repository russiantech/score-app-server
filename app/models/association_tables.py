# # app/models/association_tables.py

# from sqlalchemy import Boolean, Column, ForeignKey, String, Table, DateTime
# from sqlalchemy import Uuid
# from sqlalchemy.sql import func

# from app.db.base_class import Base

# user_roles = Table(
#     "user_roles",
#     Base.metadata,
#     Column("user_id", Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
#     Column("role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
#     Column("created_at", DateTime, server_default=func.now()),
# )

# # Association table between roles and permissions
# role_permissions = Table(
#     "role_permissions",
#     Base.metadata,
#     Column("role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
#     Column("permission_id", Uuid(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
# )

# # Course instructors association table
# course_tutors = Table(
#     "course_tutors",
#     Base.metadata,
#     Column("course_id", Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
#     Column("instructor_id", Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
# )


# # Association table for parent-student relationships
# # parent_students = Table(
# #     'parent_students',
# #     Base.metadata,
# #     Column('parent_id', Uuid(as_uuid=True), ForeignKey('parents.id'), primary_key=True),
# #     Column('student_id', Uuid(as_uuid=True), ForeignKey('students.id'), primary_key=True),
# #     Column('relationship', String(50)),  # "biological", "legal_guardian", "adoptive"
# #     Column('is_primary', Boolean, default=False)
# # )

# # CORRECTED: Association table for parent-student relationships
# # Since both are in users table, we use self-referential foreign keys
# parent_students = Table(
#     'parent_students',
#     Base.metadata,
#     Column('parent_id', Uuid(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
#     Column('student_id', Uuid(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
#     Column('relationship', String(50), default="guardian"),  # "biological", "legal_guardian", "adoptive"
#     Column('is_primary', Boolean, default=False),
#     Column('created_at', DateTime, server_default=func.now()),
# )

# course_categories = Table(
#     "course_categories",
#     Base.metadata,
#     Column("course_id", Uuid(as_uuid=True), ForeignKey("courses.id"), primary_key=True),
#     Column("category_id", Uuid(as_uuid=True), ForeignKey("categories.id"), primary_key=True),
# )


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
# COURSE TUTORS ASSOCIATION
# ============================================================================
# course_tutors = Table(
#     "course_tutors",
#     Base.metadata,
#     Column(
#         "course_id", 
#         Uuid(as_uuid=True), 
#         ForeignKey("courses.id", ondelete="CASCADE"), 
#         primary_key=True,
#         nullable=False
#     ),
#     Column(
#         "tutor_id", 
#         Uuid(as_uuid=True), 
#         ForeignKey("users.id", ondelete="CASCADE"), 
#         primary_key=True,
#         nullable=False
#     ),
#     Column(
#         "created_at", 
#         DateTime(timezone=True), 
#         server_default=func.now(),
#         nullable=False
#     ),
#     Column(
#         "is_primary", 
#         Boolean, 
#         default=False,
#         nullable=False,
#         comment="Indicates if this tutor is the primary instructor for the course"
#     ),
# )


# # ============================================================================
# # PARENT-STUDENT ASSOCIATION (SELF-REFERENTIAL)
# # ============================================================================
# # Both parent and student are users, creating a self-referential many-to-many
# parent_students = Table(
#     "parent_students",
#     Base.metadata,
#     Column(
#         "parent_id", 
#         Uuid(as_uuid=True), 
#         ForeignKey("users.id", ondelete="CASCADE"), 
#         primary_key=True,
#         nullable=False,
#         comment="User ID of the parent/guardian"
#     ),
#     Column(
#         "student_id", 
#         Uuid(as_uuid=True), 
#         ForeignKey("users.id", ondelete="CASCADE"), 
#         primary_key=True,
#         nullable=False,
#         comment="User ID of the student"
#     ),
#     Column(
#         "relationship", 
#         String(50), 
#         default="guardian",
#         nullable=False,
#         comment="Type of relationship: guardian, biological, adoptive, legal_guardian, etc."
#     ),
#     Column(
#         "is_primary", 
#         Boolean, 
#         default=False,
#         nullable=False,
#         comment="Indicates if this is the primary guardian"
#     ),
#     Column(
#         "created_at", 
#         DateTime(timezone=True), 
#         server_default=func.now(),
#         nullable=False
#     ),
#     Column(
#         "notes",
#         String(500),
#         nullable=True,
#         comment="Additional notes about the relationship"
#     ),
# )


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

