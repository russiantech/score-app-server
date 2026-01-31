# from typing import List, Optional
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import Boolean, String, Text, Integer
# from app.db.mixins import TimestampMixin, UUIDMixin

# from app.db.base_class import Base
# from app.models.tutors import CourseTutor, CourseTutorStatus
# from app.models.user import User

# class Course(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "courses"

#     code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
#     title: Mapped[str] = mapped_column(String(200), nullable=False)
#     description: Mapped[Optional[str]] = mapped_column(Text)
    
#     total_modules: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
#     total_lessons: Mapped[int] = mapped_column(Integer, default=0)
#     duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)
#     difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_public: Mapped[bool] = mapped_column(Boolean, default=True)

#     # Relationships
#     # tutors = relationship(
#     #     "User",
#     #     secondary="course_tutors",
#     #     back_populates="courses_assigned",
#     #     lazy="selectin"
#     # )

#     # Course → Tutor assignments
#     tutors_assigned: Mapped[List["CourseTutor"]] = relationship(
#         "CourseTutor",
#         back_populates="course",
#         cascade="all, delete-orphan"
#     )

#     # Active tutors
#     # @property
#     # def tutors(self):
#     #     return [
#     #         assoc.tutor
#     #         for assoc in self.tutors_assigned
#     #         if assoc.status == CourseTutorStatus.ACTIVE
#     #     ]

#     @property
#     def primary_tutor(self):
#         for assoc in self.tutors_assigned:
#             if assoc.status == CourseTutorStatus.ACTIVE and assoc.is_primary:
#                 return assoc.tutor
#         return None

#     def add_tutor(self, tutor: User):
#         self.tutors_assigned.append(CourseTutor(tutor=tutor))

#     modules: Mapped[List["Module"]] = relationship(
#         "Module",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         order_by="Module.order"
#     )

#     lessons: Mapped[List["Lesson"]] = relationship(
#         "Lesson",
#         back_populates="course",
#         cascade="all, delete-orphan"
#     )

#     enrollments: Mapped[List["Enrollment"]] = relationship(
#         "Enrollment",
#         back_populates="course",
#         cascade="all, delete-orphan"
#     )

#     reviews: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="course",
#         cascade="all, delete-orphan"
#     )

#     payments: Mapped[List["Payment"]] = relationship(
#         "Payment",
#         back_populates="course"
#     )

#     images: Mapped[List["CourseImage"]] = relationship(
#         "CourseImage",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#         order_by="CourseImage.created_at"
#     )

#     # Use association object instead of direct many-to-many
#     def get_summary(self, include_relations: bool = False) -> dict:
#         """
#         Canonical Course serializer.
#         Safe for list views and expandable for detail views.
#         """

#         data = {
#             "id": str(self.id),
#             "code": self.code,
#             "title": self.title,
#             "description": self.description,
#             "total_modules": self.total_modules or 0,
#             "total_lessons": self.total_lessons or 0,
#             "duration_weeks": self.duration_weeks,
#             "difficulty_level": self.difficulty_level,
#             "is_active": self.is_active,
#             "is_public": self.is_public,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#         }

#         if not include_relations:
#             return data

#         # ---------------------------------
#         # Tutors
#         # ---------------------------------
#         tutors = []
#         primary_tutor = None

#         for ct in self.tutors_assigned or []:
#             if not ct.tutor:
#                 continue

#             tutor_data = {
#                 "id": str(ct.tutor.id),
#                 "username": ct.tutor.username,
#                 "names": ct.tutor.names,
#                 "email": ct.tutor.email,
#                 "status": ct.status.value,
#                 "is_primary": ct.is_primary,
#             }

#             tutors.append(tutor_data)

#             if ct.is_primary and ct.status == CourseTutorStatus.ACTIVE:
#                 primary_tutor = tutor_data

#         data["tutors"] = tutors
#         data["primary_tutor"] = primary_tutor
#         data["tutor_count"] = len(tutors)

#         # ---------------------------------
#         # Lessons (ALIGNED TO Lesson MODEL)
#         # ---------------------------------
#         lessons = [
#             {
#                 "id": str(lesson.id),
#                 "title": lesson.title,
#                 "order": lesson.order,
#                 "date": lesson.date.isoformat() if lesson.date else None,
#                 "duration_minutes": lesson.duration_minutes,
#                 "is_published": lesson.is_published,
#                 "has_assessment": lesson.has_assessment,
#                 "has_assignment": lesson.has_assignment,
#             }
#             for lesson in sorted(
#                 self.lessons or [],
#                 key=lambda l: l.order
#             )
#             if lesson.is_published or not self.is_public
#         ]

#         data["lessons"] = lessons

#         # ---------------------------------
#         # Images (UX-friendly)
#         # ---------------------------------
#         images = [
#             {
#                 "id": str(img.id),
#                 "url": img.url,
#                 "is_cover": img.is_cover,
#             }
#             for img in self.images or []
#         ]

#         data["images"] = images
#         data["cover_image"] = next(
#             (img["url"] for img in images if img["is_cover"]),
#             None
#         )

#         return data

#     # def get_summary(self, include_relations=False):
#     #     data = {
#     #         "id": self.id,
#     #         "code": self.code,
#     #         "title": self.title,
#     #         "description": self.description,
#     #         "total_lessons": self.total_lessons,
#     #         "duration_weeks": self.duration_weeks,
#     #         "difficulty_level": self.difficulty_level,
#     #         "is_active": self.is_active,
#     #         "is_public": self.is_public,
#     #     }

#     #     if include_relations:
#     #         data["tutors"] = [
#     #             {
#     #                 "id": str(ct.tutor.id),
#     #                 "username": ct.tutor.username,
#     #                 "names": ct.tutor.names,
#     #                 "email": ct.tutor.email,
#     #                 "is_active": ct.tutor.is_active,
#     #                 "status": ct.status.value,
#     #                 "is_primary": ct.is_primary,
#     #             }
#     #             for ct in self.tutors_assigned
#     #             if ct.tutor
#     #         ]


#     #         data["lessons"] = [
#     #             {
#     #                 "id": str(lesson.id),
#     #                 "code": lesson.code,
#     #                 "title": lesson.title,
#     #             }
#     #             for lesson in self.lessons
#     #         ] if self.lessons else []

#     #     return data



# v2
    
# from typing import List, Optional

# from sqlalchemy import Boolean, String, Text, Integer
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.base_class import Base
# from app.db.mixins import TimestampMixin, UUIDMixin
# from app.models.tutors import CourseTutor, CourseTutorStatus
# from app.models.user import User


# class Course(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "courses"

#     # -------------------------
#     # Core fields
#     # -------------------------
#     code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
#     title: Mapped[str] = mapped_column(String(200), nullable=False)
#     description: Mapped[Optional[str]] = mapped_column(Text)

#     total_modules: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
#     total_lessons: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

#     duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)
#     difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))

#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_public: Mapped[bool] = mapped_column(Boolean, default=True)

#     # -------------------------
#     # Tutor assignments (association object)
#     # -------------------------
#     tutors_assigned: Mapped[List["CourseTutor"]] = relationship(
#         "CourseTutor",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#     )

#     @property
#     def primary_tutor(self) -> Optional[User]:
#         for assoc in self.tutors_assigned:
#             if assoc.status == CourseTutorStatus.ACTIVE and assoc.is_primary:
#                 return assoc.tutor
#         return None

#     def add_tutor(self, tutor: User) -> None:
#         self.tutors_assigned.append(CourseTutor(tutor=tutor))

#     # -------------------------
#     # Modules (Course → Module → Lesson)
#     # -------------------------
#     # lessons: Mapped[List["Lesson"]] = relationship(
#     #     "Lesson",
#     #     back_populates="course",
#     #     cascade="all, delete-orphan"
#     # )
        
#     modules: Mapped[List["Module"]] = relationship(
#         "Module",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         order_by="Module.order",
#         lazy="selectin",
#     )

#     # -------------------------
#     # Other relationships
#     # -------------------------
#     enrollments: Mapped[List["Enrollment"]] = relationship(
#         "Enrollment",
#         back_populates="course",
#         cascade="all, delete-orphan",
#     )

#     reviews: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="course",
#         cascade="all, delete-orphan",
#     )

#     payments: Mapped[List["Payment"]] = relationship(
#         "Payment",
#         back_populates="course",
#     )

#     images: Mapped[List["CourseImage"]] = relationship(
#         "CourseImage",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#         order_by="CourseImage.created_at",
#     )

#     # -------------------------
#     # Serializer
#     # -------------------------
#     def get_summary(self, include_relations: bool = False) -> dict:
#         data = {
#             "id": str(self.id),
#             "code": self.code,
#             "title": self.title,
#             "description": self.description,
#             "total_modules": self.total_modules,
#             "total_lessons": self.total_lessons,
#             "duration_weeks": self.duration_weeks,
#             "difficulty_level": self.difficulty_level,
#             "is_active": self.is_active,
#             "is_public": self.is_public,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#         }

#         if not include_relations:
#             return data

#         # Tutors
#         tutors = []
#         primary_tutor = None

#         for ct in self.tutors_assigned:
#             if not ct.tutor:
#                 continue

#             tutor_data = {
#                 "id": str(ct.tutor.id),
#                 "username": ct.tutor.username,
#                 "names": ct.tutor.names,
#                 "email": ct.tutor.email,
#                 "status": ct.status.value,
#                 "is_primary": ct.is_primary,
#             }

#             tutors.append(tutor_data)

#             if ct.is_primary and ct.status == CourseTutorStatus.ACTIVE:
#                 primary_tutor = tutor_data

#         data["tutors"] = tutors
#         data["primary_tutor"] = primary_tutor
#         data["tutor_count"] = len(tutors)

#         # Lessons (via modules — CORRECT)
#         lessons = []
#         for module in self.modules:
#             for lesson in module.lessons:
#                 if lesson.is_published or not self.is_public:
#                     lessons.append({
#                         "id": str(lesson.id),
#                         "module_id": str(module.id),
#                         "title": lesson.title,
#                         "order": lesson.order,
#                         "date": lesson.date.isoformat() if lesson.date else None,
#                         "status": lesson.status,
#                     })

#         data["lessons"] = sorted(lessons, key=lambda l: l["order"])

#         # Images
#         images = [
#             {"id": str(img.id), "url": img.url, "is_cover": img.is_cover}
#             for img in self.images
#         ]

#         data["images"] = images
#         data["cover_image"] = next((i["url"] for i in images if i["is_cover"]), None)

#         return data




# # v3
# from typing import List, Optional

# from sqlalchemy import Boolean, String, Text, Integer
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.base_class import Base
# from app.db.mixins import TimestampMixin, UUIDMixin
# from app.models.tutors import CourseTutor, CourseTutorStatus
# from app.models.user import User


# class Course(UUIDMixin, TimestampMixin, Base):
#     __tablename__ = "courses"

#     # Core fields
#     code: Mapped[str] = mapped_column(
#         String(20), unique=True, index=True, nullable=False
#     )
#     title: Mapped[str] = mapped_column(String(200), nullable=False)
#     description: Mapped[Optional[str]] = mapped_column(Text)

#     total_modules: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
#     total_lessons: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

#     duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)
#     difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))

#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     is_public: Mapped[bool] = mapped_column(Boolean, default=True)

#     # Tutor assignments (association object pattern)
#     tutors_assigned: Mapped[List["CourseTutor"]] = relationship(
#         "CourseTutor",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#     )

#     # Modules (Course → Module → Lesson hierarchy)
#     modules: Mapped[List["Module"]] = relationship(
#         "Module",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         order_by="Module.order",
#         lazy="selectin",
#     )

#     # Enrollments
#     enrollments: Mapped[List["Enrollment"]] = relationship(
#         "Enrollment",
#         back_populates="course",
#         cascade="all, delete-orphan",
#     )

#     # Reviews
#     reviews: Mapped[List["Review"]] = relationship(
#         "Review",
#         back_populates="course",
#         cascade="all, delete-orphan",
#     )

#     # Payments
#     payments: Mapped[List["Payment"]] = relationship(
#         "Payment",
#         back_populates="course",
#     )

#     # Images
#     images: Mapped[List["CourseImage"]] = relationship(
#         "CourseImage",
#         back_populates="course",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#         order_by="CourseImage.created_at",
#     )

#     # Helper properties
#     @property
#     def primary_tutor(self) -> Optional[User]:
#         """Get the primary active tutor for this course."""
#         for assoc in self.tutors_assigned:
#             if assoc.status == CourseTutorStatus.ACTIVE and assoc.is_primary:
#                 return assoc.tutor
#         return None

#     @property
#     def active_tutors(self) -> List[User]:
#         """Get all active tutors for this course."""
#         return [
#             assoc.tutor for assoc in self.tutors_assigned
#             if assoc.status == CourseTutorStatus.ACTIVE and assoc.tutor
#         ]

#     def add_tutor(self, tutor: User, is_primary: bool = False) -> None:
#         """Add a tutor to this course."""
#         assignment = CourseTutor(
#             tutor=tutor,
#             status=CourseTutorStatus.ACTIVE,
#             is_primary=is_primary
#         )
#         self.tutors_assigned.append(assignment)

#     # Serializer
#     def get_summary(self, include_relations: bool = True) -> dict:
#         """Get course summary with optional relations."""
#         data = {
#             "id": str(self.id),
#             "code": self.code,
#             "title": self.title,
#             "description": self.description,
#             "total_modules": self.total_modules,
#             "total_lessons": self.total_lessons,
#             "duration_weeks": self.duration_weeks,
#             "difficulty_level": self.difficulty_level,
#             "is_active": self.is_active,
#             "is_public": self.is_public,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#             "updated_at": self.updated_at.isoformat() if self.updated_at else None,
#         }

#         if not include_relations:
#             return data

#         # Serialize tutors
#         tutors = []
#         primary_tutor = None

#         for ct in self.tutors_assigned:
#             if not ct.tutor or ct.status != CourseTutorStatus.ACTIVE:
#                 continue

#             tutor_data = {
#                 "id": str(ct.tutor.id),
#                 "username": ct.tutor.username,
#                 "names": ct.tutor.names,
#                 "email": ct.tutor.email,
#                 "status": ct.status.value,
#                 "is_primary": ct.is_primary,
#             }

#             tutors.append(tutor_data)

#             if ct.is_primary:
#                 primary_tutor = tutor_data

#         data["tutors"] = tutors
#         data["primary_tutor"] = primary_tutor
#         data["tutor_count"] = len(tutors)

#         # Serialize modules with lessons (proper hierarchy)
#         modules_data = []
#         total_lessons = 0

#         for module in sorted(self.modules, key=lambda m: m.order):
#             lessons_data = []
            
#             for lesson in sorted(module.lessons, key=lambda l: l.order):
#                 # Only include published lessons for public courses
#                 if not self.is_public or lesson.is_published:
#                     lessons_data.append({
#                         "id": str(lesson.id),
#                         "title": lesson.title,
#                         "order": lesson.order,
#                         "date": lesson.date.isoformat() if lesson.date else None,
#                         "duration": lesson.duration,
#                         "status": lesson.status,
#                         "is_published": lesson.is_published,
#                     })
#                     total_lessons += 1

#             modules_data.append({
#                 "id": str(module.id),
#                 "title": module.title,
#                 "description": module.description,
#                 "order": module.order,
#                 "lessons_count": len(lessons_data),
#                 "lessons": lessons_data,
#             })

#         data["modules"] = modules_data
#         data["modules_count"] = len(modules_data)
#         data["total_lessons_count"] = total_lessons

#         # Serialize images
#         images = []
#         cover_image = None

#         for img in self.images:
#             image_data = {
#                 "id": str(img.id),
#                 "url": img.url,
#                 "is_cover": img.is_cover,
#             }
#             images.append(image_data)
            
#             if img.is_cover:
#                 cover_image = img.url

#         data["images"] = images
#         data["cover_image"] = cover_image

#         return data




# v4
from typing import List, Optional

from sqlalchemy import Boolean, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.tutors import CourseTutor, CourseTutorStatus
from app.models.user import User


class Course(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    # Core fields
    code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    total_modules: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    total_lessons: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)
    difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tutor assignments (association object pattern)
    tutors_assigned: Mapped[List["CourseTutor"]] = relationship(
        "CourseTutor",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Modules (Course → Module → Lesson hierarchy)
    modules: Mapped[List["Module"]] = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.order",
        lazy="selectin",
    )

    # Enrollments
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    score_columns: Mapped[List["ScoreColumn"]] = relationship(
        "ScoreColumn",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    # Reviews
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    # Payments
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="course",
    )

    # Images
    images: Mapped[List["CourseImage"]] = relationship(
        "CourseImage",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CourseImage.created_at",
    )

    # Helper properties
    @property
    def primary_tutor(self) -> Optional[User]:
        """Get the primary active tutor for this course."""
        for assoc in self.tutors_assigned:
            if assoc.status == CourseTutorStatus.ACTIVE and assoc.is_primary:
                return assoc.tutor
        return None

    @property
    def active_tutors(self) -> List[User]:
        """Get all active tutors for this course."""
        return [
            assoc.tutor for assoc in self.tutors_assigned
            if assoc.status == CourseTutorStatus.ACTIVE and assoc.tutor
        ]

    def add_tutor(self, tutor: User, is_primary: bool = False) -> None:
        """Add a tutor to this course."""
        assignment = CourseTutor(
            tutor=tutor,
            status=CourseTutorStatus.ACTIVE,
            is_primary=is_primary
        )
        self.tutors_assigned.append(assignment)

    # Serializer
    def get_summary(self, include_relations: bool = False) -> dict:
        """
        Get course summary with optional relations.
        
        Args:
            include_relations: Include tutors, modules with lessons, and images
        
        Returns:
            Dictionary containing course data
        """
        data = {
            "id": str(self.id),
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "total_modules": self.total_modules,
            "total_lessons": self.total_lessons,
            "duration_weeks": self.duration_weeks,
            "difficulty_level": self.difficulty_level,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if not include_relations:
            return data

        # Serialize tutors
        tutors = []
        primary_tutor = None

        for ct in self.tutors_assigned:
            if not ct.tutor or ct.status != CourseTutorStatus.ACTIVE:
                continue

            tutor_data = {
                "id": str(ct.tutor.id),
                "username": ct.tutor.username,
                "names": ct.tutor.names,
                "email": ct.tutor.email,
                "status": ct.status.value,
                "is_primary": ct.is_primary,
            }

            tutors.append(tutor_data)

            if ct.is_primary:
                primary_tutor = tutor_data

        data["tutors"] = tutors
        data["primary_tutor"] = primary_tutor
        data["tutor_count"] = len(tutors)

        # Serialize modules with lessons
        modules_data = []
        total_lessons_count = 0

        for module in sorted(self.modules, key=lambda m: m.order):
            lessons_data = []
            
            if hasattr(module, 'lessons') and module.lessons:
                for lesson in sorted(module.lessons, key=lambda l: l.order):
                    lessons_data.append({
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "description": getattr(lesson, 'description', None),
                        "order": lesson.order,
                        "date": lesson.date.isoformat() if hasattr(lesson, 'date') and lesson.date else None,
                        "duration": getattr(lesson, 'duration', None),
                        "status": getattr(lesson, 'status', None),
                        "is_published": getattr(lesson, 'is_published', True),
                    })
                    total_lessons_count += 1

            modules_data.append({
                "id": str(module.id),
                "title": module.title,
                "description": module.description,
                "order": module.order,
                "lessons_count": len(lessons_data),
                "lessons": lessons_data,
            })

        data["modules"] = modules_data
        data["modules_count"] = len(modules_data)
        data["total_lessons_count"] = total_lessons_count

        # Serialize images
        images = []
        cover_image = None

        for img in self.images:
            image_data = {
                "id": str(img.id),
                "url": img.url,
                "is_cover": img.is_cover,
            }
            images.append(image_data)
            
            if img.is_cover:
                cover_image = img.url

        data["images"] = images
        data["cover_image"] = cover_image

        return data