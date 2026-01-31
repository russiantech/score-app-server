
# app/schemas/rbac.py - Schemas for Role-Based Access Control (RBAC)
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100, description="Unique name of the permission")
    description: Optional[str] = Field(None, description="Description of the permission")
    resource: str = Field(..., max_length=50, description="Resource the permission applies to")
    action: str = Field(..., max_length=20, description="Action allowed by the permission")

class PermissionCreate(PermissionBase):
    pass

class PermissionRead(PermissionBase):
    model_config = ConfigDict(from_attributes=True) # ✅ Pydantic V2
    id: UUID

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, description="Unique name of the role")
    description: Optional[str] = Field(None, description="Description of the role")
    is_default: bool = Field(False, description="Indicates if this is a default role")

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic V2
    id: UUID
    permissions: List[PermissionRead] = Field([], description="List of permissions assigned to the role")

class PermissionAssign(BaseModel):
    permission_ids: List[UUID] = Field(..., description="List of permission IDs to assign to the role")
    role_id: UUID = Field(..., description="ID of the role to which permissions are assigned")
    
class PermissionUnassign(BaseModel):
    permission_ids: List[UUID] = Field(..., description="List of permission IDs to unassign from the role")
    role_id: UUID = Field(..., description="ID of the role from which permissions are unassigned")
    
class RoleListResponse(BaseModel):
    roles: List[RoleRead] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles available")

class PermissionListResponse(BaseModel):
    permissions: List[PermissionRead] = Field(..., description="List of permissions")
    total: int = Field(..., description="Total number of permissions available")

class RolePermissionResponse(BaseModel):
    role: RoleRead = Field(..., description="Role details")
    permissions: List[PermissionRead] = Field(..., description="Permissions assigned to the role")

class PermissionRoleResponse(BaseModel):
    permission: PermissionRead = Field(..., description="Permission details")
    roles: List[RoleRead] = Field(..., description="Roles that have this permission")
    total: int = Field(..., description="Total number of roles that have this permission")

class RolePermissionAssignmentResponse(BaseModel):
    role: RoleRead = Field(..., description="Role details after assignment")
    assigned_permissions: List[PermissionRead] = Field(..., description="Permissions that were assigned to the role")

class RolePermissionUnassignmentResponse(BaseModel):
    role: RoleRead = Field(..., description="Role details after unassignment")
    unassigned_permissions: List[PermissionRead] = Field(..., description="Permissions that were unassigned from the role")

# Association table between roles and permissions
# Defined in app/models/association_tables.py