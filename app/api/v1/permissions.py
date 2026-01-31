
# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@router.get("/permissions")
def list_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=200, description="Items per page"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
):
    """
    Get list of all available permissions.
    
    - **Admin only**
    """
    permissions = RoleService.get_permissions(
        db=db,
        page=page,
        page_size=page_size,
        resource=resource,
        current_user=current_user
    )
    
    paginator = PageSerializer(
        request=request,
        obj=permissions,
        resource_name="permissions",
        page=page,
        page_size=page_size
    )
    
    return paginator.get_response(message="Permissions retrieved successfully")


@router.post("/roles/{role_id}/permissions")
def assign_permission_to_role(
    request: Request,
    role_id: UUID,
    permission_data: PermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign permission(s) to a role.
    
    - **Admin only**
    """
    role = RoleService.assign_permission(
        db=db,
        role_id=role_id,
        permission_data=permission_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=role.get_summary(),
        message="Permission(s) assigned successfully",
        path=str(request.url.path)
    )


@router.delete("/roles/{role_id}/permissions/{permission_id}")
def revoke_permission_from_role(
    request: Request,
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a permission from a role.
    
    - **Admin only**
    """
    RoleService.revoke_permission(
        db=db,
        role_id=role_id,
        permission_id=permission_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        message="Permission revoked successfully",
        path=str(request.url.path)
    )


@router.get("/roles/{role_id}/permissions")
def get_role_permissions(
    request: Request,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions for a role.
    
    - **Admin only**
    """
    permissions = RoleService.get_role_permissions(
        db=db,
        role_id=role_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={
            "role_id": str(role_id),
            "permissions": [p.get_summary() for p in permissions]
        },
        message="Role permissions retrieved successfully",
        path=str(request.url.path)
    )


@router.get("/users/{user_id}/permissions")
def get_user_permissions(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions for a user (based on their role).
    
    - **Admin or self**
    """
    permissions = RoleService.get_user_permissions(
        db=db,
        user_id=user_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={
            "user_id": str(user_id),
            "permissions": [p.get_summary() for p in permissions]
        },
        message="User permissions retrieved successfully",
        path=str(request.url.path)
    )


@router.get("/my-permissions")
def get_my_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's permissions.
    
    - **Requires authentication**
    """
    permissions = RoleService.get_user_permissions(
        db=db,
        user_id=current_user.id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data={
            "user_id": str(current_user.id),
            "role": current_user.role,
            "permissions": [p.get_summary()