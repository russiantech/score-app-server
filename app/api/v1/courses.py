

# # v2
# from typing import Optional
# import uuid
# from fastapi import APIRouter, Depends, Query, Request
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import course_service
# from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate, CourseOut
# from app.api.deps.users import admin_required, get_current_user, get_db, tutor_required
# from app.utils.responses import PageSerializer, api_response

# from app.models.user import User
# from app.models.modules import Module
# from app.models.lesson import Lesson
# from app.models.course import Course

# from app.schemas.user import UserFilters
# from app.schemas.enrollment import EnrollmentFilters
# from app.services import enrollment_service

# router = APIRouter()

# @router.post(
#     "/migrate-default-modules",
#     dependencies=[Depends(admin_required)],
#     summary="Create default modules and migrate all lessons",
# )
# def migrate_all_courses_to_default_modules(
#     request: Request,
#     db: Session = Depends(get_db),
# ):
#     """
#     - Creates a default module per course if none exists
#     - Generates module titles using course code/title
#     - Moves all lessons without a module into that default module
#     - Safe to re-run
#     """

#     courses = db.query(Course).all()

#     migrated_courses = []
#     total_modules_created = 0
#     total_lessons_migrated = 0

#     for course in courses:
#         # 1️⃣ Check for existing module
#         module = (
#             db.query(Module)
#             .filter(Module.course_id == course.id)
#             .order_by(Module.order)
#             .first()
#         )

#         # 2️⃣ Create default module if none exists
#         if not module:
#             base = course.code or course.title or "Course"
#             module = Module(
#                 id=uuid.uuid4(),
#                 course_id=course.id,
#                 title=f"{base} – Module 1",
#                 order=1,
#             )
#             db.add(module)
#             db.flush()  # ensures module.id is available
#             total_modules_created += 1

#         # 3️⃣ Move unassigned lessons into module
#         updated = (
#             db.query(Lesson)
#             .filter(
#                 Lesson.course_id == course.id,
#                 Lesson.module_id.is_(None),
#             )
#             .update(
#                 {Lesson.module_id: module.id},
#                 synchronize_session=False,
#             )
#         )

#         total_lessons_migrated += updated

#         migrated_courses.append(
#             {
#                 "course_id": str(course.id),
#                 "course_title": course.title,
#                 "module_id": str(module.id),
#                 "module_title": module.title,
#                 "lessons_moved": updated,
#             }
#         )

#     db.commit()

#     return api_response(
#         success=True,
#         message="Courses migrated to default modules successfully",
#         data={
#             "courses_processed": len(courses),
#             "modules_created": total_modules_created,
#             "lessons_migrated": total_lessons_migrated,
#             "details": migrated_courses,
#         },
#         path=str(request.url.path),
#     )


# @router.post("", response_model=CourseOut, status_code=201, dependencies=[Depends(admin_required)])
# def create_course_endpoint(
#     request: Request,
#     data: CourseCreate,
#     db: Session = Depends(get_db),
# ):
#     course = course_service.create_course(db, data)
#     return api_response(
#         success=True,
#         message="Course created successfully",
#         data=course,
#         path=str(request.url.path),
#         status_code=201
#     )


# @router.get(
#     "",
#     response_model=list[CourseOut],
#     summary="List courses",
#     description="Retrieve a paginated list of courses with optional filters",
# )
# def list_courses_endpoint(
#     request: Request,
#     search: Optional[str] = Query(
#         default=None,
#         description="Search by course title, code, or description",
#     ),
#     status: Optional[str] = Query(
#         default=None,
#         regex="^(active|inactive)$",
#         description="Filter courses by status",
#     ),
#     tutor_id: Optional[UUID] = Query(
#         default=None,
#         description="Filter by tutor ID",
#     ),
#     sort_by: str = Query(
#         default="created_at",
#         regex="^(created_at|title|code)$",
#         description="Sort by field",
#     ),
#     order: str = Query(
#         default="desc",
#         regex="^(asc|desc)$",
#         description="Sort order",
#     ),
#     page: int = Query(
#         default=1,
#         ge=1,
#         description="Page number (starts from 1)",
#     ),
#     page_size: int = Query(
#         default=20,
#         ge=1,
#         le=100,
#         description="Number of items per page",
#     ),
#     include_relations: bool = Query(default=False),  # ← Optional control
#     db: Session = Depends(get_db),
# ):
#     # Create filters object
#     filters = CourseFilters(
#         search=search,
#         status=status,
#         tutor_id=tutor_id,
#         sort_by=sort_by,
#         order=order,
#         page=page,
#         page_size=page_size,
#     )

#     # Fetch filtered and paginated courses
#     courses, total = course_service.list_courses(db, filters=filters)

#     def course_serializer(course):
#         return course.get_summary(include_relations=include_relations)

#     # Paginate & serialize
#     serializer = PageSerializer(
#         request=request,
#         obj=courses,
#         resource_name="courses",
#         page=page,
#         page_size=page_size,
#         # total=total,  # Pass total to serializer
#         summary_func=course_serializer,
#     )
    
#     return serializer.get_response(
#         message="Courses fetched successfully"
#     )

# @router.get("/{course_id}")
# def get_single_course(
#     request: Request,
#     course_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     course = course_service.get_course_by_id(db, course_id)
#     return {
#         "data": course.get_summary(include_relations=True)
#     }
#     # return api_response(
#     #     success=True,
#     #     message="Course fetched successfully",
#     #     data=course,
#     #     path=str(request.url.path)
#     # )

# @router.put("/{course_id}", response_model=CourseOut, dependencies=[Depends(admin_required)])
# def update_course_endpoint(
#     request: Request,
#     course_id: UUID,
#     data: CourseUpdate,
#     db: Session = Depends(get_db),
# ):
#     """ 
#     Example payload in request:
#     {
#         "code": "MOB301",
#         "title": "Mobile App Development",
#         "description": "Build cross-platform mobile apps with React Native and Flutter.",
#         "total_lessons": 0,
#         "duration_weeks": 0,
#         "difficulty_level": "beginner",
#         "is_active": true,
#         "is_public": true,
#         "instructor_ids": [
#             "3fa85f64-5717-4562-b3fc-2c963f66afa6"
#         ]
#     }

#     """
#     course = course_service.update_course(db, course_id, data)
#     return api_response(
#         success=True,
#         message="Course updated successfully",
#         data=course,
#         path=str(request.url.path)
#     )

# @router.delete("/{course_id}", status_code=204, dependencies=[Depends(admin_required)])
# def delete_course_endpoint(
#     request: Request,
#     course_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     course_service.delete_course(db, course_id)
#     return api_response(
#         success=True,
#         message="Course deleted successfully",
#         path=str(request.url.path),
#         status_code=204
#     )

# @router.get("/{course_id}/modules")
# def get_course_modules(request: Request, course_id: UUID, db: Session = Depends(get_db)):
#     course = course_service.get_course(db, course_id)
#     return api_response(True, "Modules fetched", course.modules, path=str(request.url.path))


# @router.get(
#     "/{course_id}/enrollments",
#     summary="Get course enrollments",
# )
# def get_course_enrollments(
#     request: Request,
#     course_id: UUID,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(tutor_required),
# ):
#     filters = EnrollmentFilters(
#         course_id=course_id,
#         page=page,
#         page_size=page_size,
#     )

#     enrollments, total = enrollment_service.list_enrollments(
#         db=db,
#         filters=filters,
#     )

#     serializer = PageSerializer(
#         request=request,
#         obj=enrollments,
#         resource_name="enrollments",
#         page=page,
#         page_size=page_size,
#         summary_func=lambda e: e.get_summary(include_relations=True),
#     )

#     return serializer.get_response("Course enrollments fetched")

# @router.get(
#     "/{course_id}/lessons",
#     summary="Get course lessons",
# )
# def get_course_lessons(
#     request: Request,
#     course_id: UUID,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(tutor_required),
# ):
#     filters = EnrollmentFilters(
#         course_id=course_id,
#         page=page,
#         page_size=page_size,
#     )

#     enrollments, total = enrollment_service.list_enrollments(
#         db=db,
#         filters=filters,
#     )

#     serializer = PageSerializer(
#         request=request,
#         obj=enrollments,
#         resource_name="enrollments",
#         page=page,
#         page_size=page_size,
#         summary_func=lambda e: e.get_summary(include_relations=True),
#     )

#     return serializer.get_response("Course lessons fetched")





# v2
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from uuid import UUID
from sqlalchemy.orm import Session

from app.services import course_service
from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate, CourseOut
from app.api.deps.users import admin_required, get_current_user, get_db, tutor_required
from app.utils.responses import PageSerializer, api_response
from app.models.user import User
from app.models.modules import Module
from app.models.lesson import Lesson
from app.models.course import Course
from app.schemas.enrollment import EnrollmentFilters
from app.services import enrollment_service

router = APIRouter()


@router.post(
    "/migrate-default-modules",
    dependencies=[Depends(admin_required)],
    summary="Create default modules and migrate all lessons",
)
def migrate_all_courses_to_default_modules(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    - Creates a default module per course if none exists
    - Generates module titles using course code/title
    - Moves all lessons without a module into that default module
    - Safe to re-run
    """
    courses = db.query(Course).all()

    migrated_courses = []
    total_modules_created = 0
    total_lessons_migrated = 0

    for course in courses:
        # Check for existing module
        module = (
            db.query(Module)
            .filter(Module.course_id == course.id)
            .order_by(Module.order)
            .first()
        )

        # Create default module if none exists
        if not module:
            base = course.code or course.title or "Course"
            module = Module(
                id=uuid.uuid4(),
                course_id=course.id,
                title=f"{base} – Module 1",
                order=1,
            )
            db.add(module)
            db.flush()
            total_modules_created += 1

        # Move unassigned lessons into module
        updated = (
            db.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.module_id.is_(None),
            )
            .update(
                {Lesson.module_id: module.id},
                synchronize_session=False,
            )
        )

        total_lessons_migrated += updated

        migrated_courses.append({
            "course_id": str(course.id),
            "course_title": course.title,
            "module_id": str(module.id),
            "module_title": module.title,
            "lessons_moved": updated,
        })

    db.commit()

    return api_response(
        success=True,
        message="Courses migrated to default modules successfully",
        data={
            "courses_processed": len(courses),
            "modules_created": total_modules_created,
            "lessons_migrated": total_lessons_migrated,
            "details": migrated_courses,
        },
        path=str(request.url.path),
    )

# Debug endpoint - Remove after debugging is complete
@router.get("/{course_id}/debug", summary="Debug course data loading")
def debug_course_data(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Debug endpoint to verify course, modules, and lessons are loaded correctly.
    This endpoint should be removed in production.
    """
    from sqlalchemy.orm import joinedload
    from app.models.modules import Module
    from app.models.lesson import Lesson
    from app.models.tutors import CourseTutor
    from fastapi import HTTPException
    
    # Load course with explicit eager loading
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .options(
            joinedload(Course.tutors_assigned).joinedload(CourseTutor.tutor),
            joinedload(Course.modules).joinedload(Module.lessons),
            joinedload(Course.images)
        )
        .first()
    )
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Return complete course data in standard format
    return api_response(
        success=True,
        message="Course data loaded successfully (debug mode)",
        data={"course": course.get_summary(include_relations=True)},
        path=str(request.url.path)
    )
    
@router.post(
    "",
    response_model=CourseOut,
    status_code=201,
    dependencies=[Depends(admin_required)]
)
def create_course_endpoint(
    request: Request,
    data: CourseCreate,
    db: Session = Depends(get_db),
):
    """Create a new course."""
    course = course_service.create_course(db, data)
    return api_response(
        success=True,
        message="Course created successfully",
        data=course.get_summary(include_relations=True),
        path=str(request.url.path),
        status_code=201
    )


@router.get(
    "",
    summary="List courses",
    description="Retrieve a paginated list of courses with optional filters",
)
def list_courses_endpoint(
    request: Request,
    search: Optional[str] = Query(
        default=None,
        description="Search by course title, code, or description",
    ),
    status: Optional[str] = Query(
        default=None,
        pattern="^(active|inactive)$",
        description="Filter courses by status",
    ),
    tutor_id: Optional[UUID] = Query(
        default=None,
        description="Filter by tutor ID",
    ),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|title|code)$",
        description="Sort by field",
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (starts from 1)",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    include_relations: bool = Query(
        default=False,
        description="Include related tutors, modules, and lessons"
    ),
    db: Session = Depends(get_db),
):
    """Get paginated list of courses with filters."""
    filters = CourseFilters(
        search=search,
        status=status,
        tutor_id=tutor_id,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )

    courses, total = course_service.list_courses(db, filters=filters)

    serializer = PageSerializer(
        request=request,
        obj=courses,
        resource_name="courses",
        page=page,
        page_size=page_size,
        summary_func=lambda c: c.get_summary(include_relations=include_relations),
    )
    
    return serializer.get_response(message="Courses fetched successfully")


# @router.get("/{course_id}", summary="Get course by ID")
# def get_single_course(
#     request: Request,
#     course_id: UUID,
#     include_relations: bool = Query(
#         default=True,
#         description="Include tutors, modules, and lessons"
#     ),
#     db: Session = Depends(get_db),
# ):
#     """Get a single course with all details."""
#     course = course_service.get_course_by_id(
#         db,
#         course_id,
#         include_relations=include_relations
#     )
    
#     # return api_response(
#     #     success=True,
#     #     message="Course fetched successfully",
#     #     data=course.get_summary(include_relations=True),
#     #     path=str(request.url.path)
#     # )
    
#     # Return complete course data in standard format
#     return api_response(
#         success=True,
#         message="Course data loaded successfully (debug mode)",
#         data={"course": course.get_summary(include_relations=True)},
#         path=str(request.url.path)
#     )


@router.get(
    "/{course_id}",
    summary="Get course by ID with optional relations and attendance",
)
def get_course_by_id_x(
    request: Request,
    course_id: UUID,
    include_relations: bool = Query(False),
    include_attendance: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Get course by ID with optional relations and attendance statistics.
    """

    course_data = course_service.get_course_with_optional_attendance(
        db=db,
        course_id=course_id,
        include_relations=include_relations,
        include_attendance=include_attendance,
    )

    return api_response(
        success=True,
        message="Course retrieved successfully",
        data={"course": course_data},
        path=str(request.url.path),
    )


@router.get("/{course_id}/performance", summary="Get course statistics")
@router.get("/{course_id}/stats", summary="Get course statistics")
def get_course_stats(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
):
    """Get comprehensive course statistics."""
    stats = course_service.get_course_stats(db, course_id)
    
    return api_response(
        success=True,
        message="Course statistics fetched successfully",
        data=stats,
        path=str(request.url.path)
    )

@router.put(
    "/{course_id}",
    response_model=CourseOut,
    dependencies=[Depends(admin_required)]
)
def update_course_endpoint(
    request: Request,
    course_id: UUID,
    data: CourseUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a course.
    
    Example payload:
    ```json
    {
        "code": "MOB301",
        "title": "Mobile App Development",
        "description": "Build cross-platform mobile apps",
        "duration_weeks": 12,
        "difficulty_level": "intermediate",
        "is_active": true,
        "tutor_ids": ["uuid-here"]
    }
    ```
    """
    course = course_service.update_course(db, course_id, data)
    
    return api_response(
        success=True,
        message="Course updated successfully",
        data=course.get_summary(include_relations=True),
        path=str(request.url.path)
    )


@router.delete(
    "/{course_id}",
    status_code=204,
    dependencies=[Depends(admin_required)]
)
def delete_course_endpoint(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a course and all related data."""
    course_service.delete_course(db, course_id)
    
    return api_response(
        success=True,
        message="Course deleted successfully",
        path=str(request.url.path),
        status_code=204
    )


@router.get(
    "/{course_id}/enrollments",
    summary="Get course enrollments",
)
def get_course_enrollments(
    request: Request,
    course_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(tutor_required),
):
    """Get all enrollments for a course."""
    filters = EnrollmentFilters(
        course_id=course_id,
        page=page,
        page_size=page_size,
    )

    enrollments, total = enrollment_service.list_enrollments(
        db=db,
        filters=filters,
    )

    serializer = PageSerializer(
        request=request,
        obj=enrollments,
        resource_name="enrollments",
        page=page,
        page_size=page_size,
        summary_func=lambda e: e.get_summary(include_relations=True),
    )

    return serializer.get_response(message="Course enrollments fetched successfully")




# # 
# def serialize_lesson(lesson):
#     return {
#         "id": lesson.id,
#         "title": lesson.title,
#         "order": lesson.order,
#         "attendance_count": getattr(lesson, "attendance_count", 0),
#         "present_count": getattr(lesson, "present_count", 0),
#         "attendance_rate": getattr(lesson, "attendance_rate", 0),
#     }


# def serialize_module(module):
#     return {
#         "id": module.id,
#         "title": module.title,
#         "lessons": [
#             serialize_lesson(l) for l in (module.lessons or [])
#         ],
#     }


# def serialize_course(course):
#     return {
#         "id": course.id,
#         "title": course.title,
#         "modules": [
#             serialize_module(m) for m in (course.modules or [])
#         ],
#     }

# @router.get("/{course_id}/x", summary="Get course by ID with optional relations and attendance")
# def get_course_by_id_x(
#     course_id: UUID,
#     include_relations: bool = Query(False),
#     include_attendance: bool = Query(False),
#     db: Session = Depends(get_db),
#     # current_user = Depends(get_current_user)
# ):
#     """
#     Get course by ID with optional relations and attendance statistics.
    
#     Parameters:
#     - include_relations: Include modules and lessons
#     - include_attendance: Include attendance stats for lessons (requires include_relations=True)
#     """
    
#     # Build query
#     query = db.query(Course)
    
#     if include_relations:
#         query = query.options(
#             joinedload(Course.modules).joinedload(Module.lessons)
#         )
    
#     course = query.filter(Course.id == course_id).first()
    
#     if not course:
#         raise HTTPException(
#             status_code=404,
#             detail="Course not found"
#         )
    
#     # Enrich lessons with attendance statistics if requested
#     if include_attendance and include_relations and course.modules:
#         # Collect all lesson IDs
#         lesson_ids = []
#         for module in course.modules:
#             if module.lessons:
#                 lesson_ids.extend([lesson.id for lesson in module.lessons])
        
#         if lesson_ids:
#             # Batch query all attendance stats in one query
#             attendance_stats = db.query(
#                 Attendance.lesson_id,
#                 func.count(Attendance.id).label('total'),
#                 func.sum(
#                     case(
#                         (Attendance.status == AttendanceStatus.PRESENT, 1),
#                         else_=0
#                     )
#                 ).label('present')
#             ).filter(
#                 Attendance.lesson_id.in_(lesson_ids)
#             ).group_by(
#                 Attendance.lesson_id
#             ).all()
            
#             # Create lookup dictionary
#             stats_lookup = {
#                 stat.lesson_id: {
#                     'total': stat.total or 0,
#                     'present': int(stat.present or 0)
#                 }
#                 for stat in attendance_stats
#             }
            
#             # Apply stats to each lesson
#             for module in course.modules:
#                 if module.lessons:
#                     for lesson in module.lessons:
#                         if lesson.id in stats_lookup:
#                             stats = stats_lookup[lesson.id]
#                             lesson.attendance_count = stats['total']
#                             lesson.present_count = stats['present']
                            
#                             # Calculate rate
#                             if stats['total'] > 0:
#                                 lesson.attendance_rate = round(
#                                     (stats['present'] / stats['total']) * 100,
#                                     1
#                                 )
#                             else:
#                                 lesson.attendance_rate = 0
#                         else:
#                             # No attendance records yet
#                             lesson.attendance_count = 0
#                             lesson.present_count = 0
#                             lesson.attendance_rate = 0
    
#     # return api_response(
#     #     success=True,
#     #     message="Course retrieved successfully",
#     #     data={"course": course}
#     # )
    
#     return api_response(
#     success=True,
#     message="Course retrieved successfully",
#     data={
#         "course": serialize_course(course)
#     }
# )

# from app.models.attendance import Attendance
# from app.schemas.attendance import AttendanceStatus
# from sqlalchemy.orm import joinedload
# from sqlalchemy import func, case

