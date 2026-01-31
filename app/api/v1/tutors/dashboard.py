
from fastapi import Depends, Query, Request
from uuid import UUID
from sqlalchemy.orm import Session

# from app.services import tutor_service
from app.api.deps.users import tutor_required, get_db
from app.utils.responses import PageSerializer, api_response

# from . import router
from fastapi import APIRouter

from app.services.tutors.dashboard import *

router = APIRouter(
    prefix="/tutors",
    tags=["Tutor"],
)

@router.get(
    "/dashboard",
    summary="Get tutor dashboard",
    description="Get dashboard data for the authenticated tutor including courses, students, and lessons"
)
def get_tutor_dashboard_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Get tutor dashboard data.
    Returns overview statistics and course information for the authenticated tutor.
    """
    dashboard = get_dashboard(db, current_user.id)
    
    return api_response(
        success=True,
        message="Dashboard data fetched successfully",
        data=dashboard,
        path=str(request.url.path)
    )


@router.get(
    "/my-courses",
    summary="Get my courses",
    description="Get all courses assigned to the authenticated tutor"
)
def get_my_courses_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required),
    include_relations: bool = Query(default=False),  # ← Optional control
):
    """
    Get courses assigned to the authenticated tutor.
    This endpoint is used by tutors to see their own course assignments.
    """
    courses = get_tutor_courses(db, current_user.id)
    
    # return api_response(
    #     success=True,
    #     message="Courses fetched successfully",
    #     data=courses,
    #     path=str(request.url.path)
    # )
    def course_serializer(course):
        return course.get_summary(include_relations=include_relations)

    serializer = PageSerializer(
        request=request,
        obj=courses,
        resource_name="courses",
        # summary_func=course_serializer,
        # page=filters.page,
        # page_size=filters.page_size
    )

    return serializer.get_response("Courses fetched successfully")



# @router.get(
#     "/courses",
#     summary="Get tutor courses",
#     description="Get all courses assigned to this tutor (alias for /my-courses)"
# )
# def get_tutor_courses_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     """
#     Get courses assigned to this tutor.
#     This is an alias for /my-courses for backward compatibility.
#     """
#     courses = get_tutor_courses(db, current_user.id)
    
#     return api_response(
#         success=True,
#         message="Courses fetched successfully",
#         data=courses,
#         path=str(request.url.path)
#     )


@router.get(
    "/courses/{course_id}/students",
    summary="Get course students",
    description="Get all students enrolled in a specific course taught by this tutor"
)
def get_course_students_endpoint(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Get students enrolled in a course.
    Verifies that the authenticated tutor has access to this course.
    """
    students = get_course_students(db, course_id, current_user.id)
    
    return api_response(
        success=True,
        message="Students fetched successfully",
        data=students,
        path=str(request.url.path)
    )


@router.get(
    "/workload",
    summary="Get tutor workload",
    description="Get detailed workload information for the authenticated tutor"
)
def get_tutor_workload_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Get detailed workload information for the authenticated tutor.
    Returns course count, student count, and detailed course information.
    """
    workload = get_tutor_workload(db, current_user.id)
    
    return api_response(
        success=True,
        message="Workload data fetched successfully",
        data=workload,
        path=str(request.url.path)
    )