# app/services/role_service.py
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
# from app.models.role import Role, Permission, role_permissions
from app.models.user import User
from app.models.rbac import Permission, Role
# from app.schemas.rbac import RoleCreate, RoleUpdate, PermissionAssign
from app.models.association_tables import role_permissions
from app.schemas.rbac import RoleCreate, RoleUpdate, PermissionAssign
from app.core.data.const import SYSTEM_ROLES

class RoleService:
    SYSTEM_ROLES = SYSTEM_ROLES

    @staticmethod
    def get_roles(
        db: Session,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        current_user: User = None
    ):
        """Get roles with pagination"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can view roles")
        
        query = db.query(Role)
        
        if search:
            query = query.filter(Role.name.ilike(f"%{search}%"))
        
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    @staticmethod
    def get_role(db: Session, role_id: UUID, current_user: User):
        """Get role by ID"""
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Only admins can view roles")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return role

    @staticmethod
    def create_role(db: Session, role_data: RoleCreate, current_user: User):
        """Create new role"""
        if not current_user.has_role("admin", "developer"):
            raise HTTPException(status_code=403, detail="Only admins can create roles")
        
        # Check if role name already exists
        existing = db.query(Role).filter(Role.name == role_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Role name already exists")
        
        role = Role(**role_data.dict())
        db.add(role)
        db.commit()
        db.refresh(role)
        
        return role

    @staticmethod
    def update_role(db: Session, role_id: UUID, role_data: RoleUpdate, current_user: User):
        """Update role"""
        if not current_user.has_role("admin", "developer"):
            raise HTTPException(status_code=403, detail="Only admins can update roles")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Cannot modify system roles
        if role.name.lower() in RoleService.SYSTEM_ROLES:
            raise HTTPException(status_code=400, detail="Cannot modify system roles")
        
        for key, value in role_data.model_dump(exclude_unset=True).items():
            setattr(role, key, value)
        
        db.commit()
        db.refresh(role)
        
        return role

    @staticmethod
    def delete_role(db: Session, role_id: UUID, current_user: User):
        """Delete role"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can delete roles")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Cannot delete system roles
        if role.name.lower() in RoleService.SYSTEM_ROLES:
            raise HTTPException(status_code=400, detail="Cannot delete system roles")
        
        # Check if any users have this role
        users_with_role = db.query(User).filter(User.roles.any(Role.id == role.id)).count()
        if users_with_role > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete role. {users_with_role} users still have this role"
            )
        
        db.delete(role)
        db.commit()

    @staticmethod
    def get_permissions(
        db: Session,
        page: int,
        page_size: int,
        resource: Optional[str] = None,
        current_user: User = None
    ):
        """Get all permissions"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can view permissions")
        
        query = db.query(Permission)
        
        if resource:
            query = query.filter(Permission.resource == resource)
        
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    @staticmethod
    def assign_permission(
        db: Session,
        role_id: UUID,
        permission_data: PermissionAssign,
        current_user: User
    ):
        """Assign permission(s) to role"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can assign permissions")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        for permission_id in permission_data.permission_ids:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                continue
            
            # Check if already assigned
            existing = db.query(role_permissions).filter(
                role_permissions.role_id == role_id,
                role_permissions.permission_id == permission_id
            ).first()
            
            if not existing:
                role_permissions = role_permissions(
                    role_id=role_id,
                    permission_id=permission_id
                )
                db.add(role_permissions)
        
        db.commit()
        db.refresh(role)
        
        return role

    @staticmethod
    def revoke_permission(
        db: Session,
        role_id: UUID,
        permission_id: UUID,
        current_user: User
    ):
        """Revoke permission from role"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can revoke permissions")
        
        role_permissions = db.query(role_permissions).filter(
            role_permissions.role_id == role_id,
            role_permissions.permission_id == permission_id
        ).first()
        
        if not role_permissions:
            raise HTTPException(status_code=404, detail="Permission assignment not found")
        
        db.delete(role_permissions)
        db.commit()

    @staticmethod
    def get_role_permissions(db: Session, role_id: UUID, current_user: User) -> List[Permission]:
        """Get all permissions for a role"""
        if not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Only admins can view role permissions")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        permissions = db.query(Permission).join(role_permissions).filter(
            role_permissions.role_id == role_id
        ).all()
        
        return permissions

    @staticmethod
    def get_user_permissions(db: Session, user_id: UUID, current_user: User) -> List[Permission]:
        """Get all permissions for a user based on their role"""
        # Users can view their own permissions, admins can view any
        if current_user.id != user_id and not current_user.has_role("admin", "developer", "moderator", "superadmin"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get role
        role = db.query(Role).filter(Role.name == user.role.value).first()
        if not role:
            return []
        
        # Get permissions for this role
        permissions = db.query(Permission).join(role_permissions).filter(
            role_permissions.role_id == role.id
        ).all()
        
        return permissions
    
