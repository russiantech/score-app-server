# # ============================================================================
# # COMMENT ENDPOINTS
# # ============================================================================

# # app/api/v1/comments.py
# from typing import Optional
# from uuid import UUID
# from fastapi import APIRouter, Depends, Query, Request
# from sqlalchemy.orm import Session

# from app.api.deps import get_db, get_current_user
# from app.models.user import User
# from app.schemas.comment import (
#     CommentCreate,
#     CommentUpdate
# )
# from app.services.comment_service import CommentService
# from app.utils.responses import api_response, PageSerializer

# router = APIRouter(tags=["Comments"])


# @router.get("")
# def list_comments(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(20, ge=1, le=100, description="Items per page"),
#     score_id: Optional[UUID] = Query(None, description="Filter by score"),
#     user_id: Optional[UUID] = Query(None, description="Filter by user"),
# ):
#     """
#     Get paginated list of comments.
    
#     - **Requires authentication**
#     - Users see comments on scores they have access to
#     """
#     comments = CommentService.get_comments(
#         db=db,
#         page=page,
#         page_size=page_size,
#         score_id=score_id,
#         user_id=user_id,
#         current_user=current_user
#     )
    
#     paginator = PageSerializer(
#         request=request,
#         obj=comments,
#         resource_name="comments",
#         page=page,
#         page_size=page_size
#     )
    
#     return paginator.get_response(message="Comments retrieved successfully")


# @router.get("/{comment_id}")
# def get_comment(
#     request: Request,
#     comment_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get comment by ID.
    
#     - **Requires authentication**
#     """
#     comment = CommentService.get_comment(
#         db=db,
#         comment_id=comment_id,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=comment.get_summary(),
#         message="Comment retrieved successfully",
#         path=str(request.url.path)
#     )


# @router.post("")
# def create_comment(
#     request: Request,
#     comment_data: CommentCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Create a new comment on a score.
    
#     - **Requires authentication**
#     - Students can comment on their own scores
#     - Instructors can comment on scores for their courses
#     - Parents can comment on their children's scores
#     """
#     comment = CommentService.create_comment(
#         db=db,
#         comment_data=comment_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=comment.get_summary(),
#         message="Comment created successfully",
#         status_code=201,
#         path=str(request.url.path)
#     )


# @router.patch("/{comment_id}")
# def update_comment(
#     request: Request,
#     comment_id: UUID,
#     comment_data: CommentUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update a comment.
    
#     - **Owner or Admin only**
#     """
#     updated_comment = CommentService.update_comment(
#         db=db,
#         comment_id=comment_id,
#         comment_data=comment_data,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         data=updated_comment.get_summary(),
#         message="Comment updated successfully",
#         path=str(request.url.path)
#     )


# @router.delete("/{comment_id}")
# def delete_comment(
#     request: Request,
#     comment_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Delete a comment.
    
#     - **Owner or Admin only**
#     """
#     CommentService.delete_comment(
#         db=db,
#         comment_id=comment_id,
#         current_user=current_user
#     )
    
#     return api_response(
#         success=True,
#         message="Comment deleted successfully",
#         path=str(request.url.path)
#     )


# @router.get("/score/{score_id}")
# def get_score_comments(
#     request: Request,
#     score_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
# ):
#     """
#     Get all comments for a specific score.
    
#     - **Requires authentication**
#     - Returns comments in chronological order
#     """
#     comments = CommentService.get_score_comments(
#         db=db,
#         score_id=score_id,
#         page=page,
#         page_size=page_size,
#         current_user=current_user
#     )
    
#     paginator = PageSerializer(
#         request=request,
#         obj=comments,
#         resource_name="comments",
#         page=page,
#         page_size=page_size,
#         context_key="score_id",
#         context_id=str(score_id)
#     )
    
#     return paginator.get_response(message="Score comments retrieved successfully")



# now reviews

# app/api/endpoints/reviews.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import uuid

from app.api.deps.users import get_db, get_current_user, get_current_admin
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

