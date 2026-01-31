# from pydantic import BaseModel, ConfigDict
# from uuid import UUID
# from .user import UserRead

# class ParentBase(BaseModel):
#     pass

# class ParentCreate(ParentBase):
#     user_id: UUID

# class ParentOut(ParentBase):
#     model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic V2
#     id: UUID
#     user: UserRead

# # v2
# from datetime import datetime
# from typing import Optional, List
# from uuid import UUID
# from pydantic import BaseModel, Field, ConfigDict


# # Base Parent Schema
# class ParentBase(BaseModel):
#     """Base parent schema with common fields."""
#     relationship_to_student: Optional[str] = Field(None, max_length=50, description="e.g., Father, Mother, Guardian")
#     occupation: Optional[str] = Field(None, max_length=100)
#     address: Optional[str] = None
#     emergency_contact: Optional[str] = Field(None, max_length=20)
#     notes: Optional[str] = None


# # Parent Creation Schema
# class ParentCreate(ParentBase):
#     """Schema for creating a new parent profile."""
#     user_id: UUID = Field(..., description="ID of the user account")
#     is_primary: bool = Field(False, description="Is this the primary parent/guardian?")


# # Parent Update Schema
# class ParentUpdate(BaseModel):
#     """Schema for updating parent information."""
#     model_config = ConfigDict(extra='forbid')
    
#     relationship_to_student: Optional[str] = Field(None, max_length=50)
#     occupation: Optional[str] = Field(None, max_length=100)
#     address: Optional[str] = None
#     emergency_contact: Optional[str] = Field(None, max_length=20)
#     notes: Optional[str] = None
#     is_primary: Optional[bool] = None
#     is_verified: Optional[bool] = None


# # Parent Response Schema
# class ParentRead(ParentBase):
#     """Schema for parent responses."""
#     model_config = ConfigDict(from_attributes=True)
    
#     id: UUID
#     user_id: UUID
#     full_name: str
#     email: Optional[str]
#     phone: Optional[str]
#     is_primary: bool
#     is_verified: bool
#     students: List[str] = Field(default_factory=list)
#     created_at: datetime
#     updated_at: datetime


# # Link Student Schema
# class LinkStudentRequest(BaseModel):
#     """Schema for linking a student to a parent."""
#     child_id: UUID = Field(..., description="ID of the student to link")


# # Parent Summary Schema
# class ParentSummary(BaseModel):
#     """Minimal parent information for public display."""
#     model_config = ConfigDict(from_attributes=True)
    
#     id: UUID
#     full_name: str
#     relationship_to_student: Optional[str]
#     is_primary: bool


# 

import enum
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ParentChildCreate(BaseModel):
    """Schema for creating a parent-student link"""
    parent_id: UUID
    child_id: UUID
    relationship_type: str = Field(default="guardian")
    is_primary: bool = Field(default=False)
    notes: Optional[str] = None


class ParentChildUpdate(BaseModel):
    """Schema for updating a parent-student link"""
    relationship_type: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ParentChildFilters(BaseModel):
    """Filters for listing links"""
    search: Optional[str] = None
    status: Optional[str] = None
    parent_id: Optional[UUID] = None
    child_id: Optional[UUID] = None
    relationship_type: Optional[str] = None
    sort_by: str = "created_at"
    order: str = "desc"


# new
class RelationshipType(enum.Enum):
    """Types of parent-student relationships"""
    PARENT = "parent"
    GUARDIAN = "guardian"
    BIOLOGICAL = "biological"
    ADOPTIVE = "adoptive"
    LEGAL_GUARDIAN = "legal_guardian"
    FOSTER = "foster"
    OTHER = "other"


class LinkStatus(enum.Enum):
    """Status of parent-student link"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
