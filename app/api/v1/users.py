# # ============================================================================
# # ROUTER: Users
# # FILE: app/routers/users.py
# # ============================================================================

# """
# User resource endpoints.
# Handles CRUD, avatar upload, role management, and parent-student linking.
# """

# from uuid import UUID

# from fastapi import APIRouter, Depends, File, Query, UploadFile, status
# from sqlalchemy.orm import Session

# # from app.database import get_db
# # from app.core.security.dependencies import get_current_user
# from app.api.deps.users import get_current_user, get_db
# from app.models.user import User
# from app.schemas.user import UserCreate, UserUpdateSchema, UserResponse, PasswordUpdate, UserFilters
# from app.utils.responses import api_response

# from app.services.user_service import (
#     list_users,
#     get_user,
#     create_user,
#     update_user,
#     update_user_avatar,
#     update_password,
#     delete_user,
#     toggle_user_status,
#     assign_role,
#     remove_role,
#     link_parent_to_student,
#     unlink_parent_from_student,
# )

# # router = APIRouter(prefix="/users", tags=["Users"])
# router = APIRouter()


# # ============================================================================
# # LIST / FETCH
# # ============================================================================

# @router.get("")
# def get_users(
#     search: str | None = Query(None),
#     is_active: bool | None = Query(None),
#     role: str | None = Query(None),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     filters = UserFilters(search=search, is_active=is_active, role=role)
#     users = list_users(db, filters=filters, page=page, page_size=page_size)
#     return api_response(
#         success=True,
#         message="Users retrieved",
#         data={"users": [UserResponse.model_validate(u) for u in users]},
#     )


# @router.get("/{user_id}")
# def get_user_by_id(
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = get_user(db, user_id)
#     return api_response(
#         success=True,
#         message="User retrieved",
#         data=UserResponse.model_validate(user),
#     )


# # ============================================================================
# # CREATE
# # ============================================================================

# @router.post("", status_code=status.HTTP_201_CREATED)
# async def create_new_user(
#     data: UserCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     background_tasks=Depends(lambda: __import__("fastapi").BackgroundTasks()),
# ):
#     user = await create_user(db, data, background_tasks)
#     return api_response(
#         success=True,
#         message="User created",
#         data=UserResponse.model_validate(user),
#     )


# # ============================================================================
# # UPDATE — text fields (JSON / form, no file)
# # ============================================================================

# @router.put("/{user_id}")
# def replace_user(
#     user_id: UUID,
#     data: UserUpdateSchema,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = update_user(db, user_id, data, current_user)
#     return api_response(
#         success=True,
#         message="User updated",
#         data=UserResponse.model_validate(user),
#     )


# @router.patch("/{user_id}")
# def partial_update_user(
#     user_id: UUID,
#     data: UserUpdateSchema,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = update_user(db, user_id, data, current_user)
#     return api_response(
#         success=True,
#         message="User updated",
#         data=UserResponse.model_validate(user),
#     )


# # ============================================================================
# # AVATAR UPLOAD — multipart, lives on the user resource
# # ============================================================================

# @router.patch("/{user_id}/avatar")
# def upload_user_avatar(
#     user_id: UUID,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Upload / replace profile picture for a user.
#     Accepts multipart/form-data with a single `file` field.
#     Returns the full updated user object so the client can sync state.
#     """
#     user = update_user_avatar(db, user_id, file, current_user)
#     return api_response(
#         success=True,
#         message="Avatar updated",
#         data=UserResponse.model_validate(user),
#     )


# # ============================================================================
# # PASSWORD
# # ============================================================================

# @router.patch("/{user_id}/password")
# def change_password(
#     user_id: UUID,
#     data: PasswordUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = update_password(db, user_id, data, current_user)
#     return api_response(success=True, message="Password updated", data=UserResponse.model_validate(user))


# # ============================================================================
# # STATUS / DELETE
# # ============================================================================

# @router.patch("/{user_id}/toggle-status")
# def toggle_status(
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = toggle_user_status(db, user_id, current_user)
#     return api_response(success=True, message=f"User {'activated' if user.is_active else 'deactivated'}", data=UserResponse.model_validate(user))


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def remove_user(
#     user_id: UUID,
#     hard: bool = Query(False),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     delete_user(db, user_id, current_user, hard_delete=hard)


# # ============================================================================
# # ROLES
# # ============================================================================

# @router.post("/{user_id}/roles")
# def add_role(
#     user_id: UUID,
#     role_name: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = assign_role(db, user_id, role_name, current_user)
#     return api_response(success=True, message="Role assigned", data=UserResponse.model_validate(user))


# @router.delete("/{user_id}/roles/{role_name}")
# def delete_role(  
#     user_id: UUID,
#     role_name: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     user = remove_role(db, user_id, role_name, current_user)
#     return api_response(success=True, message="Role removed", data=UserResponse.model_validate(user))


# # ============================================================================
# # PARENT ↔ STUDENT
# # ============================================================================

# @router.post("/link-parent")
# def link_parent(
#     parent_id: UUID,
#     student_id: UUID,
#     relationship_type: str = "guardian",
#     is_primary: bool = False,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     link = link_parent_to_student(db, parent_id, student_id, relationship_type, is_primary, current_user.id)
#     return api_response(success=True, message="Parent linked", data=link)


# @router.post("/unlink-parent")
# def unlink_parent(
#     parent_id: UUID,
#     student_id: UUID,
#     reason: str | None = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     unlink_parent_from_student(db, parent_id, student_id, reason)
#     return api_response(success=True, message="Parent unlinked")





# v2
# ============================================================================
# ROUTER: Users
# FILE: app/routers/users.py
# ============================================================================

"""
User resource endpoints.
Handles CRUD, avatar upload, role management, and parent-student linking.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps.users import admin_required, get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdateSchema, UserResponse, PasswordUpdate, UserFilters
from app.utils.responses import api_response

from app.services.user_service import (
    list_users,
    get_user,
    create_user,
    update_user,
    update_user_avatar,
    update_password,
    delete_user,
    toggle_user_status,
    assign_role,
    remove_role,
    link_parent_to_student,
    unlink_parent_from_student,
)

router = APIRouter()


# ============================================================================
# LIST / FETCH
# ============================================================================

@router.get("")
def get_users(
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = UserFilters(search=search, is_active=is_active, role=role)
    users = list_users(db, filters=filters, page=page, page_size=page_size)
    return api_response(
        success=True,
        message="Users retrieved",
        data={"users": [UserResponse.model_validate(u) for u in users]},
    )


@router.get("/{user_id}")
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = get_user(db, user_id)
    return api_response(
        success=True,
        message="User retrieved",
        data=UserResponse.model_validate(user),
    )


# ============================================================================
# CREATE
# ============================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_new_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks=Depends(lambda: __import__("fastapi").BackgroundTasks()),
):
    user = await create_user(db, data, background_tasks)
    return api_response(
        success=True,
        message="User created",
        data=UserResponse.model_validate(user),
    )


# ============================================================================
# UPDATE — text fields (JSON / form, no file)
# ============================================================================

@router.put("/{user_id}")
def replace_user(
    user_id: UUID,
    data: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_user(db, user_id, data, current_user)
    return api_response(
        success=True,
        message="User updated",
        data=UserResponse.model_validate(user),
    )


@router.patch("/{user_id}")
def partial_update_user(
    user_id: UUID,
    data: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_user(db, user_id, data, current_user)
    return api_response(
        success=True,
        message="User updated",
        data=UserResponse.model_validate(user),
    )


# ============================================================================
# AVATAR UPLOAD — multipart, lives on the user resource
# ============================================================================

@router.patch("/{user_id}/avatar")
async def upload_user_avatar(
    user_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload / replace profile picture for a user.
    Accepts multipart/form-data with a single `file` field.
    Returns the full updated user object so the client can sync state.
    """
    user = await update_user_avatar(db, user_id, file, current_user)
    return api_response(
        success=True,
        message="Avatar updated",
        data=UserResponse.model_validate(user),
    )


# ============================================================================
# PASSWORD
# ============================================================================

@router.patch("/{user_id}/password")
def change_password(
    user_id: UUID,
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_password(db, user_id, data, current_user)
    return api_response(success=True, message="Password updated", data=UserResponse.model_validate(user))


# ============================================================================
# STATUS / DELETE
# ============================================================================

@router.patch("/{user_id}/toggle-status")
def toggle_status(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = toggle_user_status(db, user_id, current_user)
    return api_response(success=True, message=f"User {'activated' if user.is_active else 'deactivated'}", data=UserResponse.model_validate(user))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: UUID,
    hard: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_user(db, user_id, current_user, hard_delete=hard)


# ============================================================================
# ROLES
# ============================================================================

@router.post("/{user_id}/roles")
def add_role(
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = assign_role(db, user_id, role_name, current_user)
    return api_response(success=True, message="Role assigned", data=UserResponse.model_validate(user))


@router.delete("/{user_id}/roles/{role_name}")
def delete_role(
    user_id: UUID,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = remove_role(db, user_id, role_name, current_user)
    return api_response(success=True, message="Role removed", data=UserResponse.model_validate(user))


# ============================================================================
# PARENT ↔ STUDENT
# ============================================================================

@router.post("/link-parent")
def link_parent(
    parent_id: UUID,
    student_id: UUID,
    relationship_type: str = "guardian",
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = link_parent_to_student(db, parent_id, student_id, relationship_type, is_primary, current_user.id)
    return api_response(success=True, message="Parent linked", data=link)


@router.post("/unlink-parent")
def unlink_parent(
    parent_id: UUID,
    student_id: UUID,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unlink_parent_from_student(db, parent_id, student_id, reason)
    return api_response(success=True, message="Parent unlinked")

