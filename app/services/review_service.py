# from typing import Optional
# from uuid import UUID
# from fastapi import HTTPException
# from sqlalchemy.orm import Session
# from app.models.reviews import Comment
# from app.models.user import User, UserRole
# # from app.models.score import Assessment
# from app.models.enrollment import Enrollment
# from app.schemas.comment import CommentCreate, CommentUpdate
# from app.models.assessment import Assessment

# class CommentService:
    
#     @staticmethod
#     def get_comments(
#         db: Session,
#         page: int,
#         page_size: int,
#         score_id: Optional[UUID] = None,
#         user_id: Optional[UUID] = None,
#         current_user: User = None
#     ):
#         """Get filtered comments with pagination"""
#         query = db.query(Comment)
        
#         # Apply filters
#         if score_id:
#             query = query.filter(Comment.score_id == score_id)
#         if user_id:
#             query = query.filter(Comment.user_id == user_id)
        
#         # Order by creation date
#         query = query.order_by(Comment.created_at.asc())
        
#         offset = (page - 1) * page_size
#         return query.offset(offset).limit(page_size).all()

#     @staticmethod
#     def get_comment(db: Session, comment_id: UUID, current_user: User):
#         """Get comment by ID"""
#         comment = db.query(Comment).filter(Comment.id == comment_id).first()
        
#         if not comment:
#             raise HTTPException(status_code=404, detail="Comment not found")
        
#         return comment

#     @staticmethod
#     def create_comment(
#         db: Session,
#         comment_data: CommentCreate,
#         current_user: User
#     ):
#         """Create new comment"""
#         # Verify score exists
#         score = db.query(Assessment).filter(Assessment.id == comment_data.score_id).first()
#         if not score:
#             raise HTTPException(status_code=404, detail="Assessment not found")
        
#         # Check permissions
#         enrollment = db.query(Enrollment).filter(
#             Enrollment.id == score.enrollment_id
#         ).first()
        
#         can_comment = False
        
#         # Student can comment on their own scores
#         if current_user.role == UserRole.STUDENT and enrollment.student_id == current_user.id:
#             can_comment = True
        
#         # Instructor can comment on scores for their courses
#         elif current_user.role == UserRole.INSTRUCTOR:
#             from app.models.course_instructor import CourseInstructor
#             is_instructor = db.query(CourseInstructor).filter(
#                 CourseInstructor.course_id == enrollment.course_id,
#                 CourseInstructor.instructor_id == current_user.id
#             ).first()
#             if is_instructor:
#                 can_comment = True
        
#         # Parent can comment on their children's scores
#         elif current_user.role == UserRole.PARENT:
#             is_parent = db.query(User).filter(
#                 User.id == enrollment.student_id,
#                 User.parent_id == current_user.id
#             ).first()
#             if is_parent:
#                 can_comment = True
        
#         # Admin can comment on everything
#         elif current_user.role == UserRole.ADMIN:
#             can_comment = True
        
#         if not can_comment:
#             raise HTTPException(status_code=403, detail="You cannot comment on this score")
        
#         # Create comment
#         comment = Comment(
#             score_id=comment_data.score_id,
#             user_id=current_user.id,
#             comment=comment_data.comment
#         )
        
#         db.add(comment)
#         db.commit()
#         db.refresh(comment)
        
#         return comment

#     @staticmethod
#     def update_comment(
#         db: Session,
#         comment_id: UUID,
#         comment_data: CommentUpdate,
#         current_user: User
#     ):
#         """Update comment"""
#         comment = db.query(Comment).filter(Comment.id == comment_id).first()
#         if not comment:
#             raise HTTPException(status_code=404, detail="Comment not found")
        
#         # Only owner or admin can update
#         if comment.user_id != current_user.id and current_user.role != UserRole.ADMIN:
#             raise HTTPException(status_code=403, detail="You can only update your own comments")
        
#         for key, value in comment_data.dict(exclude_unset=True).items():
#             setattr(comment, key, value)
        
#         db.commit()
#         db.refresh(comment)
        
#         return comment

#     @staticmethod
#     def delete_comment(db: Session, comment_id: UUID, current_user: User):
#         """Delete comment"""
#         comment = db.query(Comment).filter(Comment.id == comment_id).first()
#         if not comment:
#             raise HTTPException(status_code=404, detail="Comment not found")
        
#         # Only owner or admin can delete
#         if comment.user_id != current_user.id and current_user.role != UserRole.ADMIN:
#             raise HTTPException(status_code=403, detail="You can only delete your own comments")
        
#         db.delete(comment)
#         db.commit()

#     @staticmethod
#     def get_score_comments(
#         db: Session,
#         score_id: UUID,
#         page: int,
#         page_size: int,
#         current_user: User
#     ):
#         """Get all comments for a score"""
#         # Verify score exists
#         score = db.query(Assessment).filter(Assessment.id == score_id).first()
#         if not score:
#             raise HTTPException(status_code=404, detail="Assessment not found")
        
#         query = db.query(Comment).filter(Comment.score_id == score_id)
#         query = query.order_by(Comment.created_at.asc())
        
#         offset = (page - 1) * page_size
#         return query.offset(offset).limit(page_size).all()


# v2 - changed to reviews

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

