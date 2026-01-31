from datetime import date as Date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from app.models.enums import LessonStatus


class LessonBase(BaseModel):
    """Base schema shared by create operations"""

    title: str = Field(..., min_length=1, max_length=200)
    order: int = Field(..., ge=1)
    description: Optional[str] = Field(None, max_length=1000)

    assessment_max: Optional[float] = Field(None, ge=0)
    assignment_max: Optional[float] = Field(None, ge=0)

    status: LessonStatus = Field(default=LessonStatus.UPCOMING)


class LessonCreate(LessonBase):
    """Schema for creating a new lesson"""

    module_id: UUID
    date: Date  # Required on creation

    model_config = {
        "json_encoders": {
            Date: lambda v: v.isoformat() if v else None,
        }
    }


class LessonUpdate(BaseModel):
    """Schema for updating a lesson (PATCH) – ALL fields optional"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    order: Optional[int] = Field(None, ge=1)
    date: Optional[Date] = None

    description: Optional[str] = Field(None, max_length=1000)
    assessment_max: Optional[float] = Field(None, ge=0)
    assignment_max: Optional[float] = Field(None, ge=0)
    status: Optional[LessonStatus] = None

    model_config = {
        "json_encoders": {
            Date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }
    }


class LessonOut(BaseModel):
    """Schema for returning a lesson"""

    id: UUID
    module_id: UUID

    title: str
    order: int
    date: Optional[Date]

    description: Optional[str]
    assessment_max: Optional[float]
    assignment_max: Optional[float]

    status: LessonStatus

    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            Date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }
    }


class LessonFilters(BaseModel):
    course_id: UUID
    module_id: UUID
    page: int = 1
    page_size: int = 50
    search: Optional[str] = None