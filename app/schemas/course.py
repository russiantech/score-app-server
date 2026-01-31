# v2
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from uuid import UUID

class CourseBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    total_modules: Optional[int] = 0
    total_lessons: Optional[int] = 0
    duration_weeks: Optional[int] = None
    difficulty_level: Optional[str] = None
    is_active: Optional[bool] = True
    is_public: Optional[bool] = True

class CourseCreate(CourseBase):
    tutor_ids: Optional[List[UUID]] = []

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    total_lessons: Optional[int] = None
    duration_weeks: Optional[int] = None
    difficulty_level: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    tutor_ids: Optional[List[UUID]] = None
    
    model_config = {
        "extra": "forbid"  # catches junk fields early
    }
    
    # @field_validator("instructor_ids", mode="before")
    # @classmethod
    # def validate_instructor_ids(cls, v):
    #     if v is None:
    #         return None
    #     if not all(isinstance(i, (str, UUID)) for i in v):
    #         raise ValueError("Instructor IDs must be UUID strings")
    #     return v

class CourseOut(CourseBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class CourseWithInstructors(CourseOut):
    instructors: List[dict] = []

# Search / filters
class CourseFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")
    tutor_id: Optional[UUID] = None

    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|title|code)$")
    order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

