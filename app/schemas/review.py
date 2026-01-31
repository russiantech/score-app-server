# app/schemas/review.py
from pydantic import BaseModel, Field, field_validator, validator
from typing import Optional, List
from datetime import datetime
import uuid
from enum import Enum

class ReviewType(str, Enum):
    COURSE = "course"
    INSTRUCTOR = "instructor"
    LESSON = "lesson"
    SYSTEM = "system"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    HIDDEN = "hidden"
    DELETED = "deleted"

# Base schemas
class ReviewBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    comment: str = Field(..., min_length=10, max_length=5000)
    review_type: ReviewType
    is_anonymous: bool = False
    recommend: bool = True
    would_take_again: Optional[bool] = None
    
    # Ratings (1-5)
    rating_overall: Optional[int] = Field(None, ge=1, le=5)
    rating_content: Optional[int] = Field(None, ge=1, le=5)
    rating_teaching: Optional[int] = Field(None, ge=1, le=5)
    rating_difficulty: Optional[int] = Field(None, ge=1, le=5)
    
    @field_validator('comment')
    def comment_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment cannot be empty')
        return v.strip()

# Create schemas (one target required)
class CourseReviewCreate(ReviewBase):
    review_type: ReviewType = ReviewType.COURSE
    course_id: uuid.UUID
    enrollment_id: Optional[uuid.UUID] = None

class InstructorReviewCreate(ReviewBase):
    review_type: ReviewType = ReviewType.INSTRUCTOR
    instructor_id: uuid.UUID
    course_id: Optional[uuid.UUID] = None

class LessonReviewCreate(ReviewBase):
    review_type: ReviewType = ReviewType.LESSON
    lesson_id: uuid.UUID
    course_id: Optional[uuid.UUID] = None

# Update schema
class ReviewUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = Field(None, min_length=10, max_length=5000)
    recommend: Optional[bool] = None
    would_take_again: Optional[bool] = None
    rating_overall: Optional[int] = Field(None, ge=1, le=5)
    rating_content: Optional[int] = Field(None, ge=1, le=5)
    rating_teaching: Optional[int] = Field(None, ge=1, le=5)
    rating_difficulty: Optional[int] = Field(None, ge=1, le=5)
    is_anonymous: Optional[bool] = None

# Response schemas
class ReviewAuthor(BaseModel):
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_anonymous: bool = False
    is_verified: Optional[bool] = None
    
    class Config:
        from_attributes = True

class ReviewTarget(BaseModel):
    course: Optional[dict] = None
    instructor: Optional[dict] = None
    lesson: Optional[dict] = None
    enrollment: Optional[dict] = None
    
    class Config:
        from_attributes = True

class ReviewStats(BaseModel):
    helpful_count: int = 0
    not_helpful_count: int = 0
    helpfulness_score: float = 0.0
    reply_count: int = 0
    report_count: int = 0
    
    class Config:
        from_attributes = True

class ReviewReplyInDB(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    author: ReviewAuthor
    comment: str
    is_official_response: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewInDB(ReviewBase):
    id: uuid.UUID
    author_id: uuid.UUID
    author: Optional[ReviewAuthor] = None
    target: Optional[ReviewTarget] = None
    stats: Optional[ReviewStats] = None
    replies: List[ReviewReplyInDB] = []
    
    status: ReviewStatus
    sentiment_label: Optional[str] = None
    is_verified_purchase: bool = False
    average_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @validator('author', pre=True, always=True)
    def get_author_info(cls, v, values):
        """Handle anonymous authors."""
        if v and 'is_anonymous' in values and values.get('is_anonymous'):
            return ReviewAuthor(is_anonymous=True, name="Anonymous")
        return v

# Moderation schemas
class ReviewModerationUpdate(BaseModel):
    status: ReviewStatus
    moderation_notes: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('status')
    def validate_moderation_status(cls, v):
        allowed = [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.HIDDEN]
        if v not in allowed:
            raise ValueError('Invalid moderation status')
        return v

# Vote/Report schemas
class ReviewVoteCreate(BaseModel):
    is_helpful: bool = True

class ReviewReportCreate(BaseModel):
    reason: str = Field(..., max_length=50)  # spam, inappropriate, false_info, other
    description: Optional[str] = Field(None, max_length=1000)

# Reply schemas
class ReviewReplyCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)
    is_official_response: bool = False

# Filter schemas
class ReviewFilters(BaseModel):
    review_type: Optional[ReviewType] = None
    status: Optional[ReviewStatus] = None
    course_id: Optional[uuid.UUID] = None
    instructor_id: Optional[uuid.UUID] = None
    lesson_id: Optional[uuid.UUID] = None
    author_id: Optional[uuid.UUID] = None
    min_rating: Optional[int] = Field(None, ge=1, le=5)
    max_rating: Optional[int] = Field(None, ge=1, le=5)
    recommend: Optional[bool] = None
    is_verified: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc, desc

# Analytics schemas
class ReviewAnalytics(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: dict  # {1: count, 2: count, ... 5: count}
    recommendation_rate: float
    sentiment_distribution: dict
    recent_trend: List[dict]