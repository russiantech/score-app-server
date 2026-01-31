# FOR BACKUP / REFFERENCE

# # ============================================================================
# # FILE: app/api/routes/users.py
# # User management endpoints
# # ============================================================================

# from fastapi import APIRouter, Depends, Request, Query
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import user_service
# from app.schemas.user import UserCreate, UserUpdateSchema, 
# from app.schemas.user_filters import UserFilters
# from app.api.deps.users import admin_required, get_current_user, get_db
# from app.utils.responses import PageSerializer, api_response

# router = APIRouter()

# @router.post("", response_model=, status_code=201, dependencies=[Depends(admin_required)])
# def create_user_endpoint(
#     request: Request,
#     data: UserCreate,
#     db: Session = Depends(get_db),
# ):
#     """
#     Create a new user (Admin only)
    
#     Payload:
#     {
#         "names": "John Doe",
#         "email": "john@example.com",
#         "phone": "+234 801 234 5678",
#         "roles": ["student"],
#         "password": "securepass123",
#         "parent_id": "uuid" // optional, for students
#     }
#     """
#     user = user_service.create_user(db, data)
#     return api_response(
#         success=True,
#         message="User created successfully",
#         data=user,
#         path=str(request.url.path),
#         status_code=201
#     )

# @router.get("", response_model=list[])
# def list_users_endpoint(
#     request: Request,
#     role: str | None = None,
#     is_active: bool | None = None,
#     search: str | None = None,
#     page: int = 1,
#     page_size: int = 20,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """
#     List all users with optional filters
    
#     Query params:
#     - role: student, tutor, parent, admin
#     - is_active: true/false
#     - search: search by name or email
#     """
#     filters = UserFilters(role=role, is_active=is_active, search=search)
#     users = user_service.list_users(db, filters=filters)
    
#     serializer = PageSerializer(
#         request=request,
#         obj=users,
#         resource_name="users",
#         page=page,
#         page_size=page_size
#     )
#     return serializer.get_response("Users fetched successfully")

# @router.get("/{user_id}", response_model=)
# def get_user_endpoint(
#     request: Request,
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """Get single user by ID"""
#     user = user_service.get_user(db, user_id)
#     return api_response(
#         success=True,
#         message="User fetched successfully",
#         data=user,
#         path=str(request.url.path)
#     )

# @router.put("/{user_id}", response_model=, dependencies=[Depends(admin_required)])
# def update_user_endpoint(
#     request: Request,
#     user_id: UUID,
#     data: UserUpdateSchema,
#     db: Session = Depends(get_db),
# ):
#     """
#     Update user (Admin only)
    
#     Payload (all optional):
#     {
#         "names": "Updated Name",
#         "phone": "+234 801 234 5678",
#         "roles": ["tutor"],
#         "password": "newpassword" // optional
#     }
#     """
#     user = user_service.update_user(db, user_id, data)
#     return api_response(
#         success=True,
#         message="User updated successfully",
#         data=user,
#         path=str(request.url.path)
#     )

# @router.delete("/{user_id}", status_code=204, dependencies=[Depends(admin_required)])
# def delete_user_endpoint(
#     request: Request,
#     user_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Delete user (Admin only)"""
#     user_service.delete_user(db, user_id)
#     return api_response(
#         success=True,
#         message="User deleted successfully",
#         path=str(request.url.path),
#         status_code=204
#     )

# @router.patch("/{user_id}/toggle-status", dependencies=[Depends(admin_required)])
# def toggle_user_status_endpoint(
#     request: Request,
#     user_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Toggle user active/inactive status"""
#     user = user_service.toggle_user_status(db, user_id)
#     return api_response(
#         success=True,
#         message=f"User {'activated' if user.is_active else 'deactivated'} successfully",
#         data=user,
#         path=str(request.url.path)
#     )



# # v2
# from typing import Optional
# from uuid import UUID
# from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
# from sqlalchemy.orm import Session

# from app.api.deps.users import admin_required, get_db, get_current_user
# from app.models.user import User
# from app.schemas.user import UserCreate, UserFilters, UserUpdateSchema, PasswordUpdate
# from app.services.user_service import UserService
# from app.utils.responses import api_response, PageSerializer

# router = APIRouter()

# @router.post("", status_code=201, dependencies=[Depends(admin_required)])
# async def create_user_endpoint(
#     request: Request,
#     data: UserCreate,
#     background_tasks: BackgroundTasks,  # ✅ NO Depends() - FastAPI auto-injects
#     db: Session = Depends(get_db),
# ):
#     """
#     Create a new user (Admin only).
    
#     - Validates email, username, phone uniqueness
#     - Assigns roles
#     - Links to parent if student
#     - Sends welcome email in background
#     """
#     user = await UserService.create_user(
#         db=db,
#         data=data,
#         background_tasks=background_tasks,
#     )

#     return api_response(
#         success=True,
#         message="User created successfully",
#         data={
#             "id": str(user.id),
#             "username": user.username,
#             "email": user.email,
#             "names": user.names,
#             "roles": user.role_names,
#             "is_active": user.is_active,
#             "created_at": user.created_at.isoformat() if user.created_at else None,
#         },
#         path=str(request.url.path),
#         status_code=201,
#     )


# @router.get("/me")
# def get_current_user_info(
#     request: Request,
#     current_user: User = Depends(get_current_user)
# ):
#     """Get current authenticated user information."""
#     return api_response(
#         success=True,
#         data=current_user.get_summary(),
#         message="User retrieved successfully",
#         path=str(request.url.path)
#     )

# # @router.get("")
# # def list_users(
# #     request: Request,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user),
# #     page: int = Query(1, ge=1, description="Page number"),
# #     page_size: int = Query(20, ge=1, le=100, description="Items per page"),
# #     search: Optional[str] = Query(None, description="Search by username, email, or name"),
# #     is_active: Optional[bool] = Query(None, description="Filter by active status"),
# #     role: Optional[str] = Query(None, description="Filter by role"),
# # ):
# #     """
# #     Get paginated list of users.
    
# #     - **Requires authentication**
# #     - **Admin only** for full access; regular users get limited info
# #     """
# #     # Get users
# #     users = UserService.list_users(
# #         db=db,
# #         page=page,
# #         page_size=page_size,
# #         search=search,
# #         is_active=is_active,
# #         role=role
# #     )
    
# #     # Use PageSerializer for consistent pagination response
# #     paginator = PageSerializer(
# #         request=request,
# #         obj=users,
# #         resource_name="users",
# #         page=page,
# #         page_size=page_size
# #     )
    
# #     return paginator.get_response(message="Users retrieved successfully")


# @router.get("", summary="List users", tags=["Users"])
# def list_users(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(20, ge=1, le=100, description="Items per page"),
#     search: Optional[str] = Query(None, description="Search by username, email, name, or phone"),
#     is_active: Optional[bool] = Query(None, description="Filter by active status"),
#     role: Optional[str] = Query(None, description="Filter by role name"),
# ):
#     """
#     Get a paginated list of users.

#     - **Requires authentication**
#     - **Admin only** for full access; regular users get limited info
#     - Supports searching by `username`, `email`, `name`, or `phone`
#     - Supports filtering by `is_active` and `role`
#     """
#     filters = UserFilters(
#         search=search,
#         is_active=is_active,
#         role=role
#     )

#     users = UserService.list_users(
#         db=db,
#         filters=filters,
#         page=page,
#         page_size=page_size
#     )

#     paginator = PageSerializer(
#         request=request,
#         obj=users,
#         resource_name="users",
#         page=page,
#         page_size=page_size
#     )

#     return paginator.get_response(message="Users retrieved successfully")

# @router.get("/{user_id}")
# def get_user(
#     request: Request,
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get user by ID.
    
#     - **Requires authentication**
#     - Users can view their own profile
#     - Admins can view any profile
#     """
#     user = UserService.get_user_by_id(db, user_id)
#     if not user:
#         return api_response(
#             success=False,
#             message="User not found",
#             status_code=404,
#             path=str(request.url.path)
#         )
    
#     # Check permissions (users can only view themselves unless admin)
#     if str(user.id) != str(current_user.id):
#         if not UserService.is_admin(current_user):
#             return api_response(
#                 success=False,
#                 message="Not authorized to view this user",
#                 status_code=403,
#                 path=str(request.url.path)
#             )
    
#     return api_response(
#         success=True,
#         data=user.get_summary(),
#         message="User retrieved successfully",
#         path=str(request.url.path)
#     )

# @router.patch("/me")
# def update_current_user(
#     request: Request,
#     user_data: UserUpdateSchema,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Update current user's information."""
#     updated_user = UserService.update_user(
#         db=db,
#         user_id=current_user.id,
#         user_data=user_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_user.get_summary(),
#         message="User updated successfully",
#         path=str(request.url.path)
#     )

# @router.put("/{user_id}")
# def update_user(
#     request: Request,
#     user_id: UUID,
#     user_data: UserUpdateSchema,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update user information.
    
#     - **Requires authentication**
#     - Users can update themselves
#     - Admins can update any user
#     """
#     updated_user = UserService.update_user(
#         db=db,
#         user_id=user_id,
#         data=user_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_user.get_summary(),
#         message="User updated successfully",
#         path=str(request.url.path)
#     )


# @router.post("/me/password")
# def update_current_user_password(
#     request: Request,
#     password_data: PasswordUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Update current user's password."""
#     UserService.update_password(
#         db=db,
#         user_id=current_user.id,
#         password_data=password_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         message="Password updated successfully",
#         path=str(request.url.path)
#     )


# @router.post("/{user_id}/password")
# def update_user_password(
#     request: Request,
#     user_id: UUID,
#     password_data: PasswordUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update user password.
    
#     - **Requires authentication**
#     - Users can only update their own password
#     """
#     UserService.update_password(
#         db=db,
#         user_id=user_id,
#         password_data=password_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         message="Password updated successfully",
#         path=str(request.url.path)
#     )


# @router.delete("/{user_id}")
# def delete_user(
#     request: Request,
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Delete (deactivate) a user.
    
#     - **Admin only**
#     - Cannot delete yourself
#     - Soft delete (sets is_active to False)
#     """
#     UserService.delete_user(db=db, user_id=user_id, current_user=current_user)
    
#     return api_response(
#         success=True,
#         message="User deleted successfully",
#         path=str(request.url.path)
#     )


# @router.post("/{user_id}/roles/{role_name}")
# def assign_role_to_user(
#     request: Request,
#     user_id: UUID,
#     role_name: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Assign a role to a user.
    
#     - **Admin only**
#     """
#     updated_user = UserService.assign_role(
#         db=db,
#         user_id=user_id,
#         role_name=role_name,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_user.get_summary(),
#         message=f"Role '{role_name}' assigned successfully",
#         path=str(request.url.path)
#     )


# @router.delete("/{user_id}/roles/{role_name}")
# def remove_role_from_user(
#     request: Request,
#     user_id: UUID,
#     role_name: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Remove a role from a user.
    
#     - **Admin only**
#     """
#     updated_user = UserService.remove_role(
#         db=db,
#         user_id=user_id,
#         role_name=role_name,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_user.get_summary(),
#         message=f"Role '{role_name}' removed successfully",
#         path=str(request.url.path)
#     )

# @router.patch("/{user_id}/toggle-status", dependencies=[Depends(admin_required)])
# def toggle_status(request: Request, user_id: UUID, db: Session = Depends(get_db)):
#     user = UserService.toggle_user_status(db, user_id)
#     return api_response(True, "User status updated", user, path=str(request.url.path))

# # 



# v3
# ============================================================================
# API: User Endpoints
# FILE: app/api/v1/users.py
# ============================================================================

from fastapi import APIRouter, Depends, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

# from app.api.deps import get_db, get_current_user, admin_required
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdateSchema,
    UserUpdateSchema,
    PasswordUpdate,
    UserFilters,
    UserRead,
)
from app.utils.responses import PageSerializer, api_response

# Import functional service (not class-based)
from app.services import user_service
from app.api.deps.users import admin_required, get_current_user, get_db


router = APIRouter()


# ============================================================================
# LIST USERS
# ============================================================================

# @router.get("", dependencies=[Depends(admin_required)])
# async def list_users_endpoint(
#     request: Request,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
#     search: Optional[str] = None,
#     is_active: Optional[bool] = None,
#     role: Optional[str] = None,
#     db: Session = Depends(get_db),
# ):
@router.get("", summary="List users")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username, email, name, or phone"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role name"),
):
    """
    Get paginated list of users with optional filtering.
    Admin only.
    """
    filters = UserFilters(
        search=search,
        is_active=is_active,
        role=role
    )
    
    users = user_service.list_users(
        db=db,
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    # return api_response(
    #     success=True,
    #     data={
    #         "users": [user.get_summary() for user in users],
    #         "page": page,
    #         "page_size": page_size,
    #     },
    #     path=str(request.url.path)
    # )
    paginator = PageSerializer(
        request=request,
        obj=users,
        resource_name="users",
        page=page,
        page_size=page_size
    )

    return paginator.get_response(message="Users retrieved successfully")


# ============================================================================
# GET USER
# ============================================================================

@router.get("/{user_id}")
async def get_user_endpoint(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user by ID.
    Users can get their own info, admins can get any user.
    """
    user = user_service.get_user_by_id(db, user_id)
    
    if not user:
        return api_response(
            success=False,
            message="User not found",
            status_code=404,
            path=str(request.url.path)
        )
    
    # Permission check
    if user.id != current_user.id and not current_user.is_admin:
        return api_response(
            success=False,
            message="Not authorized to view this user",
            status_code=403,
            path=str(request.url.path)
        )
    
    return api_response(
        success=True,
        data={"user": user.get_summary()},
        path=str(request.url.path)
    )


# ============================================================================
# CREATE USER
# ============================================================================

@router.post("", status_code=201, dependencies=[Depends(admin_required)])
async def create_user_endpoint(
    request: Request,
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new user.
    Admin only.
    """
    user = await user_service.create_user(
        db=db,
        data=data,
        background_tasks=background_tasks,
    )

    return api_response(
        success=True,
        message="User created successfully",
        # data={
        #     "user": {
        #         "id": str(user.id),
        #         "username": user.username,
        #         "email": user.email,
        #         "names": user.names,
        #         "roles": user.role_names,
        #         "is_active": user.is_active,
        #         "created_at": user.created_at.isoformat() if user.created_at else None,
        #     }
        # },
        data=user.get_summary(),
        path=str(request.url.path),
        status_code=201,
    )


# ============================================================================
# UPDATE USER
# ============================================================================

@router.patch("/{user_id}")
async def update_user_endpoint(
    request: Request,
    user_id: UUID,
    data: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update user information.
    
    - Users can update their own info (current_password required for password changes)
    - Admins can update any user (no current_password required when updating others)
    - Only provided fields will be updated
    """
    user = user_service.update_user(
        db=db,
        user_id=user_id,
        data=data,
        current_user=current_user,
    )

    return api_response(
        success=True,
        message="User updated successfully",
        data=user.get_summary(),
        path=str(request.url.path)
    )    

# ============================================================================
# UPDATE PASSWORD
# ============================================================================

@router.post("/{user_id}/password")
async def update_password_endpoint(
    request: Request,
    user_id: UUID,
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update user password.
    Users can only change their own password.
    Requires current password for verification.
    """
    user = user_service.update_password(
        db=db,
        user_id=user_id,
        data=data,
        current_user=current_user,
    )

    return api_response(
        success=True,
        message="Password updated successfully",
        path=str(request.url.path)
    )


# ============================================================================
# TOGGLE USER STATUS
# ============================================================================

@router.patch("/{user_id}/toggle-status", dependencies=[Depends(admin_required)])
async def toggle_user_status_endpoint(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle user active/inactive status.
    Admin only.
    """
    user = user_service.toggle_user_status(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )

    return api_response(
        success=True,
        message=f"User {'activated' if user.is_active else 'deactivated'} successfully",
        data={"user": user.get_summary()},
        path=str(request.url.path)
    )


# ============================================================================
# DELETE USER
# ============================================================================

@router.delete("/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user_endpoint(
    request: Request,
    user_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete user (soft delete by default).
    Admin only.
    """
    user_service.delete_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
        hard_delete=hard_delete,
    )

    return api_response(
        success=True,
        message="User deleted successfully",
        path=str(request.url.path)
    )


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

@router.post("/{user_id}/roles/{role_name}", dependencies=[Depends(admin_required)])
async def assign_role_endpoint(
    request: Request,
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign role to user.
    Admin only.
    """
    user = user_service.assign_role(
        db=db,
        user_id=user_id,
        role_name=role_name,
        current_user=current_user,
    )

    return api_response(
        success=True,
        message=f"Role '{role_name}' assigned successfully",
        data={"user": user.get_summary()},
        path=str(request.url.path)
    )


@router.delete("/{user_id}/roles/{role_name}", dependencies=[Depends(admin_required)])
async def remove_role_endpoint(
    request: Request,
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove role from user.
    Admin only.
    """
    user = user_service.remove_role(
        db=db,
        user_id=user_id,
        role_name=role_name,
        current_user=current_user,
    )

    return api_response(
        success=True,
        message=f"Role '{role_name}' removed successfully",
        data={"user": user.get_summary()},
        path=str(request.url.path)
    )


# ============================================================================
# PARENT-STUDENT RELATIONSHIPS
# ============================================================================

@router.post("/{student_id}/link-parent", dependencies=[Depends(admin_required)])
async def link_parent_endpoint(
    request: Request,
    student_id: UUID,
    parent_id: UUID = Query(..., description="Parent user ID"),
    relationship: str = Query("guardian", description="Relationship type"),
    is_primary: bool = Query(False, description="Is primary guardian"),
    db: Session = Depends(get_db),
):
    """
    Link a parent to a student.
    Admin only.
    """
    user_service.link_parent_to_student(
        db=db,
        parent_id=parent_id,
        student_id=student_id,
        relationship=relationship,
        is_primary=is_primary,
    )

    return api_response(
        success=True,
        message="Parent linked to student successfully",
        path=str(request.url.path)
    )


@router.delete("/{student_id}/unlink-parent", dependencies=[Depends(admin_required)])
async def unlink_parent_endpoint(
    request: Request,
    student_id: UUID,
    parent_id: UUID = Query(..., description="Parent user ID"),
    db: Session = Depends(get_db),
):
    """
    Unlink a parent from a student.
    Admin only.
    """
    user_service.unlink_parent_from_student(
        db=db,
        parent_id=parent_id,
        student_id=student_id,
    )

    return api_response(
        success=True,
        message="Parent unlinked from student successfully",
        path=str(request.url.path)
    )

