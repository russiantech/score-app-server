from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.users import get_db, get_current_user
from app.models.user import User
from app.models.assessment import AssessmentType
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    SubmissionCreate,
    SubmissionUpdate,
    GradeSubmission
)
from app.services.assessment_service import AssessmentService
from app.utils.responses import api_response, PageSerializer

router = APIRouter()


# ============================================================================
# ASSESSMENT ENDPOINTS
# ============================================================================

@router.get("")
def list_assessments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    course_id: Optional[UUID] = Query(None, description="Filter by course"),
    assessment_type: Optional[AssessmentType] = Query(None, description="Filter by type"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    search: Optional[str] = Query(None, description="Search by title or description"),
):
    """
    Get paginated list of assessments.
    
    - **Requires authentication**
    - Students see only published assessments
    - Instructors/Admins see all assessments
    """
    assessments = AssessmentService.get_assessments(
        db=db,
        page=page,
        page_size=page_size,
        course_id=course_id,
        assessment_type=assessment_type,
        is_published=is_published,
        search=search
    )
    
    paginator = PageSerializer(
        request=request,
        obj=assessments,
        resource_name="assessments",
        page=page,
        page_size=page_size
    )
    
    return paginator.get_response(message="Assessments retrieved successfully")


@router.get("/{assessment_id}")
def get_assessment(
    request: Request,
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assessment by ID.
    
    - **Requires authentication**
    - Students can only view published assessments
    """
    assessment = AssessmentService.get_assessment(db, assessment_id)
    
    return api_response(
        success=True,
        data=assessment.get_summary(),
        message="Assessment retrieved successfully",
        path=str(request.url.path)
    )


@router.post("")
def create_assessment(
    request: Request,
    assessment_data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new assessment.
    
    - **Instructor/Admin only**
    """
    assessment = AssessmentService.create_assessment(
        db=db,
        assessment_data=assessment_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=assessment.get_summary(),
        message="Assessment created successfully",
        status_code=201,
        path=str(request.url.path)
    )


@router.patch("/{assessment_id}")
def update_assessment(
    request: Request,
    assessment_id: UUID,
    assessment_data: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update assessment.
    
    - **Creator or Admin only**
    """
    updated_assessment = AssessmentService.update_assessment(
        db=db,
        assessment_id=assessment_id,
        assessment_data=assessment_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=updated_assessment.get_summary(),
        message="Assessment updated successfully",
        path=str(request.url.path)
    )


@router.delete("/{assessment_id}")
def delete_assessment(
    request: Request,
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete assessment.
    
    - **Creator or Admin only**
    """
    AssessmentService.delete_assessment(
        db=db,
        assessment_id=assessment_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        message="Assessment deleted successfully",
        path=str(request.url.path)
    )


@router.post("/{assessment_id}/publish")
def publish_assessment(
    request: Request,
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish assessment to make it available to students.
    
    - **Creator or Admin only**
    """
    assessment = AssessmentService.publish_assessment(
        db=db,
        assessment_id=assessment_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=assessment.get_summary(),
        message="Assessment published successfully",
        path=str(request.url.path)
    )


# ============================================================================
# SUBMISSION ENDPOINTS
# ============================================================================

@router.get("/{assessment_id}/submissions")
def list_assessment_submissions(
    request: Request,
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get all submissions for an assessment.
    
    - **Instructor/Admin only**
    """
    submissions = AssessmentService.get_submissions(
        db=db,
        assessment_id=assessment_id,
        page=page,
        page_size=page_size
    )
    
    paginator = PageSerializer(
        request=request,
        obj=submissions,
        resource_name="submissions",
        page=page,
        page_size=page_size,
        context_key="assessment_id",
        context_id=str(assessment_id)
    )
    
    return paginator.get_response(message="Submissions retrieved successfully")


@router.post("/submissions")
def create_submission(
    request: Request,
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit an assessment.
    
    - **Student only**
    - Must have student profile
    """
    # TODO: Get student_id from current user's student profile
    # For now, using placeholder
    from app.services.user_service import UserService
    
    # Get student profile for current user
    # student_profile = db.query(Student).filter(Student.user_id == current_user.id).first()
    # if not student_profile:
    #     return api_response(
    #         success=False,
    #         message="Student profile not found",
    #         status_code=403,
    #         path=str(request.url.path)
    #     )
    
    # Placeholder: Use user ID as student ID
    student_id = current_user.id
    
    submission = AssessmentService.create_submission(
        db=db,
        submission_data=submission_data,
        student_id=student_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=submission.get_summary(),
        message="Submission created successfully",
        status_code=201,
        path=str(request.url.path)
    )


@router.get("/submissions/{submission_id}")
def get_submission(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get submission by ID.
    
    - **Student can view their own submission**
    - **Instructor/Admin can view all submissions**
    """
    submission = AssessmentService.get_submission(db, submission_id)
    
    # Check permissions
    # TODO: Add proper permission check
    
    return api_response(
        success=True,
        data=submission.get_summary(),
        message="Submission retrieved successfully",
        path=str(request.url.path)
    )


@router.post("/submissions/{submission_id}/grade")
def grade_submission(
    request: Request,
    submission_id: UUID,
    grade_data: GradeSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Grade a submission.
    
    - **Instructor/Admin only**
    """
    graded_submission = AssessmentService.grade_submission(
        db=db,
        submission_id=submission_id,
        grade_data=grade_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=graded_submission.get_summary(),
        message="Submission graded successfully",
        path=str(request.url.path)
    )


@router.post("/submissions/{submission_id}/return")
def return_submission(
    request: Request,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return graded submission to student.
    
    - **Instructor/Admin only**
    """
    returned_submission = AssessmentService.return_submission(
        db=db,
        submission_id=submission_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=returned_submission.get_summary(),
        message="Submission returned to student",
        path=str(request.url.path)
    )


@router.get("/my-submissions")
def get_my_submissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get current user's submissions.
    
    - **Student only**
    """
    # TODO: Get student_id from current user's student profile
    student_id = current_user.id  # Placeholder
    
    submissions = AssessmentService.get_submissions(
        db=db,
        student_id=student_id,
        page=page,
        page_size=page_size
    )
    
    paginator = PageSerializer(
        request=request,
        obj=submissions,
        resource_name="submissions",
        page=page,
        page_size=page_size
    )
    
    return paginator.get_response(message="Your submissions retrieved successfully")

