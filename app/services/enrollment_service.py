# from sqlalchemy.orm import Session
# from app.models.enrollment import Enrollment
# from app.schemas.enrollment import EnrollmentCreate
# from fastapi import HTTPException

# def enroll_student(db: Session, data: EnrollmentCreate):
#     exists = db.query(Enrollment).filter(
#         Enrollment.student_id == data.student_id,
#         Enrollment.course_id == data.course_id,
#         Enrollment.session == data.session
#     ).first()

#     if exists:
#         raise HTTPException(400, "Already enrolled")

#     enrollment = Enrollment(**data.dict())
#     db.add(enrollment)
#     db.commit()
#     db.refresh(enrollment)
#     return enrollment

# def get_enrollment(db: Session, enrollment_id):
#     x = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
#     if not x:
#         raise HTTPException(404, "Enrollment not found")
#     return x


# # v2
# # ============================================================================
# # SERVICES - Part 4: Enrollment Service
# # FILE: app/services/enrollment_service.py
# # ============================================================================

# from sqlalchemy.orm import Session
# from uuid import UUID
# from fastapi import HTTPException, status

# from app.models.course import Course
# from app.models.enrollment import Enrollment
# from app.models.user import User

# def enroll_student(db: Session, student_id: UUID, course_id: UUID) -> Enrollment:
#     """Enroll a student in a course"""
#     # Verify student and course exist
#     student = db.query(User).filter(User.id == student_id).first()
#     if not student or 'student' not in student.roles:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Student not found"
#         )
    
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Course not found"
#         )
    
#     # Check if already enrolled
#     existing = db.query(Enrollment).filter(
#         Enrollment.student_id == student_id,
#         Enrollment.course_id == course_id
#     ).first()
    
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Student already enrolled in this course"
#         )
    
#     enrollment = Enrollment(student_id=student_id, course_id=course_id)
#     db.add(enrollment)
#     db.commit()
#     db.refresh(enrollment)
#     return enrollment

# def list_enrollments(
#     db: Session,
#     course_id: UUID | None = None,
#     student_id: UUID | None = None
# ) -> list[Enrollment]:
#     """List enrollments with optional filters"""
#     query = db.query(Enrollment)
    
#     if course_id:
#         query = query.filter(Enrollment.course_id == course_id)
    
#     if student_id:
#         query = query.filter(Enrollment.student_id == student_id)
    
#     return query.order_by(Enrollment.enrolled_at.desc()).all()

# def unenroll_student(db: Session, enrollment_id: UUID) -> None:
#     """Unenroll a student from a course"""
#     enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
#     if not enrollment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Enrollment not found"
#         )
    
#     db.delete(enrollment)
#     db.commit()



# v3
from typing import Optional, Tuple, List
from sqlalchemy import or_, desc, asc, and_
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.enrollment import EnrollmentCreate, EnrollmentFilters
from app.models.course import Course
from app.models.user import User
from app.models.rbac import Role

# def list_enrollments(
#     db: Session,
#     filters: Optional[EnrollmentFilters] = None
# ) -> Tuple[List[Enrollment], int]:
#     """
#     Get filtered, sorted, and paginated list of enrollments.
#     """
#     query = (
#         db.query(Enrollment)
#         .options(
#             joinedload(Enrollment.student),
#             joinedload(Enrollment.course)
#         )
#     )
    
#     if not filters:
#         filters = EnrollmentFilters()
    
#     # Apply search filter
#     if filters.search:
#         search_term = f"%{filters.search.lower()}%"
#         query = query.join(Enrollment.student).join(Enrollment.course).filter(
#             or_(
#                 User.names.ilike(search_term),
#                 User.email.ilike(search_term),
#                 Course.title.ilike(search_term),
#                 Course.code.ilike(search_term)
#             )
#         )
    
#     # Apply status filter
#     if filters.status:
#         query = query.filter(Enrollment.status == filters.status)
    
#     # Apply student filter
#     if filters.student_id:
#         query = query.filter(Enrollment.student_id == filters.student_id)
    
#     # Apply course filter
#     if filters.course_id:
#         query = query.filter(Enrollment.course_id == filters.course_id)
    
#     # Apply sorting
#     sort_column = getattr(Enrollment, filters.sort_by, Enrollment.enrolled_at)
#     query = query.order_by(
#         desc(sort_column) if filters.order == "desc" else asc(sort_column)
#     )
    
#     # Get total count
#     total = query.count()
    
#     # Apply pagination
#     enrollments = (
#         query
#         .offset((filters.page - 1) * filters.page_size)
#         .limit(filters.page_size)
#         .all()
#     )
    
#     return enrollments, total


def list_enrollments(
    db: Session,
    filters: Optional[EnrollmentFilters] = None
) -> Tuple[List[Enrollment], int]:

    # prevents N + 1 queries when relations are included.
    query = (
        db.query(Enrollment)
        .options(
            joinedload(Enrollment.student),
            joinedload(Enrollment.course)
        )
    )

    filters = filters or EnrollmentFilters()

    if filters.search:
        term = f"%{filters.search.lower()}%"
        query = (
            query
            .join(Enrollment.student)
            .join(Enrollment.course)
            .filter(
                or_(
                    User.names.ilike(term),
                    User.email.ilike(term),
                    Course.title.ilike(term),
                    Course.code.ilike(term)
                )
            )
        )

    if filters.status:
        query = query.filter(Enrollment.status == EnrollmentStatus(filters.status))

    if filters.student_id:
        query = query.filter(Enrollment.student_id == filters.student_id)

    if filters.course_id:
        query = query.filter(Enrollment.course_id == filters.course_id)

    sort_col = getattr(Enrollment, filters.sort_by, Enrollment.enrolled_at)
    query = query.order_by(desc(sort_col) if filters.order == "desc" else asc(sort_col))

    total = query.count()

    enrollments = (
        query
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
        .all()
    )

    return enrollments, total

# def create_enrollment(
#     db: Session,
#     student_id: UUID,
#     course_id: UUID
# ) -> Enrollment:
def create_enrollment(db: Session, enrollment_data: EnrollmentCreate):
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment_data.student_id,
        Enrollment.course_id == enrollment_data.course_id,
        Enrollment.status != EnrollmentStatus.WITHDRAWN
    ).first()

    if existing:
        raise ValueError("Student is already enrolled in this course")

    student = db.query(User).filter(User.id == enrollment_data.student_id).first()
    if not student:
        raise ValueError("Student not found")

    course = db.query(Course).filter(Course.id == enrollment_data.course_id).first()
    if not course:
        raise ValueError("Course not found")

    # enrollment = Enrollment(
    #     student_id=student_id,
    #     course_id=course_id,
    #     status=EnrollmentStatus.ACTIVE,
    #     enrolled_at=datetime.utcnow()
    # )
    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        course_id=enrollment_data.course_id,
        session=enrollment_data.session,
        term=enrollment_data.term,
        status=EnrollmentStatus.ACTIVE,
    )
    

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


def delete_enrollment(db: Session, enrollment_id: UUID) -> None:
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()

    if not enrollment:
        raise ValueError("Enrollment not found")

    db.delete(enrollment)
    db.commit()


def get_enrollment_stats(db: Session) -> dict:
    total_enrollments = db.query(Enrollment).count()

    active_enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
        .count()
    )

    students_enrolled = (
        db.query(Enrollment.student_id)
        .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
        .distinct()
        .count()
    )

    courses_with_students = (
        db.query(Enrollment.course_id)
        .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
        .distinct()
        .count()
    )

    total_students = (
        db.query(User)
        .filter(User.roles.any(Role.name == "student"))
        .count()
    )

    total_courses = (
        db.query(Course)
        .filter(Course.is_active.is_(True))
        .count()
    )

    return {
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "students_enrolled": students_enrolled,
        "courses_with_students": courses_with_students,
        "total_students": total_students,
        "total_courses": total_courses,
    }


# def get_enrollment_stats(db: Session) -> dict:
#     total_enrollments = db.query(Enrollment).count()

#     active_enrollments = (
#         db.query(Enrollment)
#         .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
#         .count()
#     )

#     students_enrolled = (
#         db.query(Enrollment.student_id)
#         .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
#         .distinct()
#         .count()
#     )

#     courses_with_students = (
#         db.query(Enrollment.course_id)
#         .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
#         .distinct()
#         .count()
#     )

#     total_students = (
#         db.query(User)
#         .filter(User.roles.contains(["student"]))
#         .count()
#     )

#     total_courses = (
#         db.query(Course)
#         .filter(Course.is_active.is_(True))
#         .count()
#     )

#     return {
#         "total_enrollments": total_enrollments,
#         "active_enrollments": active_enrollments,
#         "students_enrolled": students_enrolled,
#         "courses_with_students": courses_with_students,
#         "total_students": total_students,
#         "total_courses": total_courses,
#     }


# def create_enrollment(
#     db: Session,
#     student_id: UUID,
#     course_id: UUID
# ) -> Enrollment:
#     """
#     Create a new enrollment.
#     """
#     # Check if enrollment already exists
#     existing = db.query(Enrollment).filter(
#         and_(
#             Enrollment.student_id == student_id,
#             Enrollment.course_id == course_id,
#             Enrollment.status != 'dropped'
#         )
#     ).first()
    
#     if existing:
#         raise ValueError("Student is already enrolled in this course")
    
#     # Verify student and course exist
#     student = db.query(User).filter(User.id == student_id).first()
#     if not student:
#         raise ValueError("Student not found")
    
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         raise ValueError("Course not found")
    
#     enrollment = Enrollment(
#         student_id=student_id,
#         course_id=course_id,
#         enrolled_at=datetime.now(),
#         status='active',
#         progress=0
#     )
    
#     db.add(enrollment)
#     db.commit()
#     db.refresh(enrollment)
    
#     return enrollment


# def delete_enrollment(db: Session, enrollment_id: UUID) -> bool:
#     """
#     Delete an enrollment (unenroll student).
#     """
#     enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    
#     if not enrollment:
#         raise ValueError("Enrollment not found")
    
#     db.delete(enrollment)
#     db.commit()
    
#     return True


# def get_enrollment_stats(db: Session) -> dict:
#     """
#     Get enrollment statistics.
#     """
#     total_enrollments = db.query(Enrollment).count()
#     active_enrollments = db.query(Enrollment).filter(Enrollment.status == 'active').count()
    
#     students_enrolled = (
#         db.query(Enrollment.student_id)
#         .filter(Enrollment.status == 'active')
#         .distinct()
#         .count()
#     )
    
#     courses_with_students = (
#         db.query(Enrollment.course_id)
#         .filter(Enrollment.status == 'active')
#         .distinct()
#         .count()
#     )
    
#     total_students = db.query(User).filter(User.roles.contains(['student'])).count()
#     total_courses = db.query(Course).filter(Course.is_active == True).count()
    
#     return {
#         "total_enrollments": total_enrollments,
#         "active_enrollments": active_enrollments,
#         "students_enrolled": students_enrolled,
#         "courses_with_students": courses_with_students,
#         "total_students": total_students,
#         "total_courses": total_courses
#     }

