# # v3 - checks for duplicates
# from fastapi import HTTPException
# from sqlalchemy.exc import IntegrityError
# from uuid import UUID
# from app.models.course import Course
# from app.models.user import User
# from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate
# from sqlalchemy import or_, desc, asc


# from typing import Optional, Tuple, List
# from sqlalchemy.orm import Session, joinedload

# from app.models.tutors import CourseTutor
# from app.schemas.tutors import CourseTutorStatus
# from app.models.modules import Module
# from app.models.lesson import Lesson

# # def create_course(db: Session, data: CourseCreate) -> Course:
# #     # Check for duplicate code
# #     existing = db.query(Course).filter(Course.code == data.code).first()
# #     if existing:
# #         raise HTTPException(status_code=400, detail=f"Course with code '{data.code}' already exists")

# #     course = Course(**data.model_dump(exclude={"tutor_ids"}))

# #     # Add instructors if provided
# #     if data.tutor_ids:
# #         tutors = db.query(User).filter(User.id.in_(data.tutor_ids)).all()
# #         course.tutors_assigned.extend(tutors)

# #     try:
# #         db.add(course)
# #         db.commit()
# #         db.refresh(course)
# #     except IntegrityError as e:
# #         db.rollback()
# #         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# #     return course


# def create_course(db: Session, data: CourseCreate) -> Course:
#     # Check for duplicate code
#     existing = db.query(Course).filter(Course.code == data.code).first()
#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Course with code '{data.code}' already exists"
#         )

#     course = Course(**data.model_dump(exclude={"tutor_ids"}))

#     # Add tutors if provided
#     if data.tutor_ids:
#         tutors = (
#             db.query(User)
#             .filter(User.id.in_(data.tutor_ids))
#             .all()
#         )

#         course.tutors_assigned = [
#             CourseTutor(tutor=tutor)
#             for tutor in tutors
#         ]

#     try:
#         db.add(course)
#         db.commit()
#         db.refresh(course)
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#     return course

# def get_course(db: Session, course_id: UUID) -> Course | None:
#     return db.query(Course).filter(Course.id == course_id).first()


# def get_course_by_id(
#     db: Session,
#     course_id: UUID,
#     include_relations: bool = True
# ) -> Course:
#     query = (
#         db.query(Course)
#         .filter(Course.id == course_id)
#     )

#     if include_relations:
        
#         # query = query.options(
#         #     joinedload(Course.tutors_assigned)
#         #         .joinedload(CourseTutor.tutor),
#         #     joinedload(Course.lessons),
#         #     joinedload(Course.modules),
#         # )
#         # query = query.options(
#         #     joinedload(Course.tutors_assigned)
#         #         .joinedload(CourseTutor.tutor),
#         #     joinedload(Course.modules)
#         #         .joinedload("lessons"),
#         # )
#         # query = query.options(
#         #     joinedload(Course.tutors_assigned)
#         #         .joinedload(CourseTutor.tutor),
#         #     joinedload(Course.modules)
#         #         .joinedload("lessons"),
#         # )
#         from sqlalchemy import func

#         lesson_count_subq = (
#             db.query(
#                 Module.course_id.label("course_id"),
#                 func.count(Lesson.id).label("lesson_count")
#             )
#             .join(Lesson)
#             .group_by(Module.course_id)
#             .subquery()
#         )

#         query = (
#             db.query(Course, lesson_count_subq.c.lesson_count)
#             .outerjoin(lesson_count_subq, Course.id == lesson_count_subq.c.course_id)
#         )


#     course = query.first()

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     return course

# # v5
# def get_courses_query(
#     db: Session,
#     filters: Optional[CourseFilters] = None
# ):
#     """
#     Get filtered and sorted query (without executing).
#     For use with PageSerializer that does its own pagination.
#     """
#     query = db.query(Course).options(joinedload(Course.tutors_assigned))
    
#     if not filters:
#         return query.order_by(desc(Course.created_at))
    
#     # Apply search filter
#     if filters.search:
#         search_term = f"%{filters.search.lower()}%"
#         query = query.filter(
#             or_(
#                 Course.title.ilike(search_term),
#                 Course.code.ilike(search_term),
#                 Course.description.ilike(search_term)
#             )
#         )
    
#     # Apply status filter
#     if filters.status:
#         is_active = filters.status.lower() == "active"
#         query = query.filter(Course.is_active == is_active)
    
#     # Apply tutor filter
#     if filters.tutor_id:
#         # query = query.join(Course.tutors_assigned).filter(User.id == filters.tutor_id)
#         query = db.query(Course).options(
#             joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor)
#         )
    
#     # Apply sorting
#     sort_column = getattr(Course, filters.sort_by, Course.created_at)
#     query = query.order_by(
#         desc(sort_column) if filters.order == "desc" else asc(sort_column)
#     )
    
#     return query


# def list_courses(
#     db: Session,
#     filters: Optional[CourseFilters] = None
# ) -> Tuple[List[Course], int]:
#     """
#     Get filtered, sorted, and paginated list of courses.
#     Returns (courses, total_count)
#     """
#     query = get_courses_query(db, filters)
    
#     # Get total count
#     total = query.count()
    
#     # Apply pagination if filters provided
#     if filters:
#         courses = (
#             query
#             .offset((filters.page - 1) * filters.page_size)
#             .limit(filters.page_size)
#             .all()
#         )
#     else:
#         courses = query.all()
    
#     return courses, total


# def update_course(db: Session, course_id: UUID, data: CourseUpdate) -> Course:
    
#     if not data.model_dump(exclude_unset=True):
#         raise HTTPException(status_code=400, detail="No fields provided for update")
                            
#     course = get_course(db, course_id)
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     update_data = data.model_dump(exclude_unset=True)

#     # Check if code is being updated and ensure uniqueness
#     if "code" in update_data:
#         existing = db.query(Course).filter(Course.code == update_data["code"], Course.id != course_id).first()
#         if existing:
#             raise HTTPException(status_code=400, detail=f"Course with code '{update_data['code']}' already exists")

#     # Apply updates
#     for field, value in update_data.items():

#         # v2 - since relationship table no longer simple Table()
#         if field == "tutor_ids" and value is not None:
#             # Existing tutor IDs already assigned
#             existing_tutor_ids = {
#                 ct.tutor_id for ct in course.tutors_assigned
#                 if ct.status == CourseTutorStatus.ACTIVE
#             }

#             # Tutors to assign
#             tutors = db.query(User).filter(User.id.in_(value)).all()

#             for tutor in tutors:
#                 if tutor.id not in existing_tutor_ids:
#                     assignment = CourseTutor(
#                         tutor_id=tutor.id,
#                         course_id=course.id,
#                         status=CourseTutorStatus.ACTIVE,
#                     )
#                     course.tutors_assigned.append(assignment)

#         else:
#             setattr(course, field, value)

#     try:
#         db.commit()
#         db.refresh(course)
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#     return course


# def delete_course(db: Session, course_id: UUID):
#     course = get_course(db, course_id)
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     try:
#         db.delete(course)
#         db.commit()
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")




# v3
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case, or_, desc, asc, func
from uuid import UUID
from typing import Optional, Tuple, List

from app.models.course import Course
from app.models.user import User
from app.models.tutors import CourseTutor, CourseTutorStatus
from app.models.modules import Module
from app.models.lesson import Lesson
from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate
from app.utils.serializers import serialize_course
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceStatus


def create_course(db: Session, data: CourseCreate) -> Course:
    """Create a new course with optional tutor assignments."""
    # Check for duplicate code
    existing = db.query(Course).filter(Course.code == data.code).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Course with code '{data.code}' already exists"
        )

    # Create course (exclude tutor_ids from model dump)
    course = Course(**data.model_dump(exclude={"tutor_ids"}))

    # Add tutors if provided
    if data.tutor_ids:
        tutors = db.query(User).filter(User.id.in_(data.tutor_ids)).all()
        
        if len(tutors) != len(data.tutor_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more tutors not found"
            )
        
        course.tutors_assigned = [
            CourseTutor(
                tutor=tutor,
                status=CourseTutorStatus.ACTIVE,
                is_primary=(i == 0)  # First tutor is primary
            )
            for i, tutor in enumerate(tutors)
        ]

    try:
        db.add(course)
        db.commit()
        db.refresh(course)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    return course


def get_course(db: Session, course_id: UUID) -> Course | None:
    """Get a course by ID without relations."""
    return db.query(Course).filter(Course.id == course_id).first()


# def get_course_by_id(
#     db: Session,
#     course_id: UUID,
#     include_relations: bool = True
# ) -> Course:
#     """Get a course by ID with optional relations. """
#     query = db.query(Course).filter(Course.id == course_id)
    
#     # Load course with explicit eager loading
#     if include_relations:
#         query = query.options(
#             joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor),
#             joinedload(Course.modules).joinedload(Module.lessons),
#             joinedload(Course.images)
#         )

#     course = query.first()

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     return course


# def get_course_with_optional_attendance(
#     db: Session,
#     course_id: UUID,
#     include_relations: bool = False,
#     include_attendance: bool = False,
# ) -> dict:
#     """
#     Fetch a course with optional modules/lessons and attendance statistics.
#     Returns a fully serialized dictionary (NOT ORM objects).
#     """

#     query = db.query(Course)

#     if include_relations:
#         query = query.options(
#             joinedload(Course.modules).joinedload(Module.lessons)
#         )

#     course = query.filter(Course.id == course_id).first()

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     # If attendance not requested, just serialize
#     if not (include_attendance and include_relations):
#         return serialize_course(course)

#     # -----------------------------
#     # Attendance aggregation
#     # -----------------------------
#     lesson_ids = [
#         lesson.id
#         for module in (course.modules or [])
#         for lesson in (module.lessons or [])
#     ]

#     stats_lookup = {}

#     if lesson_ids:
#         stats = (
#             db.query(
#                 Attendance.lesson_id,
#                 func.count(Attendance.id).label("total"),
#                 func.sum(
#                     case(
#                         (Attendance.status == AttendanceStatus.PRESENT, 1),
#                         else_=0,
#                     )
#                 ).label("present"),
#             )
#             .filter(Attendance.lesson_id.in_(lesson_ids))
#             .group_by(Attendance.lesson_id)
#             .all()
#         )

#         stats_lookup = {
#             row.lesson_id: {
#                 "total": row.total or 0,
#                 "present": int(row.present or 0),
#             }
#             for row in stats
#         }

#     # Attach stats (safe mutation before serialization)
#     for module in course.modules or []:
#         for lesson in module.lessons or []:
#             stat = stats_lookup.get(lesson.id, {"total": 0, "present": 0})

#             lesson.attendance_count = stat["total"]
#             lesson.present_count = stat["present"]
#             lesson.attendance_rate = (
#                 round((stat["present"] / stat["total"]) * 100, 1)
#                 if stat["total"] > 0
#                 else 0
#             )

#     return serialize_course(course)

# def get_course_with_optional_attendance(
#     db: Session,
#     course_id: UUID,
#     include_relations: bool = True,
#     include_attendance: bool = False,
# ) -> dict:
#     """
#     Superset of get_course_by_id:
#     - Loads tutors, modules, lessons, images (same as baseline)
#     - Optionally enriches lessons with attendance statistics
#     - Always returns a serialized dict
#     """

#     query = db.query(Course).filter(Course.id == course_id)

#     #  STRICTLY mirror get_course_by_id
#     if include_relations:
#         query = query.options(
#             joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor),
#             joinedload(Course.modules).joinedload(Module.lessons),
#             joinedload(Course.images),
#         )

#     course = query.first()

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     # --------------------------------
#     # Attendance enrichment (optional)
#     # --------------------------------
#     if include_relations and include_attendance and course.modules:

#         lesson_ids = [
#             lesson.id
#             for module in course.modules
#             for lesson in (module.lessons or [])
#         ]

#         if lesson_ids:
#             stats = (
#                 db.query(
#                     Attendance.lesson_id,
#                     func.count(Attendance.id).label("total"),
#                     func.sum(
#                         case(
#                             (Attendance.status == AttendanceStatus.PRESENT, 1),
#                             else_=0,
#                         )
#                     ).label("present"),
#                 )
#                 .filter(Attendance.lesson_id.in_(lesson_ids))
#                 .group_by(Attendance.lesson_id)
#                 .all()
#             )

#             stats_lookup = {
#                 row.lesson_id: {
#                     "total": int(row.total or 0),
#                     "present": int(row.present or 0),
#                 }
#                 for row in stats
#             }

#             # Attach computed fields
#             for module in course.modules:
#                 for lesson in module.lessons or []:
#                     stat = stats_lookup.get(
#                         lesson.id,
#                         {"total": 0, "present": 0},
#                     )

#                     lesson.attendance_count = stat["total"]
#                     lesson.present_count = stat["present"]
#                     lesson.attendance_rate = (
#                         round((stat["present"] / stat["total"]) * 100, 1)
#                         if stat["total"] > 0
#                         else 0.0
#                     )

#     #  Always serialize AFTER enrichment
#     return serialize_course(course)

# v2
def get_course_with_optional_attendance(
    db: Session,
    course_id: UUID,
    include_relations: bool = True,
    include_attendance: bool = False,
) -> dict:
    """
    Get course by ID, strictly following get_course_by_id behavior,
    with optional lesson attendance statistics.
    """

    query = db.query(Course).filter(Course.id == course_id)

    # ---- STRICTLY mirror original eager loading ----
    if include_relations:
        query = query.options(
            joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor),
            joinedload(Course.modules).joinedload(Module.lessons),
            joinedload(Course.images),
        )

    course = query.first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # ------------------------------------------------
    # Attendance aggregation (ONLY if requested)
    # ------------------------------------------------
    if include_attendance and include_relations:
        lesson_ids = [
            lesson.id
            for module in course.modules or []
            for lesson in module.lessons or []
        ]

        if lesson_ids:
            stats = (
                db.query(
                    Attendance.lesson_id,
                    func.count(Attendance.id).label("total"),
                    func.sum(
                        case(
                            (Attendance.status == AttendanceStatus.PRESENT, 1),
                            else_=0,
                        )
                    ).label("present"),
                )
                .filter(Attendance.lesson_id.in_(lesson_ids))
                .group_by(Attendance.lesson_id)
                .all()
            )

            stats_lookup = {
                row.lesson_id: {
                    "total": row.total or 0,
                    "present": int(row.present or 0),
                }
                for row in stats
            }

            # Attach computed stats to lesson instances
            for module in course.modules or []:
                for lesson in module.lessons or []:
                    stat = stats_lookup.get(
                        lesson.id, {"total": 0, "present": 0}
                    )

                    lesson.attendance_count = stat["total"]
                    lesson.present_count = stat["present"]
                    lesson.attendance_rate = (
                        round((stat["present"] / stat["total"]) * 100, 1)
                        if stat["total"] > 0
                        else 0
                    )

    # ------------------------------------------------
    # Serialization (authoritative)
    # ------------------------------------------------
    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "is_active": course.is_active,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,

        "tutors": [
            {
                "id": str(ct.tutor.id),
                "name": ct.tutor.names,
                "email": ct.tutor.email,
            }
            for ct in (course.tutors_assigned or [])
            if ct.tutor
        ],

        "images": [
            {
                "id": str(img.id),
                "url": img.url,
            }
            for img in (course.images or [])
        ],

        "modules": [
            {
                "id": str(module.id),
                "title": module.title,
                "order": module.order,
                "lessons_count": len(module.lessons or []),
                "lessons": [
                    lesson.get_summary(include_module=False)
                    for lesson in (module.lessons or [])
                ],
            }
            for module in (course.modules or [])
        ],
    }


def get_courses_query(
    db: Session,
    filters: Optional[CourseFilters] = None
):
    """
    Get filtered and sorted query (without executing).
    For use with PageSerializer that does its own pagination.
    """
    query = db.query(Course).options(
        joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor)
    )
    
    if not filters:
        return query.order_by(desc(Course.created_at))
    
    # Apply search filter
    if filters.search:
        search_term = f"%{filters.search.lower()}%"
        query = query.filter(
            or_(
                Course.title.ilike(search_term),
                Course.code.ilike(search_term),
                Course.description.ilike(search_term)
            )
        )
    
    # Apply status filter
    if filters.status:
        is_active = filters.status.lower() == "active"
        query = query.filter(Course.is_active == is_active)
    
    # Apply tutor filter
    if filters.tutor_id:
        query = (
            query
            .join(Course.tutors_assigned)
            .filter(
                CourseTutor.tutor_id == filters.tutor_id,
                CourseTutor.status == CourseTutorStatus.ACTIVE
            )
        )
    
    # Apply sorting
    sort_column = getattr(Course, filters.sort_by, Course.created_at)
    query = query.order_by(
        desc(sort_column) if filters.order == "desc" else asc(sort_column)
    )
    
    return query


def list_courses(
    db: Session,
    filters: Optional[CourseFilters] = None
) -> Tuple[List[Course], int]:
    """
    Get filtered, sorted, and paginated list of courses.
    Returns (courses, total_count)
    """
    query = get_courses_query(db, filters)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination if filters provided
    if filters:
        courses = (
            query
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .all()
        )
    else:
        courses = query.all()
    
    return courses, total


def update_course(db: Session, course_id: UUID, data: CourseUpdate) -> Course:
    """Update a course with validation."""
    update_data = data.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )
                            
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if code is being updated and ensure uniqueness
    if "code" in update_data:
        existing = (
            db.query(Course)
            .filter(
                Course.code == update_data["code"],
                Course.id != course_id
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Course with code '{update_data['code']}' already exists"
            )

    # Handle tutor assignments
    if "tutor_ids" in update_data and update_data["tutor_ids"] is not None:
        new_tutor_ids = set(update_data["tutor_ids"])
        
        # Get existing active tutor IDs
        existing_tutor_ids = {
            ct.tutor_id for ct in course.tutors_assigned
            if ct.status == CourseTutorStatus.ACTIVE
        }

        # Find tutors to add
        tutors_to_add = new_tutor_ids - existing_tutor_ids
        
        if tutors_to_add:
            tutors = (
                db.query(User)
                .filter(User.id.in_(tutors_to_add))
                .all()
            )
            
            if len(tutors) != len(tutors_to_add):
                raise HTTPException(
                    status_code=404,
                    detail="One or more tutors not found"
                )
            
            for tutor in tutors:
                assignment = CourseTutor(
                    tutor_id=tutor.id,
                    course_id=course.id,
                    status=CourseTutorStatus.ACTIVE,
                    is_primary=len(course.tutors_assigned) == 0  # First is primary
                )
                course.tutors_assigned.append(assignment)

        # Remove tutor_ids from update_data (already handled)
        del update_data["tutor_ids"]

    # Apply remaining updates
    for field, value in update_data.items():
        setattr(course, field, value)

    try:
        db.commit()
        db.refresh(course)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    return course


def delete_course(db: Session, course_id: UUID) -> None:
    """Delete a course and all related data (cascading)."""
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        db.delete(course)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def get_course_stats(db: Session, course_id: UUID) -> dict:
    """Get comprehensive course statistics."""
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Count modules
    module_count = (
        db.query(func.count(Module.id))
        .filter(Module.course_id == course_id)
        .scalar()
    )

    # Count lessons
    lesson_count = (
        db.query(func.count(Lesson.id))
        .join(Module)
        .filter(Module.course_id == course_id)
        .scalar()
    )

    # Count enrollments
    from app.models.enrollment import Enrollment
    enrollment_count = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course_id)
        .scalar()
    )

    return {
        "modules": module_count or 0,
        "lessons": lesson_count or 0,
        "students": enrollment_count or 0,
        "tutors": len([
            ct for ct in course.tutors_assigned
            if ct.status == CourseTutorStatus.ACTIVE
        ])
    }

