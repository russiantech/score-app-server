# ============================================================================
# SCHEMAS - Tutor Assignments
# FILE: app/schemas/tutors.py
# ============================================================================

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


# class CourseTutorStatus(str, Enum):
#     """Status of a tutor assignment"""
#     ACTIVE = "active"
#     INACTIVE = "inactive"
#     REVOKED = "revoked"

class CourseTutorStatus(str, Enum):
    """Status of a tutor assignment"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"

class TutorCourseCreate(BaseModel):
    """Schema for creating a new tutor assignment"""
    tutor_id: UUID = Field(..., description="ID of the tutor to assign")
    course_id: UUID = Field(..., description="ID of the course to assign")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the assignment")

    class Config:
        json_schema_extra = {
            "example": {
                "tutor_id": "123e4567-e89b-12d3-a456-426614174000",
                "course_id": "123e4567-e89b-12d3-a456-426614174001",
                "notes": "Assigned due to expertise in Python"
            }
        }


class TutorCourseUpdate(BaseModel):
    """Schema for updating a tutor assignment"""
    status: Optional[CourseTutorStatus] = Field(None, description="New status")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "inactive",
                "notes": "Temporarily inactive due to leave"
            }
        }


class TutorCourseFilters(BaseModel):
    """Filters for querying tutor assignments"""
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Filtering
    tutor_id: Optional[UUID] = Field(None, description="Filter by tutor ID")
    course_id: Optional[UUID] = Field(None, description="Filter by course ID")
    status: Optional[str] = Field(None, description="Filter by status (active, inactive, revoked, all)")
    
    # Search
    search: Optional[str] = Field(None, max_length=100, description="Search by tutor name, email, or course code")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Field to sort by")
    order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")
    
    # Include relations
    include_relations: bool = Field(default=False, description="Include tutor and course details")

    @field_validator('status')
    def validate_status(cls, v):
        if v and v not in ['active', 'inactive', 'revoked', 'all']:
            raise ValueError('Status must be one of: active, inactive, revoked, all')
        return v

    @field_validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['created_at', 'assigned_at', 'updated_at']
        if v not in allowed:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10,
                "status": "active",
                "search": "python",
                "sort_by": "created_at",
                "order": "desc",
                "include_relations": True
            }
        }


class BulkTutorCourseCreate(BaseModel):
    """Schema for bulk assignment creation"""
    tutor_id: UUID = Field(..., description="ID of the tutor")
    course_ids: list[UUID] = Field(..., min_items=1, description="List of course IDs to assign")
    notes: Optional[str] = Field(None, max_length=500, description="Notes for all assignments")

    class Config:
        json_schema_extra = {
            "example": {
                "tutor_id": "123e4567-e89b-12d3-a456-426614174000",
                "course_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002"
                ],
                "notes": "Bulk assignment for Fall 2024"
            }
        }


class BulkTutorCourseDelete(BaseModel):
    """Schema for bulk assignment deletion"""
    assignment_ids: list[UUID] = Field(..., min_items=1, description="List of assignment IDs to delete")

    class Config:
        json_schema_extra = {
            "example": {
                "assignment_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001"
                ]
            }
        }


class ReassignTutorCourseRequest(BaseModel):
    """Schema for reassigning a course to a different tutor"""
    assignment_id: UUID = Field(..., description="ID of the assignment to reassign")
    new_tutor_id: UUID = Field(..., description="ID of the new tutor")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for reassignment")

    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "123e4567-e89b-12d3-a456-426614174000",
                "new_tutor_id": "123e4567-e89b-12d3-a456-426614174002",
                "reason": "Original tutor on medical leave"
            }
        }
