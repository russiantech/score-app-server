# """ (These cover BOTH assessments & assignments) """

# from pydantic import BaseModel, ConfigDict
# from uuid import UUID
# from enum import Enum

# class AssessmentType(str, Enum):
#     assessment = "assessment"
#     assignment = "assignment"

# class AssessmentBase(BaseModel):
#     lesson_id: UUID
#     type: AssessmentType
#     title: str
#     max_score: float

# class AssessmentCreate(AssessmentBase):
#     pass

# class AssessmentUpdate(AssessmentBase):
#     pass

# class AssessmentOut(AssessmentBase):
#     model_config = ConfigDict(from_attributes=True)  #  Pydantic V2
#     id: UUID


# v2

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.assessment import AssessmentType, AssessmentStatus, SubmissionStatus


# Assessment Schemas
class AssessmentBase(BaseModel):
    """Base assessment schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    type: AssessmentType = AssessmentType.CLASSWORK
    total_points: float = Field(100.0, ge=0)
    passing_score: Optional[float] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    allow_late_submission: bool = False
    late_penalty_percent: float = Field(0.0, ge=0, le=100)
    max_attempts: int = Field(1, ge=1)
    time_limit_minutes: Optional[int] = Field(None, ge=1)


class AssessmentCreate(AssessmentBase):
    """Schema for creating assessment."""
    course_id: UUID
    status: AssessmentStatus = AssessmentStatus.DRAFT
    is_published: bool = False


class AssessmentUpdate(BaseModel):
    """Schema for updating assessment."""
    model_config = ConfigDict(extra='forbid')
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    type: Optional[AssessmentType] = None
    status: Optional[AssessmentStatus] = None
    total_points: Optional[float] = Field(None, ge=0)
    passing_score: Optional[float] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    allow_late_submission: Optional[bool] = None
    late_penalty_percent: Optional[float] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    is_published: Optional[bool] = None


class AssessmentRead(AssessmentBase):
    """Schema for assessment responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    course_id: UUID
    status: AssessmentStatus
    is_published: bool
    is_overdue: bool
    is_available: bool
    submission_count: int
    graded_count: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


# Submission Schemas
class SubmissionBase(BaseModel):
    """Base submission schema."""
    content: Optional[str] = None
    attachment_urls: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    """Schema for creating submission."""
    assessment_id: UUID


class SubmissionUpdate(BaseModel):
    """Schema for updating submission."""
    model_config = ConfigDict(extra='forbid')
    
    content: Optional[str] = None
    attachment_urls: Optional[str] = None


class GradeSubmission(BaseModel):
    """Schema for grading a submission."""
    score: float = Field(..., ge=0)
    feedback: Optional[str] = None
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        if v < 0:
            raise ValueError('Score cannot be negative')
        return v


class SubmissionRead(SubmissionBase):
    """Schema for submission responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    assessment_id: UUID
    student_id: UUID
    status: SubmissionStatus
    attempt_number: int
    submitted_at: Optional[datetime]
    graded_at: Optional[datetime]
    score: Optional[float]
    final_score: Optional[float]
    percentage: Optional[float]
    feedback: Optional[str]
    is_late: bool
    late_penalty_applied: float
    graded_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


# Summary Schemas
class AssessmentSummary(BaseModel):
    """Minimal assessment info."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    type: AssessmentType
    due_date: Optional[datetime]
    total_points: float
    is_published: bool


class SubmissionSummary(BaseModel):
    """Minimal submission info."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: SubmissionStatus
    submitted_at: Optional[datetime]
    score: Optional[float]
    percentage: Optional[float]

