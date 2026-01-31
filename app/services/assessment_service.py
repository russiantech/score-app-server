# from sqlalchemy.orm import Session
# from app.models.assessment import Assessment
# from app.schemas.assessment import AssessmentCreate

# def create_assessment(db: Session, data: AssessmentCreate):
#     assessment = Assessment(**data.dict())
#     db.add(assessment)
#     db.commit()
#     db.refresh(assessment)
#     return assessment

# def get_assessments_by_lesson(db: Session, lesson_id):
#     return db.query(Assessment).filter(Assessment.lesson_id == lesson_id).all()



# v2

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.assessment import Assessment, Submission, AssessmentType, SubmissionStatus
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, SubmissionCreate, SubmissionUpdate, GradeSubmission
# from app.services.user_service import UserService


class AssessmentService:
    """Service layer for assessment operations."""
    
    @staticmethod
    def get_assessment(db: Session, assessment_id: UUID) -> Assessment:
        """Get assessment by ID."""
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        return assessment
    
    @staticmethod
    def get_assessments(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        course_id: Optional[UUID] = None,
        assessment_type: Optional[AssessmentType] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Assessment]:
        """Get list of assessments with filtering."""
        query = db.query(Assessment)
        
        # Apply filters
        if course_id:
            query = query.filter(Assessment.course_id == course_id)
        
        if assessment_type:
            query = query.filter(Assessment.type == assessment_type)
        
        if is_published is not None:
            query = query.filter(Assessment.is_published == is_published)
        
        if search:
            search_filter = or_(
                Assessment.title.ilike(f"%{search}%"),
                Assessment.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Order by due date (upcoming first)
        query = query.order_by(Assessment.due_date.asc().nullslast())
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get paginated results
        assessments = query.offset(offset).limit(page_size).all()
        
        return assessments
    
    @staticmethod
    def create_assessment(
        db: Session,
        assessment_data: AssessmentCreate,
        current_user: User
    ) -> Assessment:
        """Create a new assessment."""
        # Check if user is instructor for this course
        # TODO: Add course permission check
        
        assessment = Assessment(
            title=assessment_data.title,
            description=assessment_data.description,
            instructions=assessment_data.instructions,
            type=assessment_data.type,
            status=assessment_data.status,
            course_id=assessment_data.course_id,
            created_by=current_user.id,
            total_points=assessment_data.total_points,
            passing_score=assessment_data.passing_score,
            due_date=assessment_data.due_date,
            available_from=assessment_data.available_from,
            available_until=assessment_data.available_until,
            allow_late_submission=assessment_data.allow_late_submission,
            late_penalty_percent=assessment_data.late_penalty_percent,
            max_attempts=assessment_data.max_attempts,
            time_limit_minutes=assessment_data.time_limit_minutes,
            is_published=assessment_data.is_published,
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        return assessment
    
    @staticmethod
    def update_assessment(
        db: Session,
        assessment_id: UUID,
        assessment_data: AssessmentUpdate,
        current_user: User
    ) -> Assessment:
        """Update assessment."""
        assessment = AssessmentService.get_assessment(db, assessment_id)
        
        # Check permissions (only creator or admin can update)
        if str(assessment.created_by) != str(current_user.id):
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this assessment"
                )
        
        # Update fields
        update_data = assessment_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(assessment, field, value)
        
        db.commit()
        db.refresh(assessment)
        
        return assessment
    
    @staticmethod
    def delete_assessment(
        db: Session,
        assessment_id: UUID,
        current_user: User
    ) -> bool:
        """Delete assessment."""
        assessment = AssessmentService.get_assessment(db, assessment_id)
        
        # Check permissions
        if str(assessment.created_by) != str(current_user.id):
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this assessment"
                )
        
        db.delete(assessment)
        db.commit()
        
        return True
    
    @staticmethod
    def publish_assessment(
        db: Session,
        assessment_id: UUID,
        current_user: User
    ) -> Assessment:
        """Publish assessment to make it available to students."""
        assessment = AssessmentService.get_assessment(db, assessment_id)
        
        # Check permissions
        if str(assessment.created_by) != str(current_user.id):
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to publish this assessment"
                )
        
        assessment.is_published = True
        db.commit()
        db.refresh(assessment)
        
        return assessment
    
    @staticmethod
    def get_submission(db: Session, submission_id: UUID) -> Submission:
        """Get submission by ID."""
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        return submission
    
    @staticmethod
    def get_submissions(
        db: Session,
        assessment_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Submission]:
        """Get list of submissions."""
        query = db.query(Submission)
        
        if assessment_id:
            query = query.filter(Submission.assessment_id == assessment_id)
        
        if student_id:
            query = query.filter(Submission.student_id == student_id)
        
        # Order by submission date
        query = query.order_by(Submission.submitted_at.desc().nullslast())
        
        # Pagination
        offset = (page - 1) * page_size
        submissions = query.offset(offset).limit(page_size).all()
        
        return submissions
    
    @staticmethod
    def create_submission(
        db: Session,
        submission_data: SubmissionCreate,
        student_id: UUID,
        current_user: User
    ) -> Submission:
        """Create or update a submission."""
        assessment = AssessmentService.get_assessment(db, submission_data.assessment_id)
        
        # Check if assessment is available
        if not assessment.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment is not currently available"
            )
        
        # Check existing submissions
        existing = db.query(Submission).filter(
            Submission.assessment_id == submission_data.assessment_id,
            Submission.student_id == student_id
        ).all()
        
        attempt_number = len(existing) + 1
        
        # Check max attempts
        if attempt_number > assessment.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempts ({assessment.max_attempts}) reached"
            )
        
        # Check if late
        is_late = False
        if assessment.due_date and datetime.utcnow() > assessment.due_date:
            if not assessment.allow_late_submission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Late submissions are not allowed"
                )
            is_late = True
        
        submission = Submission(
            assessment_id=submission_data.assessment_id,
            student_id=student_id,
            content=submission_data.content,
            attachment_urls=submission_data.attachment_urls,
            status=SubmissionStatus.SUBMITTED,
            attempt_number=attempt_number,
            submitted_at=datetime.utcnow(),
            is_late=is_late
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        return submission
    
    @staticmethod
    def grade_submission(
        db: Session,
        submission_id: UUID,
        grade_data: GradeSubmission,
        current_user: User
    ) -> Submission:
        """Grade a submission."""
        submission = AssessmentService.get_submission(db, submission_id)
        assessment = submission.assessment
        
        # Check permissions (instructor or admin)
        # TODO: Add proper course instructor check
        
        # Validate score doesn't exceed total points
        if grade_data.score > assessment.total_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score cannot exceed total points ({assessment.total_points})"
            )
        
        # Calculate late penalty if applicable
        late_penalty = 0.0
        if submission.is_late and assessment.late_penalty_percent > 0:
            # Calculate days late
            if assessment.due_date:
                days_late = (submission.submitted_at - assessment.due_date).days
                if days_late > 0:
                    late_penalty = (grade_data.score * assessment.late_penalty_percent / 100) * days_late
        
        submission.score = grade_data.score
        submission.feedback = grade_data.feedback
        submission.late_penalty_applied = late_penalty
        submission.status = SubmissionStatus.GRADED
        submission.graded_at = datetime.utcnow()
        submission.graded_by = current_user.id
        
        db.commit()
        db.refresh(submission)
        
        return submission
    
    @staticmethod
    def return_submission(
        db: Session,
        submission_id: UUID,
        current_user: User
    ) -> Submission:
        """Return graded submission to student."""
        submission = AssessmentService.get_submission(db, submission_id)
        
        if submission.status != SubmissionStatus.GRADED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission must be graded before returning"
            )
        
        submission.status = SubmissionStatus.RETURNED
        submission.returned_at = datetime.utcnow()
        
        db.commit()
        db.refresh(submission)
        
        return submission

