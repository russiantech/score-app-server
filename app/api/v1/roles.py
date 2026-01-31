
# ============================================================================
# ROLE & PERMISSION ENDPOINTS
# ============================================================================

# app/api/v1/roles.py
from typing import List, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.users import get_db, get_current_user
from app.models.user import User
from app.schemas.rbac import (
    RoleCreate,
    RoleUpdate,
    PermissionAssign
)
from app.services.role_service import RoleService
from app.utils.responses import api_response, PageSerializer
from app.models.rbac import Role

router = APIRouter(tags=["Roles & Permissions"])


# ============================================================================
# ROLE ENDPOINTS
# ============================================================================

@router.get("/roles")
def list_roles(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by role name"),
):
    """
    Get paginated list of roles.
    
    - **Admin only**
    """
    roles = RoleService.get_roles(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        current_user=current_user
    )
    
    paginator = PageSerializer(
        request=request,
        obj=roles,
        resource_name="roles",
        page=page,
        page_size=page_size
    )
    
    return paginator.get_response(message="Roles retrieved successfully")


@router.get("/roles/{role_id}")
def get_role(
    request: Request,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get role by ID with permissions.
    
    - **Admin only**
    """
    role = RoleService.get_role(
        db=db,
        role_id=role_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=role.get_summary(),
        message="Role retrieved successfully",
        path=str(request.url.path)
    )


@router.post("/roles")
def create_role(
    request: Request,
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new role.
    
    - **Admin only**
    """
    role = RoleService.create_role(
        db=db,
        role_data=role_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=role.get_summary(),
        message="Role created successfully",
        status_code=201,
        path=str(request.url.path)
    )

# create update role endpoint
@router.patch("/roles/{role_id}")
def update_role(
    request: Request,
    role_id: UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update role details.
    
    - **Admin only**
    """
    updated_role = RoleService.update_role(
        db=db,
        role_id=role_id,
        role_data=role_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=updated_role.get_summary(),
        message="Role updated successfully",
        path=str(request.url.path)
    )

#  delete role endpoint
@router.delete("/roles/{role_id}")
def delete_role(
    request: Request,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a role.
    
    - **Admin only**
    - Cannot delete system roles (admin, instructor, student, parent)
    """
    RoleService.delete_role(
        db=db,
        role_id=role_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        message="Role deleted successfully",
        path=str(request.url.path)
    )

# insert roles directyly
@router.post("/roles/bulk")
def bulk_insert_roles(
    request: Request,
    role_data: List[RoleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Insert multiple roles at once.
    
    - **Admin only**
    """
    roles = RoleService.bulk_insert_roles(
        db=db,
        role_data=role_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=[role.get_summary() for role in roles],
        message="Roles inserted successfully",
        path=str(request.url.path)
    )

# manual insertion of roles
@router.post("/manual-insert-roles")
def manual_insert_roles(
    request: Request,
    # role_data: List[RoleCreate],
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Manually insert roles into the system.
    
    - **Admin only**
    """
    
    # if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
    #         raise HTTPException(status_code=403, detail="Only admins can view role permissions")
        
    role_data = [ 
        {'name':'admin', 'description':'System administrator', }, 
        {'name':'superadmin', 'description':'Super administrator with all permissions'},
        {'name':'instructor', 'description':'Course instructor'}, 
        {'name':'student', 'description':'Course student'}, 
        {'name':'parent', 'description':'Parent of a student'},
        {'name':'content_creator', 'description':'Content creator'}, 
        {'name':'moderator', 'description':'Content moderator'},
        {'name':'guest', 'description':'Guest user with limited access'},
        {'name':'editor', 'description':'Content editor'},
        {'name':'user', 'description':'Regular user with standard privileges'},
        {'name':'alumni', 'description':'Former student with alumni privileges'},
        {'name':'staff', 'description':'Support staff member'},
        
        ]

    roles = [Role(**data) for data in role_data]
    db.add_all(roles)
    db.commit()
    # for role in roles:
    #     db.refresh(role)

    return api_response(
        success=True,
        data=[role.get_summary() for role in roles],
        message="Roles manually inserted successfully",
        path=str(request.url.path)
    )


# create permission assignment endpoint
@router.post("/roles/{role_id}/permissions")
def assign_permissions_to_role(
    request: Request,
    role_id: UUID,
    permission_data: PermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign permissions to a role.
    
    - **Admin only**
    """
    updated_role = RoleService.assign_permissions(
        db=db,
        role_id=role_id,
        permission_data=permission_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=updated_role.get_summary(),
        message="Permissions assigned successfully",
        path=str(request.url.path)
    )

# create permission assignment endpoint
@router.delete("/roles/{role_id}/permissions")
def remove_permissions_from_role(
    request: Request,
    role_id: UUID,
    permission_data: PermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove permissions from a role.
    
    - **Admin only**
    """
    updated_role = RoleService.remove_permissions(
        db=db,
        role_id=role_id,
        permission_data=permission_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=updated_role.get_summary(),
        message="Permissions removed successfully",
        path=str(request.url.path)
    )

@router.get("/roles/{role_id}/permissions")
def list_role_permissions(
    request: Request,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List permissions assigned to a role.
    
    - **Admin only**
    """
    permissions = RoleService.list_permissions(
        db=db,
        role_id=role_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={"permissions": permissions},
        message="Permissions retrieved successfully",
        path=str(request.url.path)
    )

# create endpoint to list all available permissions
@router.get("/permissions")
def list_all_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available permissions in the system.
    
    - **Admin only**
    """
    permissions = RoleService.list_all_permissions(
        db=db,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={"permissions": permissions},
        message="All permissions retrieved successfully",
        path=str(request.url.path)
    )

# create endpoint to count total roles
@router.get("/roles/count")
def count_roles(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get total count of roles in the system.
    
    - **Admin only**
    """
    role_count = RoleService.count_roles(
        db=db,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={"count": role_count},
        message="Total roles count retrieved successfully",
        path=str(request.url.path)
    )

# 