# # from pydantic import BaseModel, ConfigDict
# # from uuid import UUID

# # class EnrollmentBase(BaseModel):
# #     student_id: UUID
# #     course_id: UUID
# #     session: str

# # class EnrollmentCreate(EnrollmentBase):
# #     pass

# # class EnrollmentOut(EnrollmentBase):
# #     model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic V2
# #     id: UUID

# # v2
# # ============================================================================
# # SCHEMAS - Part 4: Enrollment Schemas
# # FILE: app/schemas/enrollment.py
# # ============================================================================

# from pydantic import BaseModel, Field
# from uuid import UUID
# from datetime import datetime
# from typing import Optional

# class EnrollmentCreate(BaseModel):
#     student_id: UUID
#     course_id: UUID

# # class EnrollmentOut(BaseModel):
# #     id: UUID
# #     student_id: UUID
# #     course_id: UUID
# #     enrolled_at: datetime
# #     progress: float = 0.0
# #     overall_grade: Optional[str] = None
    
# #     class Config:
# #         from_attributes = True

# class EnrollmentOut(BaseModel):
#     id: UUID
#     student_id: UUID
#     course_id: UUID
#     enrolled_at: datetime
#     status: str
#     progress: int
#     overall_grade: Optional[str] = None
    
#     # Nested data
#     student: Optional[dict] = None
#     course: Optional[dict] = None
    
#     class Config:
#         from_attributes = True
    

# # Filters Model
# class EnrollmentFilters(BaseModel):
#     search: Optional[str] = None
#     status: Optional[str] = Field(None, pattern="^(active|completed|dropped)$")
#     student_id: Optional[UUID] = None
#     course_id: Optional[UUID] = None
#     sort_by: Optional[str] = Field("enrolled_at", pattern="^(enrolled_at|student_name|course_name|progress)$")
#     order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
#     page: int = Field(1, ge=1)
#     page_size: int = Field(10, ge=1, le=100)


# v2
# ============================================================================
# SCHEMAS - Enrollment
# FILE: app/schemas/enrollment.py
# ============================================================================

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class EnrollmentStatusEnum(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    withdrawn = "withdrawn"
    suspended = "suspended"

class EnrollmentCreate(BaseModel):
    student_id: UUID
    course_id: UUID
    session: str = "2026/2027"  # default
    term: str = "Q1.2026"       # default

class EnrollmentOut(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    enrolled_at: datetime
    status: EnrollmentStatusEnum

    # nested summaries
    student: Optional[dict] = None
    course: Optional[dict] = None

    class Config:
        from_attributes = True


class EnrollmentFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[EnrollmentStatusEnum] = None
    student_id: Optional[UUID] = None
    course_id: Optional[UUID] = None

    sort_by: Optional[str] = Field(
        "enrolled_at",
        pattern="^(enrolled_at|created_at)$"
    )
    order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

