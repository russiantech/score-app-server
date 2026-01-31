# # ============================================================================
# # FILE: app/api/routes/admin.py
# # Admin-specific endpoints
# # ============================================================================

# from fastapi import APIRouter, Depends, Request
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import admin_service, user_service, course_service, enrollment_service
# from app.schemas.admin import AdminStatsOut, RecentActivityOut
# from app.schemas.user import UserCreate, UserUpdateSchema
# from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut
# from app.api.deps.users import admin_required, get_db
# from app.utils.responses import PageSerializer, api_response

# router = APIRouter()

# # ============================================================================
# # DASHBOARD ENDPOINTS
# # ============================================================================

# @router.get("/dashboard")
# def get_admin_dashboard_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """Get complete dashboard data (stats + recent activities)"""
#     dashboard_data = admin_service.get_dashboard_overview(db)
#     return api_response(
#         success=True,
#         message="Dashboard data fetched successfully",
#         data=dashboard_data,
#         path=str(request.url.path)
#     )

# @router.get("/stats", response_model=AdminStatsOut)
# def get_admin_stats_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """Get admin statistics"""
#     stats = admin_service.get_statistics(db)
#     return api_response(
#         success=True,
#         message="Statistics fetched successfully",
#         data=stats,
#         path=str(request.url.path)
#     )

# @router.get("/activities", response_model=list[RecentActivityOut])
# def get_recent_activities_endpoint(
#     request: Request,
#     limit: int = 10,
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """Get recent system activities"""
#     activities = admin_service.get_recent_activities(db, limit=limit)
#     return api_response(
#         success=True,
#         message="Recent activities fetched successfully",
#         data=activities,
#         path=str(request.url.path)
#     )

# # ============================================================================
# # TUTOR ASSIGNMENT ENDPOINTS
# # ============================================================================

# @router.post("/courses/{course_id}/assign-tutor", dependencies=[Depends(admin_required)])
# def assign_tutor_to_course_endpoint(
#     request: Request,
#     course_id: UUID,
#     tutor_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """
#     Assign a tutor to a course
    
#     Payload: { "tutor_id": "uuid" }
#     """
#     result = course_service.assign_tutor(db, course_id, tutor_id)
#     return api_response(
#         success=True,
#         message="Tutor assigned successfully",
#         data=result,
#         path=str(request.url.path)
#     )

# @router.delete("/courses/{course_id}/assign-tutor/{tutor_id}", dependencies=[Depends(admin_required)])
# def remove_tutor_from_course_endpoint(
#     request: Request,
#     course_id: UUID,
#     tutor_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Remove tutor from course"""
#     course_service.remove_tutor(db, course_id, tutor_id)
#     return api_response(
#         success=True,
#         message="Tutor removed successfully",
#         path=str(request.url.path),
#         status_code=204
#     )

# # ============================================================================
# # PARENT-CHILD LINKING ENDPOINTS
# # ============================================================================

# @router.post("/parent-child-links", dependencies=[Depends(admin_required)])
# def create_parent_child_link_endpoint(
#     request: Request,
#     parent_id: UUID,
#     student_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """
#     Link a student to a parent
    
#     Payload: { "parent_id": "uuid", "student_id": "uuid" }
#     """
#     link = user_service.link_parent_to_student(db, parent_id, student_id)
#     return api_response(
#         success=True,
#         message="Parent-child link created successfully",
#         data=link,
#         path=str(request.url.path),
#         status_code=201
#     )

# @router.get("/parent-child-links")
# def list_parent_child_links_endpoint(
#     request: Request,
#     page: int = 1,
#     page_size: int = 20,
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """List all parent-child relationships"""
#     links = user_service.list_parent_child_links(db)
#     serializer = PageSerializer(
#         request=request,
#         obj=links,
#         resource_name="links",
#         page=page,
#         page_size=page_size
#     )
#     return serializer.get_response("Parent-child links fetched successfully")

# @router.delete("/parent-child-links/{parent_id}/{student_id}", dependencies=[Depends(admin_required)])
# def remove_parent_child_link_endpoint(
#     request: Request,
#     parent_id: UUID,
#     student_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Remove parent-child link"""
#     user_service.unlink_parent_from_student(db, parent_id, student_id)
#     return api_response(
#         success=True,
#         message="Parent-child link removed successfully",
#         path=str(request.url.path),
#         status_code=204
#     )




# v2
# ============================================================================
# FILE: app/api/routes/admin.py
# Admin-specific endpoints
# ============================================================================

from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional

from app.services import admin_service, user_service, course_service, enrollment_service
from app.schemas.admin import AdminStatsOut, RecentActivityOut
from app.schemas.user import UserCreate, UserUpdateSchema, UserRead
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut
from app.api.deps.users import admin_required, get_db
from app.utils.responses import PageSerializer, api_response

router = APIRouter()

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard")
def get_admin_dashboard_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Get complete dashboard data (stats + recent activities)"""
    dashboard_data = admin_service.get_dashboard_overview(db)
    return api_response(
        success=True,
        message="Dashboard data fetched successfully",
        data=dashboard_data,
        path=str(request.url.path)
    )

@router.get("/stats", response_model=AdminStatsOut)
def get_admin_stats_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Get admin statistics"""
    stats = admin_service.get_statistics(db)
    return api_response(
        success=True,
        message="Statistics fetched successfully",
        data=stats,
        path=str(request.url.path)
    )

@router.get("/activities", response_model=List[RecentActivityOut])
def get_recent_activities_endpoint(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Get recent system activities"""
    activities = admin_service.get_recent_activities(db, limit=limit)
    return api_response(
        success=True,
        message="Recent activities fetched successfully",
        data=activities,
        path=str(request.url.path)
    )

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/users", response_model=UserRead, status_code=201)
def create_user_endpoint(
    request: Request,
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    Create a new user (Admin only)
    
    Payload:
    {
        "names": "John Doe",
        "email": "john@example.com",
        "phone": "+234 801 234 5678",
        "roles": ["student"],
        "password": "securepass123",
        "parent_id": "uuid" // optional, for students
    }
    """
    user = user_service.create_user(db, data)
    return api_response(
        success=True,
        message="User created successfully",
        data=user,
        path=str(request.url.path),
        status_code=201
    )

@router.get("/users", response_model=List[UserRead])
def list_users_endpoint(
    request: Request,
    role: Optional[str] = Query(None, description="Filter by role: student, tutor, parent, admin"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    List all users with optional filters (Admin only)
    """
    # Build filters
    filters = {}
    if role:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    if search:
        filters["search"] = search
    
    users = user_service.list_users(db, filters=filters)
    
    serializer = PageSerializer(
        request=request,
        obj=users,
        resource_name="users",
        page=page,
        page_size=page_size
    )
    return serializer.get_response("Users fetched successfully")

@router.get("/users/{user_id}", response_model=UserRead)
def get_user_endpoint(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Get single user by ID (Admin only)"""
    user = user_service.get_user(db, user_id)
    return api_response(
        success=True,
        message="User fetched successfully",
        data=user,
        path=str(request.url.path)
    )

@router.put("/users/{user_id}", response_model=UserRead)
def update_user_endpoint(
    request: Request,
    user_id: UUID,
    data: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    Update user (Admin only)
    
    Payload (all optional):
    {
        "names": "Updated Name",
        "phone": "+234 801 234 5678",
        "roles": ["tutor"],
        "password": "newpassword" // optional
    }
    """
    user = user_service.update_user(db, user_id, data)
    return api_response(
        success=True,
        message="User updated successfully",
        data=user,
        path=str(request.url.path)
    )

@router.delete("/users/{user_id}", status_code=204)
def delete_user_endpoint(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Delete user (Admin only)"""
    user_service.delete_user(db, user_id)
    return api_response(
        success=True,
        message="User deleted successfully",
        path=str(request.url.path),
        status_code=204
    )

@router.patch("/users/{user_id}/toggle-status", response_model=UserRead)
def toggle_user_status_endpoint(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Toggle user active/inactive status (Admin only)"""
    user = user_service.toggle_user_status(db, user_id)
    return api_response(
        success=True,
        message=f"User {'activated' if user.is_active else 'deactivated'} successfully",
        data=user,
        path=str(request.url.path)
    )

# ============================================================================
# TUTOR ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/courses/{course_id}/assign-tutor")
def assign_tutor_to_course_endpoint(
    request: Request,
    course_id: UUID,
    tutor_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    Assign a tutor to a course (Admin only)
    """
    try:
        result = course_service.assign_tutor(db, course_id, tutor_id)
        return api_response(
            success=True,
            message="Tutor assigned successfully",
            data=result,
            path=str(request.url.path)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/courses/{course_id}/assign-tutor/{tutor_id}", status_code=204)
def remove_tutor_from_course_endpoint(
    request: Request,
    course_id: UUID,
    tutor_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Remove tutor from course (Admin only)"""
    try:
        course_service.remove_tutor(db, course_id, tutor_id)
        return api_response(
            success=True,
            message="Tutor removed successfully",
            path=str(request.url.path),
            status_code=204
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ============================================================================
# PARENT-CHILD LINKING ENDPOINTS
# ============================================================================

@router.post("/parent-child-links", status_code=201)
def create_parent_child_link_endpoint(
    request: Request,
    parent_id: UUID,
    student_id: UUID,
    relationship: str = Query("guardian", description="Relationship type: biological, guardian, adoptive"),
    is_primary: bool = Query(False, description="Whether this is the primary parent"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    Link a student to a parent (Admin only)
    """
    try:
        link = user_service.link_parent_to_student(
            db, 
            parent_id, 
            student_id, 
            relationship, 
            is_primary
        )
        return api_response(
            success=True,
            message="Parent-child link created successfully",
            data=link,
            path=str(request.url.path),
            status_code=201
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/parent-child-links")
def list_parent_child_links_endpoint(
    request: Request,
    parent_id: Optional[UUID] = Query(None, description="Filter by parent ID"),
    student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """List all parent-child relationships (Admin only)"""
    filters = {}
    if parent_id:
        filters["parent_id"] = parent_id
    if student_id:
        filters["student_id"] = student_id
    
    links = user_service.list_parent_child_links(db, filters=filters)
    
    serializer = PageSerializer(
        request=request,
        obj=links,
        resource_name="links",
        page=page,
        page_size=page_size
    )
    return serializer.get_response("Parent-child links fetched successfully")

@router.delete("/parent-child-links/{parent_id}/{student_id}", status_code=204)
def remove_parent_child_link_endpoint(
    request: Request,
    parent_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Remove parent-child link (Admin only)"""
    try:
        user_service.unlink_parent_from_student(db, parent_id, student_id)
        return api_response(
            success=True,
            message="Parent-child link removed successfully",
            path=str(request.url.path),
            status_code=204
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ============================================================================
# ENROLLMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/enrollments", response_model=EnrollmentOut, status_code=201)
def create_enrollment_endpoint(
    request: Request,
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """
    Enroll a student in a course (Admin only)
    
    Payload:
    {
        "student_id": "uuid",
        "course_id": "uuid"
    }
    """
    try: 
        enrollment = enrollment_service.enroll_student(db, data.student_id, data.course_id)
        return api_response(
            success=True,
            message="Student enrolled successfully",
            data=enrollment,
            path=str(request.url.path),
            status_code=201
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# @router.get("/enrollments", response_model=List[EnrollmentOut])
# def list_enrollments_endpoint(
#     request: Request,
#     course_id: Optional[UUID] = Query(None, description="Filter by course ID"),
#     student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """
#     List enrollments with optional filters (Admin only)
#     """
#     filters = {}
#     if course_id:
#         filters["course_id"] = course_id
#     if student_id:
#         filters["student_id"] = student_id
    
#     enrollments, total = enrollment_service.list_enrollments(
#         db=db,
#         filters=filters
#     )

#     serializer = PageSerializer(
#         request=request,
#         obj=enrollments,
#         resource_name="enrollments",
#         page=page,
#         page_size=page_size,
#     )

#     return serializer.get_response("Enrollments fetched successfully")



@router.delete("/enrollments/{enrollment_id}", status_code=204)
def delete_enrollment_endpoint(
    request: Request,
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Unenroll student from course (Admin only)"""
    try:
        enrollment_service.unenroll_student(db, enrollment_id)
        return api_response(
            success=True,
            message="Student unenrolled successfully",
            path=str(request.url.path),
            status_code=204
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ============================================================================
# COURSE MANAGEMENT ENDPOINTS (For completeness)
# ============================================================================

@router.get("/courses")
def list_courses_admin_endpoint(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    tutor_id: Optional[UUID] = Query(None, description="Filter by tutor ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """List all courses with admin privileges"""
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if tutor_id:
        filters["tutor_id"] = tutor_id
    
    courses = course_service.list_courses(db, filters=filters)
    
    serializer = PageSerializer(
        request=request,
        obj=courses,
        resource_name="courses",
        page=page,
        page_size=page_size
    )
    return serializer.get_response("Courses fetched successfully")

# ============================================================================
# LESSON MANAGEMENT ENDPOINTS (Admin override)
# ============================================================================

@router.delete("/lessons/{lesson_id}", status_code=204)
def admin_delete_lesson_endpoint(
    request: Request,
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    """Delete lesson (Admin only - can delete any lesson)"""
    from app.services import lesson_service
    
    try:
        lesson_service.delete_lesson(db, lesson_id)
        return api_response(
            success=True,
            message="Lesson deleted successfully",
            path=str(request.url.path),
            status_code=204
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
