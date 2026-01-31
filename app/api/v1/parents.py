# from typing import Optional
# from uuid import UUID
# from fastapi import APIRouter, Depends, Query, Request
# from sqlalchemy.orm import Session

# from app.api.deps.users import get_db, get_current_user
# from app.models.user import User
# from app.schemas.parent import ParentCreate, ParentUpdate, LinkStudentRequest
# from app.services.parent_service import ParentService
# from app.utils.responses import api_response, PageSerializer

# router = APIRouter()


# @router.get("/me")
# def get_current_parent_profile(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Get current user's parent profile."""
#     parent = ParentService.get_parent_by_user_id(db, current_user.id)
    
#     if not parent:
#         return api_response(
#             success=False,
#             message="Parent profile not found for current user",
#             status_code=404,
#             path=str(request.url.path)
#         )
    
#     return api_response(
#         success=True,
#         data=parent.get_summary(),
#         message="Parent profile retrieved successfully",
#         path=str(request.url.path)
#     )


# @router.get("")
# def list_parents(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(20, ge=1, le=100, description="Items per page"),
#     search: Optional[str] = Query(None, description="Search by name, email, or occupation"),
#     is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
#     is_primary: Optional[bool] = Query(None, description="Filter by primary parent status"),
# ):
#     """
#     Get paginated list of parents.
    
#     - **Requires authentication**
#     - **Admin only** for full access
#     """
#     # Get parents
#     parents = ParentService.get_parents(
#         db=db,
#         page=page,
#         page_size=page_size,
#         search=search,
#         is_verified=is_verified,
#         is_primary=is_primary
#     )
    
#     # Use PageSerializer for consistent pagination response
#     paginator = PageSerializer(
#         request=request,
#         obj=parents,
#         resource_name="parents",
#         page=page,
#         page_size=page_size
#     )
    
#     return paginator.get_response(message="Parents retrieved successfully")


# @router.get("/{parent_id}")
# def get_parent(
#     request: Request,
#     parent_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get parent by ID.
    
#     - **Requires authentication**
#     - Parents can view their own profile
#     - Admins can view any profile
#     """
#     parent = ParentService.get_parent_by_id(db, parent_id)
#     if not parent:
#         return api_response(
#             success=False,
#             message="Parent not found",
#             status_code=404,
#             path=str(request.url.path)
#         )
    
#     # Check permissions
#     from app.services.user_service import UserService
#     if str(parent.user_id) != str(current_user.id):
#         if not UserService.is_admin(current_user):
#             return api_response(
#                 success=False,
#                 message="Not authorized to view this parent profile",
#                 status_code=403,
#                 path=str(request.url.path)
#             )
    
#     return api_response(
#         success=True,
#         data=parent.get_summary(),
#         message="Parent retrieved successfully",
#         path=str(request.url.path)
#     )


# @router.post("")
# def create_parent(
#     request: Request,
#     parent_data: ParentCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Create a new parent profile.
    
#     - **Requires authentication**
#     - Users can create their own parent profile
#     - Admins can create any parent profile
#     """
#     parent = ParentService.create_parent(
#         db=db,
#         parent_data=parent_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=parent.get_summary(),
#         message="Parent profile created successfully",
#         status_code=201,
#         path=str(request.url.path)
#     )


# @router.patch("/me")
# def update_current_parent_profile(
#     request: Request,
#     parent_data: ParentUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Update current user's parent profile."""
#     parent = ParentService.get_parent_by_user_id(db, current_user.id)
    
#     if not parent:
#         return api_response(
#             success=False,
#             message="Parent profile not found for current user",
#             status_code=404,
#             path=str(request.url.path)
#         )
    
#     updated_parent = ParentService.update_parent(
#         db=db,
#         parent_id=parent.id,
#         parent_data=parent_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_parent.get_summary(),
#         message="Parent profile updated successfully",
#         path=str(request.url.path)
#     )


# @router.patch("/{parent_id}")
# def update_parent(
#     request: Request,
#     parent_id: UUID,
#     parent_data: ParentUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update parent information.
    
#     - **Requires authentication**
#     - Parents can update themselves
#     - Admins can update any parent
#     """
#     updated_parent = ParentService.update_parent(
#         db=db,
#         parent_id=parent_id,
#         parent_data=parent_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_parent.get_summary(),
#         message="Parent profile updated successfully",
#         path=str(request.url.path)
#     )


# @router.delete("/{parent_id}")
# def delete_parent(
#     request: Request,
#     parent_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Delete a parent profile.
    
#     - **Admin only**
#     """
#     ParentService.delete_parent(db=db, parent_id=parent_id, current_user=current_user)
    
#     return api_response(
#         success=True,
#         message="Parent profile deleted successfully",
#         path=str(request.url.path)
#     )


# @router.post("/{parent_id}/students")
# def link_student_to_parent(
#     request: Request,
#     parent_id: UUID,
#     link_data: LinkStudentRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Link a student to a parent.
    
#     - **Requires authentication**
#     - Parents can link students to themselves
#     - Admins can link any student to any parent
#     """
#     updated_parent = ParentService.link_student(
#         db=db,
#         parent_id=parent_id,
#         student_id=link_data.student_id,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_parent.get_summary(),
#         message="Student linked successfully",
#         path=str(request.url.path)
#     )


# @router.delete("/{parent_id}/students/{student_id}")
# def unlink_student_from_parent(
#     request: Request,
#     parent_id: UUID,
#     student_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Unlink a student from a parent.
    
#     - **Requires authentication**
#     - Parents can unlink students from themselves
#     - Admins can unlink any student from any parent
#     """
#     updated_parent = ParentService.unlink_student(
#         db=db,
#         parent_id=parent_id,
#         student_id=student_id,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_parent.get_summary(),
#         message="Student unlinked successfully",
#         path=str(request.url.path)
#     )


# @router.get("/{parent_id}/students")
# def get_parent_students(
#     request: Request,
#     parent_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get all students linked to a parent.
    
#     - **Requires authentication**
#     - Parents can view their own students
#     - Admins can view any parent's students
#     """
#     students = ParentService.get_parent_students(
#         db=db,
#         parent_id=parent_id,
#         current_user=current_user
#     )
    
#     # Use PageSerializer for consistent response
#     paginator = PageSerializer(
#         request=request,
#         obj=students,
#         resource_name="students"
#     )
    
#     return paginator.get_response(message="Students retrieved successfully")




# # v2
# # ============================================================================
# # FILE: app/api/routes/parent.py
# # Parent-specific endpoints
# # ============================================================================

# from fastapi import APIRouter, Depends, Request
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import parent_service
# from app.api.deps.users import parent_required, get_db
# from app.utils.responses import api_response

# router = APIRouter()

# @router.get("/dashboard")
# def get_parent_dashboard_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(parent_required)
# ):
#     """Get parent dashboard data"""
#     dashboard = parent_service.get_dashboard(db, current_user.id)
#     return api_response(
#         success=True,
#         message="Dashboard data fetched successfully",
#         data=dashboard,
#         path=str(request.url.path)
#     )

# @router.get("/children")
# def get_parent_children_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(parent_required)
# ):
#     """Get parent's children"""
#     children = parent_service.get_children(db, current_user.id)
#     return api_response(
#         success=True,
#         message="Children fetched successfully",
#         data=children,
#         path=str(request.url.path)
#     )

# @router.get("/children/{child_id}/performance")
# def get_child_performance_endpoint(
#     request: Request,
#     child_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(parent_required)
# ):
#     """Get child's overall performance"""
#     performance = parent_service.get_child_performance(db, current_user.id, child_id)
#     return api_response(
#         success=True,
#         message="Child performance fetched successfully",
#         data=performance,
#         path=str(request.url.path)
#     )

# @router.get("/children/{child_id}/courses/{course_id}")
# def get_child_course_details_endpoint(
#     request: Request,
#     child_id: UUID,
#     course_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(parent_required)
# ):
#     """Get child's performance in a specific course"""
#     details = parent_service.get_child_course_details(db, current_user.id, child_id, course_id)
#     return api_response(
#         success=True,
#         message="Course details fetched successfully",
#         data=details,
#         path=str(request.url.path)
#     )





# v3

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID

from app.api.deps.users import admin_required, get_db
from app.models.parents import ParentChildren
from app.models.user import User
from app.schemas.parent import ParentChildCreate, ParentChildFilters, ParentChildUpdate
from app.services import parent_service
from app.utils.responses import PageSerializer, api_response

router = APIRouter()


@router.get("")
def list_links_endpoint(
    request: Request,
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None, regex="^(active|inactive|suspended)$"),
    parent_id: Optional[UUID] = Query(default=None),
    student_id: Optional[UUID] = Query(default=None),
    relationship: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at", regex="^(created_at|updated_at)$"),
    order: str = Query(default="desc", regex="^(asc|desc)$"),
    include_relations: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all parent-student links with filtering and pagination"""
    filters = ParentChildFilters(
        search=search,
        status=status,
        parent_id=parent_id,
        student_id=student_id,
        relationship=relationship,
        sort_by=sort_by,
        order=order,
    )
    
    query = parent_service.list_links(db, filters)
    
    def link_serializer(links):
        return links.get_summary(include_relations=include_relations)

    serializer = PageSerializer(
        request=request,
        obj=query,
        resource_name="links",
        page=page,
        page_size=page_size,
        summary_func=link_serializer,
    )
    
    # def enrollment_serializer(enrollment):
    #     return enrollment.get_summary(created_at=created_at)

    # serializer = PageSerializer(
    #     request=request,
    #     obj=enrollments,
    #     resource_name="enrollments",
    #     summary_func=enrollment_serializer,
    #     page=filters.page,
    #     page_size=filters.page_size
    # )
    
    return serializer.get_response(message="Links fetched successfully")


@router.get("/stats")
def get_link_stats(db: Session = Depends(get_db)):
    """Get parent-student link statistics"""
    stats = parent_service.get_stats(db)
    
    return api_response(
        success=True,
        data=stats,
        message="Statistics fetched successfully"
    )


@router.get("/{link_id}")
def get_link_endpoint(
    link_id: UUID,
    include_relations: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """Get a single parent-student link by ID"""
    link = db.query(ParentChildren).options(
        joinedload(ParentChildren.parent),
        joinedload(ParentChildren.student)
    ).filter(ParentChildren.id == link_id).first()
    
    if not link:
        return api_response(
            success=False,
            message="Link not found",
            status_code=404
        )
    
    return api_response(
        success=True,
        data=link.get_summary(include_relations=include_relations),
        message="Link fetched successfully"
    )


@router.post("")
def create_link_endpoint(
    link_data: ParentChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """Create a new parent-student link"""
    try:
        link = parent_service.create_link(
            db=db,
            link_data=link_data,
            linked_by_id=current_user.id
        )
        
        return api_response(
            success=True,
            data=link.get_summary(include_relations=True),
            message="Link created successfully",
            status_code=201
        )
    except ValueError as exc:
        return api_response(
            success=False,
            message=str(exc),
            status_code=400
        )


@router.patch("/{link_id}")
def update_link_endpoint(
    link_id: UUID,
    update_data: ParentChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """Update a parent-student link"""
    try:
        link = parent_service.update_link(db, link_id, update_data)
        
        return api_response(
            success=True,
            data=link.get_summary(include_relations=True),
            message="Link updated successfully"
        )
    except ValueError as exc:
        return api_response(
            success=False,
            message=str(exc),
            status_code=400
        )


@router.delete("/{link_id}")
def delete_link_endpoint(
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """Delete a parent-student link"""
    try:
        parent_service.delete_link(db, link_id)
        
        return api_response(
            success=True,
            message="Link deleted successfully"
        )
    except ValueError as exc:
        return api_response(
            success=False,
            message=str(exc),
            status_code=404
        )

