
# # v2
# # app/models/user.py
# from sqlalchemy import DateTime, String, Boolean, Text
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from typing import Optional, List
# from datetime import datetime
# from sqlalchemy import CheckConstraint, or_

# from app.core.security.password import hash_password, verify_password
# from app.db.mixins import UUIDMixin
# from app.db.mixins import TimestampMixin
# from app.db.base_class import Base
# from app.models.association_tables import user_roles, course_tutors, parent_students
# # from app.models.association_tables import  users_categories # Not applicable now - do not remove just yet. Might be useful later.

# class User(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "users"

#     # Personal Information
#     username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
#     email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
#     password: Mapped[str] = mapped_column(String(255), nullable=False)
#     names: Mapped[str | None] = mapped_column(String(50))
#     # last_name: Mapped[str] = mapped_column(String(50), nullable=False)
#     phone: Mapped[str | None] = mapped_column(String(20), unique=True)
#     ip: Mapped[str | None] = mapped_column(String(50))
    
#     # Account Status
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
#     email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
#     phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
#     # Profile Information
#     avatar_url: Mapped[str | None] = mapped_column(String(500))
#     bio: Mapped[str | None] = mapped_column(Text)
#     dob: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
#     password_changed_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=True,
#     )
    
#     """ 
#         favorites = db.relationship('Favorite', back_populates='users', lazy='dynamic')
#     favorite_lists = db.relationship('FavoriteList', back_populates='users', lazy='dynamic')

    
#     """
#     # Relationships

#     # Keeps track of user's payments
#     payments: Mapped[List["Payment"]] = relationship(
#         "Payment",
#         back_populates="user",
#     )
    
#     # Keeps track of user's saved payment modes
#     payment_modes: Mapped[List["PaymentModes"]] = relationship(
#         "PaymentModes",
#         back_populates="user",
#     )
        
#     # Keeps track of user's subscriptions
#     subscriptions: Mapped[List["Subscription"]] = relationship(
#         "Subscription",
#         back_populates="user",
#     )
    
#     # Keeps track of user's subscriptions
#     addresses = relationship('Address', back_populates='user', lazy='selectin')
    
#     # favorites: Mapped[List["Favorite"]] = relationship(
#     #     back_populates="user",
#     #     lazy="selectin",
#     #     cascade="all, delete-orphan",
#     # )
    
#     avatar: Mapped[list["UserAvatar"]] = relationship(
#         back_populates="user",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#         order_by="UserAvatar.created_at",
#     )
    
#     # Student profile (if user is a student)
#     student = relationship(
#         "Student",
#         back_populates="user",
#         uselist=False,
#         cascade="all, delete-orphan",
#         lazy="selectin"
#     )
#     # Parent profile (if user is a parent)
#     # parents = relationship(
#     #     "Parent", 
#     #     back_populates="user", 
#     #     uselist=False,
#     #     lazy="selectin"
#     # )
#     # Parent-Student relationships (SELF-REFERENTIAL)
#     # Students linked to this user (if user is a parent)
#     # children = relationship(
#     #     "User",
#     #     secondary="parent_students",
#     #     primaryjoin=lambda: User.id == parent_students.c.parent_id,
#     #     secondaryjoin=lambda: User.id == parent_students.c.student_id,
#     #     backref="parents",  # This creates the reverse relationship
#     #     lazy="selectin"
#     # )
    
#     # Parent -> Students
#     students = relationship(
#         "User",
#         secondary=parent_students,
#         primaryjoin=id == parent_students.c.parent_id,
#         secondaryjoin=id == parent_students.c.student_id,
#         back_populates="parents",
#     )

#     # Student -> Parents
#     parents = relationship(
#         "User",
#         secondary=parent_students,
#         primaryjoin=id == parent_students.c.student_id,
#         secondaryjoin=id == parent_students.c.parent_id,
#         back_populates="students",
#     )
    
#     # Relationships
#     roles: Mapped[List["Role"]] = relationship(
#         "Role", 
#         secondary=user_roles,
#         back_populates="user",
#         lazy="selectin"
#     )
    
#     # As a student
#     enrollments: Mapped[List["Enrollment"]] = relationship(
#         "Enrollment",
#         back_populates="student",
#         cascade="all, delete-orphan"
#     )
    
#     # As an instructor

#     # Courses this user teaches
#     courses_assigned: Mapped[list["Course"]] = relationship(
#         back_populates="instructors",
#         secondary=course_tutors,
#         lazy="selectin"
#     )
    
#     # As a parent (if applicable)

#     # Authored assessments/assignments
#     created_assessments: Mapped[List["Assessment"]] = relationship(
#         "Assessment",
#         back_populates="creator",
#         foreign_keys="Assessment.creator_id"
#     )
    
#     # Recorded scores
#     recorded_scores: Mapped[List["Score"]] = relationship(
#         "Score",
#         back_populates="recorder",
#         foreign_keys="Score.recorder_id"
#     )
    
#     # Comments / Reviews made
    
#     reviews_authored: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="author",
#         foreign_keys="Review.author_id",
#         cascade="all, delete-orphan"
#     )

#     reviews_received: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="instructor",
#         foreign_keys="Review.instructor_id"
#     )

#     helpful_votes: Mapped[List["ReviewHelpfulVote"]] = relationship(
#         "ReviewHelpfulVote",
#         back_populates="user",
#         cascade="all, delete-orphan"
#     )

#     review_reports: Mapped[List["ReviewReport"]] = relationship(
#         "ReviewReport",
#         back_populates="reporter",
#         foreign_keys="ReviewReport.reporter_id"
#     )
    
#     # Attendance records (if student)
#     attendance_records: Mapped[List["Attendance"]] = relationship(
#         "Attendance",
#         back_populates="student",
#         foreign_keys="Attendance.student_id"
#     )
    
#     # Certificates earned
#     certificates: Mapped[List["Certificate"]] = relationship(
#         "Certificate",
#         back_populates="student",
#         foreign_keys="Certificate.student_id"
#     )

#     contact_info: Mapped["ContactInfo"] = relationship(
#         back_populates="user",
#         cascade="all, delete-orphan",
#         uselist=False,
#     )
    
#     location_info: Mapped["Location"] = relationship(
#         back_populates="user",
#         cascade="all, delete-orphan",
#         uselist=False,
#     )
    
#     # Add database-level constraints
#     __table_args__ = (
#         CheckConstraint(
#             "email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'",
#             name='valid_email_format'
#         ),
#         CheckConstraint(
#             "phone ~ '^[0-9]{10,15}$'",
#             name='valid_phone_format'
#         ),
#         CheckConstraint(
#             "username ~ '^[a-zA-Z0-9_]{3,30}$'",
#             name='valid_username_format'
#         ),
#         CheckConstraint(
#             "length(password) >= 60",  # Hashed passwords should be at least 60 chars
#             name='hashed_password_length'
#         ),
#         CheckConstraint(
#             "name IS NULL OR (name ~ '^[a-zA-Z\\s''\\-]{2,100}$' AND length(trim(name)) >= 2)",
#             name='valid_name_format'
#         ),
#     )
    
#     @staticmethod
#     def get_user(username: str, db) -> Optional["User"]:
#         """
#         Static method to fetch a user from the database by username or user ID.
        
#         Args:
#             username (str): The username or user ID to search for.
        
#         Returns:
#             User: The user object if found, otherwise None.
        
#         Raises:
#             ValueError: If the username is empty.
#         """
#         if not username:
#             raise ValueError("Username cannot be empty")
        
#         # Attempt to fetch the user by either username or user ID
#         user = db.session.query(User).filter(or_(User.username == username, User.email == username, User.phone == username, User.id == username)).first()
        
#         return user

#     def set_password(self, password: str) -> None:
#         """Hashes the password using bcrypt/scrypt and stores it."""
#         if not password:
#             raise ValueError("Password cannot be empty")
#         self.password = hash_password(password)

#     def check_password(self, password: str) -> bool:
#         """Checks the hashed password using bcrypt."""
#         if self.password is None:
#             # return False
#             raise ValueError(f"Password not set for this user [{self.username}].")
#         return verify_password(self.password, password)
    
#     # Properties for convenience
#     @property
#     def full_name(self) -> str:
#         return f"{self.names}"

#     # default roles
#     @property
#     def default_roles(self) -> List[str]:
#         return ['user', 'student']
    
#     @property
#     def role_names(self) -> List[str]:
#         """Get list of role names for this user."""
#         if not self.roles:
#             return self.default_roles
#         return [role.name for role in self.roles]
    
#     @property
#     def is_admin(self) -> bool:
#         """Check if user has admin role."""
#         if not self.roles:
#             return False
#         return any(role.name.lower() == 'admin' for role in self.roles)

#     @property
#     def is_superuser(self) -> bool:
#         """Check if user has superuser role."""
#         if not self.roles:
#             return False
#         return any(role.name == 'superuser' for role in self.roles)
    
#     @property
#     def is_tutor(self) -> bool:
#         if not self.roles:
#             return False
#         return any(role.name.lower() == 'tutor' for role in self.roles)

#     @property
#     def is_student(self) -> bool:
#         if not self.roles:
#             return False
#         return any(role.name.lower() == 'student' for role in self.roles)

#     @property
#     def is_parent(self) -> bool:
#         if not self.roles:
#             return False
#         return any(role.name.lower() == 'parent' for role in self.roles)

#     # def has_role(self, role_name: str) -> bool:
#     #     if not self.roles:
#     #         return False
#     #     return any(role.name.lower() == role_name.lower() for role in self.roles)
    
#     def has_role(self, *role_names: str) -> bool:
#         """Check if user has any of the given roles."""
#         if not self.roles:
#             return False
#         role_names_lower = [r.lower() for r in role_names]
#         return any(role.name.lower() in role_names_lower for role in self.roles)


#     def has_permission(self, permission_name: str) -> bool:
#         if not self.roles:
#             return False
#         for role in self.roles:
#             for permission in role.permissions:
#                 if permission.name == permission_name:
#                     return True
#         return False

#     def get_summary(self) -> dict:
#         """Get user summary for API responses."""
#         data =  {
#             "id": str(self.id),
#             "username": self.username,
#             "email": self.email,
#             "names": self.names,
#             "phone": self.phone,
#             "is_active": self.is_active,
#             "is_verified": self.is_verified,
#             "roles": self.role_names,
#             "addresses": [address.get_summary() for address in self.addresses] if self.addresses else [],
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#         }
#         return data




# v2
# app/models/user.py
from sqlalchemy import DateTime, String, Boolean, Text, CheckConstraint, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime

from app.core.security.password import hash_password, verify_password
from app.db.mixins import UUIDMixin, TimestampMixin
from app.db.base_class import Base
from app.models.association_tables import (
    user_roles, 
    # parent_students
)
from app.models.tutors import CourseTutorStatus


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # ========================================================================
    # PERSONAL INFORMATION
    # ========================================================================
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    names: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    ip: Mapped[str | None] = mapped_column(String(50))
    
    # ========================================================================
    # ACCOUNT STATUS
    # ========================================================================
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # ========================================================================
    # PROFILE INFORMATION
    # ========================================================================
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    dob: Mapped[Optional[datetime]] = mapped_column(DateTime)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # ========================================================================
    # PAYMENT & SUBSCRIPTION RELATIONSHIPS
    # ========================================================================
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    payment_modes: Mapped[List["PaymentModes"]] = relationship(
        "PaymentModes",
        back_populates="user",
        cascade="all, delete-orphan"
    )
        
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # ========================================================================
    # PROFILE ASSETS
    # ========================================================================
    avatar: Mapped[List["UserAvatar"]] = relationship(
        "UserAvatar",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="UserAvatar.created_at"
    )
    
    contact_info: Mapped[Optional["ContactInfo"]] = relationship(
        "ContactInfo",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin"
    )
    
    location_info: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin"
    )
    
    # ========================================================================
    # ROLE-SPECIFIC PROFILES
    # ========================================================================
    # student: Mapped[Optional["Student"]] = relationship(
    #     "Student",
    #     back_populates="user",
    #     uselist=False,
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )
    
    # ========================================================================
    # PARENT-STUDENT RELATIONSHIPS (SELF-REFERENTIAL)
    # ========================================================================
    # When this user is a PARENT: List of students they are guardian of
    # students: Mapped[List["User"]] = relationship(
    #     "User",
    #     secondary=parent_students,
    #     primaryjoin=lambda: User.id == parent_students.c.parent_id,
    #     secondaryjoin=lambda: User.id == parent_students.c.student_id,
    #     back_populates="parents",
    #     lazy="selectin"
    # )

    # # When this user is a STUDENT: List of parents/guardians
    # parents: Mapped[List["User"]] = relationship(
    #     "User",
    #     secondary=parent_students,
    #     primaryjoin=lambda: User.id == parent_students.c.student_id,
    #     secondaryjoin=lambda: User.id == parent_students.c.parent_id,
    #     back_populates="students",
    #     lazy="selectin"
    # )
    
    
    # Parent-Student Relationships (Self-referential)
    children = relationship(
        "ParentChildren",
        foreign_keys="ParentChildren.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    parents = relationship(
        "ParentChildren", 
        foreign_keys="ParentChildren.child_id",
        back_populates="child",
        cascade="all, delete-orphan"
    )
    
    # ========================================================================
    # ROLE & PERMISSIONS
    # ========================================================================
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=user_roles,
        back_populates="user",
        lazy="selectin"
    )
    
    # ========================================================================
    # COURSE RELATIONSHIPS
    # ========================================================================
    # As a STUDENT: Course enrollments
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan",
        foreign_keys="Enrollment.student_id"
    )
    
    # As an INSTRUCTOR: Courses taught
    # courses_assigned: Mapped[List["Course"]] = relationship(
    #     "Course",
    #     secondary="course_tutors",
    #     back_populates="tutors",
    #     lazy="selectin"
    # )
    courses_assigned = relationship(
        "CourseTutor",
        foreign_keys="CourseTutor.tutor_id",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    
    # Tutor → Course assignments (association objects)
    # courses_assigned: Mapped[List["CourseTutor"]] = relationship(
    #     "CourseTutor",
    #     back_populates="tutor",
    #     cascade="all, delete-orphan"
    # )

    # Convenience property (NO ORM magic here)
    @property
    def my_assigned_courses(self):
        return [
            assoc.course
            for assoc in self.courses_assigned
            if assoc.status != None
            # if assoc.status == CourseTutorStatus.ACTIVE
        ]

    
    # ========================================================================
    # ASSESSMENT & SCORING
    # ========================================================================
    created_assessments: Mapped[List["Assessment"]] = relationship(
        "Assessment",
        back_populates="creator",
        foreign_keys="Assessment.creator_id",
        cascade="all, delete-orphan"
    )
    
    recorded_scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="recorder",
        foreign_keys="Score.recorder_id",
        cascade="all, delete-orphan"
    )
    
    submissions = relationship(
        "Submission",
        back_populates="student",
        foreign_keys="[Submission.student_id]"
    )
    
    # ========================================================================
    # REVIEWS & FEEDBACK
    # ========================================================================
    reviews_authored: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="author",
        foreign_keys="Review.author_id",
        cascade="all, delete-orphan"
    )

    reviews_received: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="instructor",
        foreign_keys="Review.instructor_id"
    )

    helpful_votes: Mapped[List["ReviewHelpfulVote"]] = relationship(
        "ReviewHelpfulVote",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    review_reports: Mapped[List["ReviewReport"]] = relationship(
        "ReviewReport",
        back_populates="reporter",
        foreign_keys="ReviewReport.reporter_id",
        cascade="all, delete-orphan"
    )
    
    # ========================================================================
    # ATTENDANCE & CERTIFICATES
    # ========================================================================
    attendance_records: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="student",
        foreign_keys="Attendance.student_id",
        cascade="all, delete-orphan"
    )
    
    certificates: Mapped[List["Certificate"]] = relationship(
        "Certificate",
        back_populates="student",
        foreign_keys="Certificate.student_id",
        cascade="all, delete-orphan"
    )
    
    # ========================================================================
    # DATABASE CONSTRAINTS
    # ========================================================================
    __table_args__ = (
        CheckConstraint(
            "email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'",
            name='valid_email_format'
        ),
        CheckConstraint(
            "phone IS NULL OR phone ~ '^[+]?[0-9]{10,15}$'",
            name='valid_phone_format'
        ),
        CheckConstraint(
            "username ~ '^[a-zA-Z0-9_]{3,30}$'",
            name='valid_username_format'
        ),
        CheckConstraint(
            "length(password) >= 60",
            name='hashed_password_length'
        ),
        CheckConstraint(
            "names IS NULL OR (names ~ '^[a-zA-Z\\s''\\-]{2,100}$' AND length(trim(names)) >= 2)",
            name='valid_name_format'
        ),
    )
    
    # ========================================================================
    # STATIC METHODS
    # ========================================================================
    @staticmethod
    def get_user(username: str, db) -> Optional["User"]:
        """
        Fetch a user from the database by username, email, phone, or user ID.
        
        Args:
            username: The identifier to search for
            db: Database session
        
        Returns:
            User object if found, None otherwise
        
        Raises:
            ValueError: If username is empty
        """
        if not username:
            raise ValueError("Username cannot be empty")
        
        user = db.query(User).filter(
            or_(
                User.username == username,
                User.email == username,
                User.phone == username,
                User.id == username
            )
        ).first()
        
        return user

    # ========================================================================
    # PASSWORD METHODS
    # ========================================================================
    def set_password(self, password: str) -> None:
        """
        Hash and store the password.
        
        Args:
            password: Plain text password
        
        Raises:
            ValueError: If password is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")
        self.password = hash_password(password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
        
        Returns:
            True if password matches, False otherwise
        
        Raises:
            ValueError: If no password is set for user
        """
        if not self.password:
            raise ValueError(f"Password not set for user [{self.username}]")
        return verify_password(self.password, password)
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return self.names or self.username

    @property
    def default_roles(self) -> List[str]:
        """Default roles for users without assigned roles."""
        return ['user', 'student']
    
    @property
    def role_names(self) -> List[str]:
        """Get list of role names for this user."""
        if not self.roles:
            return self.default_roles
        return [role.name for role in self.roles]
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        if not self.roles:
            return False
        return any(role.name.lower() == 'admin' for role in self.roles)

    @property
    def is_superuser(self) -> bool:
        """Check if user has superuser role."""
        if not self.roles:
            return False
        return any(role.name.lower() == 'superuser' for role in self.roles)
    
    @property
    def is_tutor(self) -> bool:
        """Check if user has tutor role."""
        if not self.roles:
            return False
        return any(role.name.lower() == 'tutor' for role in self.roles)

    @property
    def is_student(self) -> bool:
        """Check if user has student role."""
        if not self.roles:
            return True  # Default role
        return any(role.name.lower() == 'student' for role in self.roles)

    @property
    def is_parent(self) -> bool:
        """Check if user has parent role."""
        if not self.roles:
            return False
        return any(role.name.lower() == 'parent' for role in self.roles)

    # ========================================================================
    # PERMISSION METHODS
    # ========================================================================
    def has_role(self, *role_names: str) -> bool:
        """
        Check if user has any of the given roles.
        
        Args:
            *role_names: Variable number of role names to check
        
        Returns:
            True if user has any of the specified roles
        """
        if not self.roles:
            return any(r.lower() in ['user', 'student'] for r in role_names)
        
        role_names_lower = [r.lower() for r in role_names]
        return any(role.name.lower() in role_names_lower for role in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission_name: Name of the permission to check
        
        Returns:
            True if user has the permission
        """
        if not self.roles:
            return False
        
        for role in self.roles:
            if hasattr(role, 'permissions'):
                for permission in role.permissions:
                    if permission.name == permission_name:
                        return True
        return False

    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    def get_summary(self) -> dict:
        """
        Get user summary for API responses.
        
        Returns:
            Dictionary containing user summary data
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "names": self.names,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "roles": self.role_names,
            "avatar_url": self.avatar_url,
            "addresses": [
                address.get_summary() 
                for address in self.addresses
            ] if self.addresses else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


