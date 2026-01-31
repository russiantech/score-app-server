
# app/models/review.py
from sqlalchemy import Column, DateTime, String, Text, Integer, Boolean, Float, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from typing import Optional, List
import enum
import uuid
from datetime import datetime

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDMixin

class ReviewType(enum.Enum):
    COURSE = "course"
    INSTRUCTOR = "instructor"
    LESSON = "lesson"
    SCORE = "score"
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
        Uuid(as_uuid=True), 
        ForeignKey('users.id')
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Foreign Keys (at least one must be non-null)
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Target of the review (at least one should be set)
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('courses.id', ondelete='CASCADE'),
        index=True
    )
    instructor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('lessons.id', ondelete='CASCADE'),
        index=True
    )
    score_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('scores.id', ondelete='CASCADE'),
        index=True
    )
    enrollment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('enrollments.id', ondelete='CASCADE'),
        index=True
    )
    
    # product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    #     Uuid(as_uuid=True),
    #     ForeignKey('products.id', ondelete='CASCADE'),
    #     index=True
    # )
    
    # Helpfulness tracking
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    # product: Mapped[Optional["Product"]] = relationship("Product", back_populates="reviews")
    
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
        
    score: Mapped[Optional["Score"]] = relationship(
        "Score",
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
        Uuid(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
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
        UniqueConstraint('review_id', 'user_id', name='uq_review_user_vote'),
    )

class ReviewReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_reports"
    
    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
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
        Uuid(as_uuid=True), 
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
        UniqueConstraint('review_id', 'reporter_id', name='uq_review_reporter'),
    )

class ReviewReply(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_replies"
    
    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_official_response: Mapped[bool] = mapped_column(Boolean, default=False)  # From instructor/owner
    
    # For threaded replies
    parent_reply_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey('review_replies.id', ondelete='CASCADE')
    )
    
    # Relationships
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="replies"
    )
    
    author: Mapped["User"] = relationship("User")
    
    # 🔥 Only 2 required relationships:
    # parent: Mapped[Optional["ReviewReply"]] = relationship(
    #     "ReviewReply",
    #     remote_side="ReviewReply.id",      # IMPORTANT FIX
    # )

    # replies: Mapped[List["ReviewReply"]] = relationship(
    #     "ReviewReply",
    #     cascade="all, delete-orphan"
    # )
    parent: Mapped[Optional["ReviewReply"]] = relationship(
    "ReviewReply",
    back_populates="replies",
    remote_side="ReviewReply.id"
    )

    replies: Mapped[List["ReviewReply"]] = relationship(
        "ReviewReply",
        back_populates="parent",
        overlaps="parent" ,
        cascade="all, delete-orphan"
    )

    
    # parent_reply: Mapped[Optional["ReviewReply"]] = relationship(
    #     "ReviewReply",
    #     remote_side=[id],
    #     back_populates="child_replies"
    # )
    
    # child_replies: Mapped[List["ReviewReply"]] = relationship(
    #     "ReviewReply",
    #     back_populates="parent_reply",
    #     cascade="all, delete-orphan"
    # )
    
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
