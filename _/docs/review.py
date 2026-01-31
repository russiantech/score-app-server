I'll create a comprehensive review/feedback system similar to your Flask implementation, but integrated professionally with your FastAPI scoring system. This will allow reviews for courses, instructors, and lessons.

## Review Model Implementation

```python
# app/models/review.py
from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
import enum
import uuid
from datetime import datetime
from .base import Base, TimestampMixin, UUIDMixin

class ReviewType(enum.Enum):
    COURSE = "course"
    INSTRUCTOR = "instructor"
    LESSON = "lesson"
    SYSTEM = "system"

class ReviewStatus(enum.Enum):
    PENDING = "pending"      # Awaiting moderation
    APPROVED = "approved"    # Published
    REJECTED = "rejected"    # Moderator rejected
    HIDDEN = "hidden"       # User/Admin hid
    DELETED = "deleted"     # Soft deleted

class Review(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    
    # Review Metadata
    title: Mapped[str | None] = mapped_column(String(200))
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    review_type: Mapped[ReviewType] = mapped_column(Enum(ReviewType), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), 
        default=ReviewStatus.PENDING
    )
    
    # Ratings (1-5 scale)
    rating_overall: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    rating_content: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    rating_teaching: Mapped[Optional[int]] = mapped_column(Integer) # 1-5
    rating_difficulty: Mapped[Optional[int]] = mapped_column(Integer) # 1-5
    
    # Recommendations
    recommend: Mapped[bool] = mapped_column(Boolean, default=True)
    would_take_again: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Sentiment Analysis
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    sentiment_label: Mapped[str | None] = mapped_column(String(20))  # positive/negative/neutral
    
    # Flags & Moderation
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_notes: Mapped[str | None] = mapped_column(Text)
    moderated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id')
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Foreign Keys (at least one must be non-null)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Target of the review (at least one should be set)
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('courses.id', ondelete='CASCADE'),
        index=True
    )
    instructor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('lessons.id', ondelete='CASCADE'),
        index=True
    )
    enrollment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('enrollments.id', ondelete='CASCADE'),
        index=True
    )
    
    # Helpfulness tracking
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="reviews_authored",
        foreign_keys=[author_id]
    )
    
    course: Mapped[Optional["Course"]] = relationship(
        "Course",
        back_populates="reviews"
    )
    
    instructor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviews_received",
        foreign_keys=[instructor_id]
    )
    
    lesson: Mapped[Optional["Lesson"]] = relationship(
        "Lesson",
        back_populates="reviews"
    )
    
    enrollment: Mapped[Optional["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="review"
    )
    
    moderator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[moderated_by]
    )
    
    helpful_votes: Mapped[List["ReviewHelpfulVote"]] = relationship(
        "ReviewHelpfulVote",
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    reports: Mapped[List["ReviewReport"]] = relationship(
        "ReviewReport",
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    replies: Mapped[List["ReviewReply"]] = relationship(
        "ReviewReply",
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    # Calculated Properties
    @property
    def average_rating(self) -> Optional[float]:
        """Calculate average of all rating components."""
        ratings = []
        if self.rating_overall:
            ratings.append(self.rating_overall)
        if self.rating_content:
            ratings.append(self.rating_content)
        if self.rating_teaching:
            ratings.append(self.rating_teaching)
        if self.rating_difficulty:
            ratings.append(self.rating_difficulty)
        
        if ratings:
            return sum(ratings) / len(ratings)
        return None
    
    @property
    def helpfulness_score(self) -> float:
        """Calculate helpfulness score."""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0.0
        return self.helpful_count / total_votes
    
    @property
    def is_visible(self) -> bool:
        """Check if review should be visible."""
        return self.status == ReviewStatus.APPROVED and not self.is_deleted
    
    # Validation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure at least one target is set
        if not any([self.course_id, self.instructor_id, self.lesson_id, self.enrollment_id]):
            raise ValueError("Review must be related to a course, instructor, lesson, or enrollment")
    
    def get_summary(
        self, 
        include_author: bool = False,
        include_target: bool = False,
        include_stats: bool = False,
        include_replies: bool = False,
        **kwargs
    ) -> dict:
        """
        Get review summary for API responses.
        
        Args:
            include_author: Include author details
            include_target: Include target details (course/instructor/lesson)
            include_stats: Include helpfulness and engagement stats
            include_replies: Include reply threads
        """
        data = {
            "id": str(self.id),
            "title": self.title,
            "comment": self.comment,
            "review_type": self.review_type.value,
            "status": self.status.value,
            "is_anonymous": self.is_anonymous,
            "is_verified": self.is_verified_purchase,
            "rating_overall": self.rating_overall,
            "rating_content": self.rating_content,
            "rating_teaching": self.rating_teaching,
            "rating_difficulty": self.rating_difficulty,
            "average_rating": self.average_rating,
            "recommend": self.recommend,
            "would_take_again": self.would_take_again,
            "sentiment_label": self.sentiment_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Include author info (respect anonymity)
        if include_author:
            if self.is_anonymous:
                data["author"] = {
                    "is_anonymous": True,
                    "name": "Anonymous"
                }
            else:
                data["author"] = {
                    "id": str(self.author_id),
                    "name": self.author.full_name,
                    "username": self.author.username,
                    "avatar_url": self.author.avatar_url,
                    "is_verified": self.author.is_verified
                }
        
        # Include target info
        if include_target:
            target_data = {}
            if self.course_id:
                target_data["course"] = {
                    "id": str(self.course_id),
                    "title": self.course.title if self.course else None,
                    "code": self.course.code if self.course else None
                }
            if self.instructor_id:
                target_data["instructor"] = {
                    "id": str(self.instructor_id),
                    "name": self.instructor.full_name if self.instructor else None,
                    "username": self.instructor.username if self.instructor else None
                }
            if self.lesson_id:
                target_data["lesson"] = {
                    "id": str(self.lesson_id),
                    "title": self.lesson.title if self.lesson else None
                }
            if self.enrollment_id:
                target_data["enrollment"] = {
                    "id": str(self.enrollment_id)
                }
            data["target"] = target_data
        
        # Include engagement stats
        if include_stats:
            data["stats"] = {
                "helpful_count": self.helpful_count,
                "not_helpful_count": self.not_helpful_count,
                "helpfulness_score": self.helpfulness_score,
                "reply_count": len(self.replies),
                "report_count": self.report_count
            }
        
        # Include replies
        if include_replies and self.replies:
            data["replies"] = [
                reply.get_summary(include_author=True)
                for reply in sorted(self.replies, key=lambda x: x.created_at)
            ]
        
        return data

class ReviewHelpfulVote(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_helpful_votes"
    
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # Relationships
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="helpful_votes"
    )
    
    user: Mapped["User"] = relationship("User")
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('review_id', 'user_id', name='uq_review_user_vote'),
    )

class ReviewReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_reports"
    
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    reason: Mapped[str] = mapped_column(String(50), nullable=False)  # spam, inappropriate, false_info, other
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",  # pending, reviewed, resolved, dismissed
        nullable=False
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id')
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    
    # Relationships
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="reports"
    )
    
    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reporter_id]
    )
    
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by]
    )
    
    __table_args__ = (
        db.UniqueConstraint('review_id', 'reporter_id', name='uq_review_reporter'),
    )

class ReviewReply(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_replies"
    
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_official_response: Mapped[bool] = mapped_column(Boolean, default=False)  # From instructor/owner
    
    # For threaded replies
    parent_reply_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('review_replies.id', ondelete='CASCADE')
    )
    
    # Relationships
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="replies"
    )
    
    author: Mapped["User"] = relationship("User")
    
    parent_reply: Mapped[Optional["ReviewReply"]] = relationship(
        "ReviewReply",
        remote_side=[id],
        back_populates="child_replies"
    )
    
    child_replies: Mapped[List["ReviewReply"]] = relationship(
        "ReviewReply",
        back_populates="parent_reply",
        cascade="all, delete-orphan"
    )
    
    def get_summary(self, include_author: bool = False) -> dict:
        """Get reply summary for API responses."""
        data = {
            "id": str(self.id),
            "review_id": str(self.review_id),
            "comment": self.comment,
            "is_official_response": self.is_official_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_author:
            data["author"] = {
                "id": str(self.author_id),
                "name": self.author.full_name,
                "username": self.author.username,
                "avatar_url": self.author.avatar_url
            }
        
        return data

# Update User model to include review relationships
# In app/models/user.py, add these relationships:

# reviews_authored: Mapped[List["Review"]] = relationship(
#     "Review",
#     back_populates="author",
#     foreign_keys="Review.author_id",
#     cascade="all, delete-orphan"
# )

# reviews_received: Mapped[List["Review"]] = relationship(
#     "Review",
#     back_populates="instructor",
#     foreign_keys="Review.instructor_id"
# )

# helpful_votes: Mapped[List["ReviewHelpfulVote"]] = relationship(
#     "ReviewHelpfulVote",
#     back_populates="user",
#     cascade="all, delete-orphan"
# )

# review_reports: Mapped[List["ReviewReport"]] = relationship(
#     "ReviewReport",
#     back_populates="reporter",
#     foreign_keys="ReviewReport.reporter_id"
# )
```

## Pydantic Schemas for Reviews

```python
# app/schemas/review.py
from pydantic import BaseModel, Field, validator
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
    
    @validator('comment')
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
    
    @validator('status')
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
```

## Service Layer Implementation

```python
# app/services/review_service.py
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, case
import math

from app.models.review import (
    Review, ReviewType, ReviewStatus, 
    ReviewHelpfulVote, ReviewReport, ReviewReply
)
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewModerationUpdate,
    ReviewVoteCreate, ReviewReportCreate, ReviewReplyCreate,
    ReviewFilters
)

class ReviewService:
    
    @staticmethod
    def get_reviews(
        db: Session,
        filters: ReviewFilters,
        page: int = 1,
        page_size: int = 20,
        include_hidden: bool = False,
        current_user: Optional[User] = None
    ) -> Tuple[List[Review], int]:
        """
        Get filtered reviews with pagination.
        
        Args:
            filters: Filter criteria
            page: Page number (1-indexed)
            page_size: Items per page
            include_hidden: Include hidden reviews (admin/instructor only)
            current_user: Current user for permission checks
        
        Returns:
            Tuple of (reviews, total_count)
        """
        query = db.query(Review)
        
        # Apply filters
        if filters.review_type:
            query = query.filter(Review.review_type == filters.review_type)
        
        if filters.status:
            query = query.filter(Review.status == filters.status)
        elif not include_hidden:
            # Only show approved reviews for non-admin users
            query = query.filter(Review.status == ReviewStatus.APPROVED)
        
        if filters.course_id:
            query = query.filter(Review.course_id == filters.course_id)
        
        if filters.instructor_id:
            query = query.filter(Review.instructor_id == filters.instructor_id)
        
        if filters.lesson_id:
            query = query.filter(Review.lesson_id == filters.lesson_id)
        
        if filters.author_id:
            query = query.filter(Review.author_id == filters.author_id)
        
        if filters.min_rating:
            query = query.filter(
                or_(
                    Review.rating_overall >= filters.min_rating,
                    Review.average_rating >= filters.min_rating
                )
            )
        
        if filters.max_rating:
            query = query.filter(
                or_(
                    Review.rating_overall <= filters.max_rating,
                    Review.average_rating <= filters.max_rating
                )
            )
        
        if filters.recommend is not None:
            query = query.filter(Review.recommend == filters.recommend)
        
        if filters.is_verified is not None:
            query = query.filter(Review.is_verified_purchase == filters.is_verified)
        
        if filters.date_from:
            query = query.filter(Review.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Review.created_at <= filters.date_to)
        
        # Permission checks
        if current_user:
            if current_user.role == UserRole.STUDENT:
                # Students can only see their own pending/hidden reviews
                query = query.filter(
                    or_(
                        Review.status == ReviewStatus.APPROVED,
                        and_(
                            Review.author_id == current_user.id,
                            Review.status.in_([ReviewStatus.PENDING, ReviewStatus.HIDDEN])
                        )
                    )
                )
            elif current_user.role == UserRole.INSTRUCTOR:
                # Instructors can see all approved reviews + their own pending/hidden
                # + reviews about them (if hidden)
                query = query.filter(
                    or_(
                        Review.status == ReviewStatus.APPROVED,
                        Review.author_id == current_user.id,
                        and_(
                            Review.instructor_id == current_user.id,
                            Review.status.in_([ReviewStatus.PENDING, ReviewStatus.HIDDEN])
                        )
                    )
                )
        else:
            # Anonymous users only see approved reviews
            query = query.filter(Review.status == ReviewStatus.APPROVED)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_column = {
            "created_at": Review.created_at,
            "updated_at": Review.updated_at,
            "rating": Review.rating_overall,
            "helpfulness": Review.helpful_count,
        }.get(filters.sort_by, Review.created_at)
        
        if filters.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()
        
        return reviews, total_count
    
    @staticmethod
    def get_review(db: Session, review_id: UUID, current_user: Optional[User] = None) -> Review:
        """
        Get review by ID with permission checks.
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Permission check
        if review.status != ReviewStatus.APPROVED:
            if not current_user:
                raise HTTPException(status_code=403, detail="Review not accessible")
            
            can_view = False
            if current_user.role == UserRole.ADMIN:
                can_view = True
            elif review.author_id == current_user.id:
                can_view = True
            elif current_user.role == UserRole.INSTRUCTOR and review.instructor_id == current_user.id:
                can_view = True
            
            if not can_view:
                raise HTTPException(status_code=403, detail="Review not accessible")
        
        return review
    
    @staticmethod
    def create_review(
        db: Session, 
        review_data: dict, 
        author: User
    ) -> Review:
        """
        Create a new review.
        
        Args:
            review_data: Review creation data
            author: User creating the review
        
        Returns:
            Created review
        """
        # Validate target exists
        target_type = review_data.get("review_type")
        target_id = None
        
        if target_type == ReviewType.COURSE:
            target_id = review_data.get("course_id")
            target = db.query(Course).filter(Course.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Course not found")
            
            # Check if user is enrolled (for verification)
            enrollment = db.query(Enrollment).filter(
                Enrollment.course_id == target_id,
                Enrollment.student_id == author.id,
                Enrollment.status == "completed"
            ).first()
            if enrollment:
                review_data["is_verified_purchase"] = True
                review_data["enrollment_id"] = enrollment.id
        
        elif target_type == ReviewType.INSTRUCTOR:
            target_id = review_data.get("instructor_id")
            target = db.query(User).filter(
                User.id == target_id,
                User.roles.any(name="instructor")
            ).first()
            if not target:
                raise HTTPException(status_code=404, detail="Instructor not found")
        
        elif target_type == ReviewType.LESSON:
            target_id = review_data.get("lesson_id")
            target = db.query(Lesson).filter(Lesson.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Lesson not found")
            
            review_data["course_id"] = target.course_id
        
        # Check for existing review
        existing_query = db.query(Review).filter(
            Review.author_id == author.id,
            Review.review_type == target_type
        )
        
        if target_type == ReviewType.COURSE:
            existing_query = existing_query.filter(Review.course_id == target_id)
        elif target_type == ReviewType.INSTRUCTOR:
            existing_query = existing_query.filter(Review.instructor_id == target_id)
        elif target_type == ReviewType.LESSON:
            existing_query = existing_query.filter(Review.lesson_id == target_id)
        
        existing = existing_query.first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="You have already reviewed this target"
            )
        
        # Create review
        review_data["author_id"] = author.id
        review_data["status"] = ReviewStatus.PENDING
        
        # Auto-approve if user is verified and has good history
        if author.is_verified and ReviewService._should_auto_approve(db, author):
            review_data["status"] = ReviewStatus.APPROVED
        
        review = Review(**review_data)
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # Calculate sentiment (simplified - integrate with NLP service)
        sentiment = ReviewService._calculate_sentiment(review.comment)
        if sentiment:
            review.sentiment_score = sentiment["score"]
            review.sentiment_label = sentiment["label"]
            db.commit()
            db.refresh(review)
        
        return review
    
    @staticmethod
    def update_review(
        db: Session,
        review_id: UUID,
        update_data: ReviewUpdate,
        current_user: User
    ) -> Review:
        """
        Update existing review.
        
        Args:
            review_id: Review ID to update
            update_data: Update data
            current_user: User making the update
        
        Returns:
            Updated review
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Permission check
        if review.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot update this review")
        
        # Update fields
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(review, key, value)
        
        # Reset to pending if admin didn't make the change
        if current_user.role != UserRole.ADMIN:
            review.status = ReviewStatus.PENDING
            review.moderated_by = None
            review.moderated_at = None
            review.moderation_notes = None
        
        # Recalculate sentiment if comment changed
        if update_data.comment:
            sentiment = ReviewService._calculate_sentiment(review.comment)
            if sentiment:
                review.sentiment_score = sentiment["score"]
                review.sentiment_label = sentiment["label"]
        
        db.commit()
        db.refresh(review)
        
        return review
    
    @staticmethod
    def delete_review(
        db: Session,
        review_id: UUID,
        current_user: User
    ) -> None:
        """
        Delete review (soft delete).
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Permission check
        if review.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot delete this review")
        
        # Soft delete
        review.status = ReviewStatus.DELETED
        db.commit()
    
    @staticmethod
    def moderate_review(
        db: Session,
        review_id: UUID,
        moderation_data: ReviewModerationUpdate,
        moderator: User
    ) -> Review:
        """
        Moderate review (approve/reject/hide).
        
        Args:
            review_id: Review ID to moderate
            moderation_data: Moderation data
            moderator: User moderating
        
        Returns:
            Moderated review
        """
        if moderator.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can moderate reviews")
        
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Update moderation fields
        review.status = moderation_data.status
        review.moderated_by = moderator.id
        review.moderated_at = datetime.utcnow()
        review.moderation_notes = moderation_data.moderation_notes
        
        db.commit()
        db.refresh(review)
        
        return review
    
    @staticmethod
    def vote_helpful(
        db: Session,
        review_id: UUID,
        vote_data: ReviewVoteCreate,
        voter: User
    ) -> dict:
        """
        Vote on review helpfulness.
        
        Args:
            review_id: Review ID to vote on
            vote_data: Vote data
            voter: User voting
        
        Returns:
            Vote result
        """
        review = db.query(Review).filter(
            Review.id == review_id,
            Review.status == ReviewStatus.APPROVED
        ).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Check for existing vote
        existing_vote = db.query(ReviewHelpfulVote).filter(
            ReviewHelpfulVote.review_id == review_id,
            ReviewHelpfulVote.user_id == voter.id
        ).first()
        
        if existing_vote:
            # Update existing vote
            if existing_vote.is_helpful != vote_data.is_helpful:
                # Update counters
                if existing_vote.is_helpful:
                    review.helpful_count -= 1
                else:
                    review.not_helpful_count -= 1
                
                existing_vote.is_helpful = vote_data.is_helpful
                
                if vote_data.is_helpful:
                    review.helpful_count += 1
                else:
                    review.not_helpful_count += 1
        else:
            # Create new vote
            vote = ReviewHelpfulVote(
                review_id=review_id,
                user_id=voter.id,
                is_helpful=vote_data.is_helpful
            )
            db.add(vote)
            
            # Update counters
            if vote_data.is_helpful:
                review.helpful_count += 1
            else:
                review.not_helpful_count += 1
        
        db.commit()
        db.refresh(review)
        
        return {
            "review_id": str(review_id),
            "helpful_count": review.helpful_count,
            "not_helpful_count": review.not_helpful_count,
            "helpfulness_score": review.helpfulness_score,
            "user_vote": vote_data.is_helpful
        }
    
    @staticmethod
    def report_review(
        db: Session,
        review_id: UUID,
        report_data: ReviewReportCreate,
        reporter: User
    ) -> ReviewReport:
        """
        Report a review.
        
        Args:
            review_id: Review ID to report
            report_data: Report data
            reporter: User reporting
        
        Returns:
            Created report
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Check for existing report
        existing_report = db.query(ReviewReport).filter(
            ReviewReport.review_id == review_id,
            ReviewReport.reporter_id == reporter.id
        ).first()
        
        if existing_report:
            raise HTTPException(
                status_code=400,
                detail="You have already reported this review"
            )
        
        # Create report
        report = ReviewReport(
            review_id=review_id,
            reporter_id=reporter.id,
            reason=report_data.reason,
            description=report_data.description
        )
        db.add(report)
        
        # Update report counter
        review.report_count += 1
        db.commit()
        db.refresh(report)
        
        return report
    
    @staticmethod
    def add_reply(
        db: Session,
        review_id: UUID,
        reply_data: ReviewReplyCreate,
        author: User
    ) -> ReviewReply:
        """
        Add reply to review.
        
        Args:
            review_id: Review ID to reply to
            reply_data: Reply data
            author: User replying
        
        Returns:
            Created reply
        """
        review = db.query(Review).filter(
            Review.id == review_id,
            Review.status == ReviewStatus.APPROVED
        ).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Check if user can reply
        can_reply = False
        
        if author.role == UserRole.ADMIN:
            can_reply = True
        elif review.author_id == author.id:
            can_reply = True
        elif author.role == UserRole.INSTRUCTOR:
            # Instructor can reply to reviews about them
            if review.instructor_id == author.id:
                can_reply = True
                reply_data.is_official_response = True
            # Instructor can reply to reviews of their courses
            elif review.course_id:
                # Check if author teaches this course
                from app.models.course_instructor import CourseInstructor
                is_instructor = db.query(CourseInstructor).filter(
                    CourseInstructor.course_id == review.course_id,
                    CourseInstructor.instructor_id == author.id
                ).first()
                if is_instructor:
                    can_reply = True
                    reply_data.is_official_response = True
        
        if not can_reply:
            raise HTTPException(
                status_code=403,
                detail="You cannot reply to this review"
            )
        
        # Create reply
        reply = ReviewReply(
            review_id=review_id,
            author_id=author.id,
            comment=reply_data.comment,
            is_official_response=reply_data.is_official_response
        )
        db.add(reply)
        db.commit()
        db.refresh(reply)
        
        return reply
    
    @staticmethod
    def get_review_analytics(
        db: Session,
        target_type: Optional[ReviewType] = None,
        target_id: Optional[UUID] = None,
        timeframe_days: int = 30
    ) -> dict:
        """
        Get review analytics.
        
        Args:
            target_type: Type of target to analyze
            target_id: Specific target ID
            timeframe_days: Timeframe for recent trend
        
        Returns:
            Analytics data
        """
        query = db.query(Review).filter(Review.status == ReviewStatus.APPROVED)
        
        if target_type:
            query = query.filter(Review.review_type == target_type)
        
        if target_id:
            if target_type == ReviewType.COURSE:
                query = query.filter(Review.course_id == target_id)
            elif target_type == ReviewType.INSTRUCTOR:
                query = query.filter(Review.instructor_id == target_id)
            elif target_type == ReviewType.LESSON:
                query = query.filter(Review.lesson_id == target_id)
        
        # Basic counts
        total_reviews = query.count()
        verified_reviews = query.filter(Review.is_verified_purchase == True).count()
        
        # Rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        rating_reviews = query.filter(Review.rating_overall != None).all()
        
        for review in rating_reviews:
            rating = review.rating_overall
            if 1 <= rating <= 5:
                rating_distribution[rating] += 1
        
        # Average rating
        avg_rating = None
        if rating_reviews:
            avg_rating = sum(r.rating_overall for r in rating_reviews) / len(rating_reviews)
        
        # Recommendation rate
        recommend_reviews = query.filter(Review.recommend != None).count()
        if recommend_reviews > 0:
            recommend_count = query.filter(Review.recommend == True).count()
            recommendation_rate = (recommend_count / recommend_reviews) * 100
        else:
            recommendation_rate = 0
        
        # Sentiment distribution
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        sentiment_reviews = query.filter(Review.sentiment_label != None).all()
        
        for review in sentiment_reviews:
            label = review.sentiment_label
            if label in sentiment_distribution:
                sentiment_distribution[label] += 1
        
        # Recent trend
        recent_trend = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Group by day
        trend_query = db.query(
            func.date(Review.created_at).label('date'),
            func.count(Review.id).label('count'),
            func.avg(Review.rating_overall).label('avg_rating')
        ).filter(
            Review.status == ReviewStatus.APPROVED,
            Review.created_at >= start_date,
            Review.created_at <= end_date
        )
        
        if target_type:
            trend_query = trend_query.filter(Review.review_type == target_type)
        if target_id:
            if target_type == ReviewType.COURSE:
                trend_query = trend_query.filter(Review.course_id == target_id)
            elif target_type == ReviewType.INSTRUCTOR:
                trend_query = trend_query.filter(Review.instructor_id == target_id)
        
        trend_query = trend_query.group_by(func.date(Review.created_at))
        trend_results = trend_query.all()
        
        for result in trend_results:
            recent_trend.append({
                "date": result.date.isoformat(),
                "count": result.count,
                "avg_rating": float(result.avg_rating) if result.avg_rating else None
            })
        
        return {
            "total_reviews": total_reviews,
            "verified_reviews": verified_reviews,
            "average_rating": avg_rating,
            "rating_distribution": rating_distribution,
            "recommendation_rate": recommendation_rate,
            "sentiment_distribution": sentiment_distribution,
            "recent_trend": recent_trend
        }
    
    # Helper methods
    @staticmethod
    def _should_auto_approve(db: Session, author: User) -> bool:
        """Determine if review should be auto-approved."""
        # Check author's review history
        past_reviews = db.query(Review).filter(
            Review.author_id == author.id,
            Review.status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED])
        ).all()
        
        if not past_reviews:
            return author.is_verified  # Auto-approve if verified user
        
        # Calculate approval rate
        approved_count = sum(1 for r in past_reviews if r.status == ReviewStatus.APPROVED)
        approval_rate = approved_count / len(past_reviews) if past_reviews else 0
        
        # Auto-approve if high approval rate
        return approval_rate >= 0.8  # 80% approval rate
    
    @staticmethod
    def _calculate_sentiment(text: str) -> Optional[dict]:
        """Calculate sentiment of text (simplified)."""
        # In production, integrate with NLP service (e.g., NLTK, spaCy, AWS Comprehend)
        # This is a simplified implementation
        positive_words = ["good", "great", "excellent", "awesome", "amazing", "love", "best"]
        negative_words = ["bad", "poor", "terrible", "awful", "hate", "worst", "disappointing"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return {"score": 0.0, "label": "neutral"}
        
        score = (positive_count - negative_count) / total
        
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"
        
        return {"score": score, "label": label}
```

## API Endpoints for Reviews

```python
# app/api/endpoints/reviews.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import uuid

from server.app.api.deps.users import get_db, get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.schemas.review import (
    CourseReviewCreate, InstructorReviewCreate, LessonReviewCreate,
    ReviewUpdate, ReviewModerationUpdate, ReviewInDB,
    ReviewVoteCreate, ReviewReportCreate, ReviewReplyCreate,
    ReviewFilters, ReviewAnalytics
)
from app.services.review_service import ReviewService

router = APIRouter()

@router.get("/", response_model=dict)
def get_reviews(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    # Filter parameters
    review_type: Optional[str] = None,
    status: Optional[str] = None,
    course_id: Optional[uuid.UUID] = None,
    instructor_id: Optional[uuid.UUID] = None,
    lesson_id: Optional[uuid.UUID] = None,
    author_id: Optional[uuid.UUID] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    recommend: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|rating|helpfulness)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get filtered reviews with pagination.
    
    - **review_type**: Filter by type (course/instructor/lesson)
    - **status**: Filter by status (pending/approved/rejected/hidden)
    - **course_id**: Filter by course
    - **instructor_id**: Filter by instructor
    - **lesson_id**: Filter by lesson
    - **author_id**: Filter by author
    - **min_rating**: Minimum rating (1-5)
    - **max_rating**: Maximum rating (1-5)
    - **recommend**: Filter by recommendation
    - **is_verified**: Filter by verified purchase
    - **date_from**: Start date (YYYY-MM-DD)
    - **date_to**: End date (YYYY-MM-DD)
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order (asc/desc)
    """
    # Parse dates
    from datetime import datetime
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
    
    # Build filters
    filters = ReviewFilters(
        review_type=review_type,
        status=status,
        course_id=course_id,
        instructor_id=instructor_id,
        lesson_id=lesson_id,
        author_id=author_id,
        min_rating=min_rating,
        max_rating=max_rating,
        recommend=recommend,
        is_verified=is_verified,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get reviews
    include_hidden = current_user and current_user.role in [UserRole.ADMIN, UserRole.INSTRUCTOR]
    reviews, total_count = ReviewService.get_reviews(
        db, filters, page, page_size, include_hidden, current_user
    )
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "items": [ReviewInDB.from_orm(review) for review in reviews],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@router.post("/course", response_model=ReviewInDB, status_code=status.HTTP_201_CREATED)
def create_course_review(
    *,
    db: Session = Depends(get_db),
    review_in: CourseReviewCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a course review.
    
    - Users can review courses they have completed
    - Verified purchases get special badge
    """
    review = ReviewService.create_review(db, review_in.dict(), current_user)
    return ReviewInDB.from_orm(review)

@router.post("/instructor", response_model=ReviewInDB, status_code=status.HTTP_201_CREATED)
def create_instructor_review(
    *,
    db: Session = Depends(get_db),
    review_in: InstructorReviewCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create an instructor review.
    
    - Users can review instructors they have taken courses from
    """
    review = ReviewService.create_review(db, review_in.dict(), current_user)
    return ReviewInDB.from_orm(review)

@router.post("/lesson", response_model=ReviewInDB, status_code=status.HTTP_201_CREATED)
def create_lesson_review(
    *,
    db: Session = Depends(get_db),
    review_in: LessonReviewCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a lesson review.
    
    - Users can review lessons they have completed
    """
    review = ReviewService.create_review(db, review_in.dict(), current_user)
    return ReviewInDB.from_orm(review)

@router.get("/{review_id}", response_model=ReviewInDB)
def get_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get review by ID.
    """
    review = ReviewService.get_review(db, review_id, current_user)
    return ReviewInDB.from_orm(review)

@router.put("/{review_id}", response_model=ReviewInDB)
def update_review(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update review.
    
    - Only author or admin can update
    - Status resets to pending if not admin
    """
    review = ReviewService.update_review(db, review_id, review_in, current_user)
    return ReviewInDB.from_orm(review)

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete review (soft delete).
    
    - Only author or admin can delete
    """
    ReviewService.delete_review(db, review_id, current_user)

@router.put("/{review_id}/moderate", response_model=ReviewInDB)
def moderate_review(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    moderation_in: ReviewModerationUpdate,
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Moderate review (admin only).
    
    - Approve, reject, or hide reviews
    """
    review = ReviewService.moderate_review(db, review_id, moderation_in, current_user)
    return ReviewInDB.from_orm(review)

@router.post("/{review_id}/vote", response_model=dict)
def vote_review(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    vote_in: ReviewVoteCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Vote on review helpfulness.
    
    - Users can vote helpful/not helpful
    - One vote per user per review
    """
    return ReviewService.vote_helpful(db, review_id, vote_in, current_user)

@router.post("/{review_id}/report", response_model=dict)
def report_review(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    report_in: ReviewReportCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Report a review.
    
    - Users can report inappropriate content
    - One report per user per review
    """
    report = ReviewService.report_review(db, review_id, report_in, current_user)
    return {
        "id": str(report.id),
        "review_id": str(report.review_id),
        "reason": report.reason,
        "status": report.status,
        "created_at": report.created_at.isoformat()
    }

@router.post("/{review_id}/replies", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_review_reply(
    *,
    db: Session = Depends(get_db),
    review_id: uuid.UUID,
    reply_in: ReviewReplyCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Add reply to review.
    
    - Author, instructor, or admin can reply
    - Instructor replies are marked as official
    """
    reply = ReviewService.add_reply(db, review_id, reply_in, current_user)
    return {
        "id": str(reply.id),
        "review_id": str(reply.review_id),
        "author": {
            "id": str(reply.author_id),
            "name": reply.author.full_name,
            "username": reply.author.username
        },
        "comment": reply.comment,
        "is_official_response": reply.is_official_response,
        "created_at": reply.created_at.isoformat()
    }

@router.get("/{review_id}/replies", response_model=List[dict])
def get_review_replies(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all replies for a review.
    """
    # First get the review to check permissions
    review = ReviewService.get_review(db, review_id, current_user)
    
    # Get replies
    from app.models.review import ReviewReply
    replies = db.query(ReviewReply).filter(
        ReviewReply.review_id == review_id
    ).order_by(ReviewReply.created_at.asc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(reply.id),
            "author": {
                "id": str(reply.author_id),
                "name": reply.author.full_name,
                "username": reply.author.username,
                "avatar_url": reply.author.avatar_url
            },
            "comment": reply.comment,
            "is_official_response": reply.is_official_response,
            "created_at": reply.created_at.isoformat()
        }
        for reply in replies
    ]

@router.get("/analytics/{target_type}", response_model=ReviewAnalytics)
def get_review_analytics(
    target_type: str,
    target_id: Optional[uuid.UUID] = None,
    timeframe_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get review analytics.
    
    - **target_type**: Type of target (course/instructor/lesson)
    - **target_id**: Specific target ID (optional)
    - **timeframe_days**: Days for recent trend analysis
    
    Permissions:
    - Admins can see all analytics
    - Instructors can see their own or their course analytics
    - Students/Parents can see public analytics
    """
    # Validate target type
    try:
        review_type = ReviewType(target_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target type")
    
    # Permission check
    if review_type == ReviewType.INSTRUCTOR and target_id:
        if current_user.role != UserRole.ADMIN and str(current_user.id) != str(target_id):
            raise HTTPException(status_code=403, detail="Cannot view analytics for this instructor")
    
    elif review_type == ReviewType.COURSE and target_id:
        if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
            # Check if user is enrolled
            from app.models.enrollment import Enrollment
            enrollment = db.query(Enrollment).filter(
                Enrollment.course_id == target_id,
                Enrollment.student_id == current_user.id
            ).first()
            if not enrollment:
                raise HTTPException(status_code=403, detail="Cannot view analytics for this course")
    
    # Get analytics
    analytics = ReviewService.get_review_analytics(db, review_type, target_id, timeframe_days)
    return ReviewAnalytics(**analytics)

@router.get("/user/{user_id}/reviews", response_model=dict)
def get_user_reviews(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    review_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all reviews by a specific user.
    
    - Users can see their own reviews (including pending/hidden)
    - Others can only see approved reviews
    """
    # Permission check
    if str(user_id) != str(current_user.id) and current_user.role != UserRole.ADMIN:
        # Non-admin viewing other user's reviews
        status = "approved"
        include_hidden = False
    else:
        # Viewing own reviews or admin
        status = None
        include_hidden = True
    
    # Build filters
    filters = ReviewFilters(
        author_id=user_id,
        review_type=review_type,
        status=status
    )
    
    # Get reviews
    reviews, total_count = ReviewService.get_reviews(
        db, filters, page, page_size, include_hidden, current_user
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "items": [ReviewInDB.from_orm(review) for review in reviews],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "user_id": str(user_id)
    }

@router.get("/course/{course_id}/reviews/summary", response_model=dict)
def get_course_reviews_summary(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get course review summary.
    
    Includes:
    - Average rating
    - Rating distribution
    - Total reviews
    - Recent reviews
    """
    # Check if course exists
    from app.models.course import Course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get analytics
    analytics = ReviewService.get_review_analytics(
        db, ReviewType.COURSE, course_id, 30
    )
    
    # Get recent reviews
    filters = ReviewFilters(
        review_type=ReviewType.COURSE,
        course_id=course_id,
        status=ReviewStatus.APPROVED,
        sort_by="created_at",
        sort_order="desc"
    )
    
    reviews, _ = ReviewService.get_reviews(db, filters, 1, 5, False, current_user)
    
    return {
        "course_id": str(course_id),
        "course_title": course.title,
        "analytics": analytics,
        "recent_reviews": [
            {
                "id": str(review.id),
                "author": {
                    "id": str(review.author_id),
                    "name": review.author.full_name if not review.is_anonymous else "Anonymous",
                    "is_anonymous": review.is_anonymous
                },
                "rating": review.rating_overall,
                "comment": review.comment[:200] + "..." if len(review.comment) > 200 else review.comment,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ]
    }
```

## Complete API Endpoint Summary for Reviews

### **Reviews** (`/api/reviews`)
- `GET /` - List reviews with advanced filtering & pagination
- `POST /course` - Create course review
- `POST /instructor` - Create instructor review
- `POST /lesson` - Create lesson review
- `GET /{review_id}` - Get review by ID
- `PUT /{review_id}` - Update review (author/admin)
- `DELETE /{review_id}` - Delete review (soft delete, author/admin)
- `PUT /{review_id}/moderate` - Moderate review (admin only)
- `POST /{review_id}/vote` - Vote on review helpfulness
- `POST /{review_id}/report` - Report review
- `POST /{review_id}/replies` - Add reply to review
- `GET /{review_id}/replies` - Get review replies
- `GET /analytics/{target_type}` - Get review analytics
- `GET /user/{user_id}/reviews` - Get user's reviews
- `GET /course/{course_id}/reviews/summary` - Get course review summary

## Key Features of This Review System:

### **1. Multi-Target Reviews**
- Courses, instructors, lessons
- Enrollment-based verification
- Proper relationship constraints

### **2. Comprehensive Rating System**
- Overall rating
- Content rating
- Teaching rating
- Difficulty rating
- Recommendation flag
- "Would take again" flag

### **3. Moderation Workflow**
- Pending → Approved/Rejected/Hidden
- Auto-approval for trusted users
- Moderation notes
- Admin-only moderation endpoints

### **4. Engagement Features**
- Helpful/Not helpful voting
- Reply system with official responses
- Report system with tracking
- Sentiment analysis (basic implementation)

### **5. Privacy & Anonymity**
- Anonymous posting option
- Visibility controls
- Proper permission checks
- GDPR-compliant data handling

### **6. Analytics & Insights**
- Rating distribution
- Recommendation rates
- Sentiment analysis
- Recent trends
- Verified vs unverified reviews

### **7. Integration with Scoring System**
- Enrollment verification
- Course completion validation
- Instructor relationship checks
- Performance context for reviews

### **8. Professional Design Patterns**
- Service layer abstraction
- Consistent error handling
- Proper validation
- Comprehensive documentation
- RESTful endpoints

This review system integrates seamlessly with your scoring application, providing a professional platform for students, parents, and instructors to share feedback and insights about courses, lessons, and teaching quality.