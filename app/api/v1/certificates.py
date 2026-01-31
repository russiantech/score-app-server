
# ============================================================================
# CERTIFICATE ENDPOINTS
# ============================================================================

# app/api/v1/certificates.py
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.users import get_db, get_current_user
from app.models.user import User
from app.schemas.certificate import (
    CertificateCreate,
    CertificateUpdate,
    CertificateGenerate
)
from app.services.certificate_service import CertificateService
from app.utils.responses import api_response, PageSerializer

router = APIRouter(tags=["Certificates"])


@router.get("")
def list_certificates(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    enrollment_id: Optional[UUID] = Query(None, description="Filter by enrollment"),
    student_id: Optional[UUID] = Query(None, description="Filter by student"),
    course_id: Optional[UUID] = Query(None, description="Filter by course"),
    search: Optional[str] = Query(None, description="Search by certificate number"),
):
    """
    Get paginated list of certificates.
    
    - **Requires authentication**
    - Students see only their certificates
    - Instructors see certificates for their courses
    - Admins see all certificates
    """
    certificates = CertificateService.get_certificates(
        db=db,
        page=page,
        page_size=page_size,
        enrollment_id=enrollment_id,
        student_id=student_id,
        course_id=course_id,
        search=search,
        current_user=current_user
    )
    
    paginator = PageSerializer(
        request=request,
        obj=certificates,
        resource_name="certificates",
        page=page,
        page_size=page_size
    )
    
    return paginator.get_response(message="Certificates retrieved successfully")


@router.get("/{certificate_id}")
def get_certificate(
    request: Request,
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get certificate by ID.
    
    - **Requires authentication**
    - Students can view their own certificates
    """
    certificate = CertificateService.get_certificate(
        db=db,
        certificate_id=certificate_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=certificate.get_summary(),
        message="Certificate retrieved successfully",
        path=str(request.url.path)
    )


@router.get("/number/{certificate_number}")
def get_certificate_by_number(
    request: Request,
    certificate_number: str,
    db: Session = Depends(get_db),
):
    """
    Get certificate by certificate number.
    
    - **Public endpoint for verification**
    - No authentication required
    """
    certificate = CertificateService.get_certificate_by_number(
        db=db,
        certificate_number=certificate_number
    )
    
    return api_response(
        success=True,
        data=certificate.get_summary(),
        message="Certificate retrieved successfully",
        path=str(request.url.path)
    )


@router.post("/generate")
def generate_certificate(
    request: Request,
    certificate_data: CertificateGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new certificate for a student.
    
    - **Instructor/Admin only**
    - Validates that student completed the course
    """
    certificate = CertificateService.generate_certificate(
        db=db,
        certificate_data=certificate_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=certificate.get_summary(),
        message="Certificate generated successfully",
        status_code=201,
        path=str(request.url.path)
    )


@router.patch("/{certificate_id}")
def update_certificate(
    request: Request,
    certificate_id: UUID,
    certificate_data: CertificateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update certificate details.
    
    - **Admin only**
    """
    updated_certificate = CertificateService.update_certificate(
        db=db,
        certificate_id=certificate_id,
        certificate_data=certificate_data,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=updated_certificate.get_summary(),
        message="Certificate updated successfully",
        path=str(request.url.path)
    )


@router.delete("/{certificate_id}")
def revoke_certificate(
    request: Request,
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke/delete a certificate.
    
    - **Admin only**
    """
    CertificateService.revoke_certificate(
        db=db,
        certificate_id=certificate_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        message="Certificate revoked successfully",
        path=str(request.url.path)
    )


@router.get("/{certificate_id}/download")
def download_certificate(
    request: Request,
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download certificate PDF.
    
    - **Student can download their own certificates**
    - **Instructor/Admin can download all**
    """
    certificate_file = CertificateService.download_certificate(
        db=db,
        certificate_id=certificate_id,
        current_user=current_user
    )
    
    return certificate_file  # Returns FileResponse


@router.get("/enrollment/{enrollment_id}")
def get_enrollment_certificate(
    request: Request,
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get certificate for a specific enrollment.
    
    - **Requires authentication**
    """
    certificate = CertificateService.get_certificate_by_enrollment(
        db=db,
        enrollment_id=enrollment_id,
        current_user=current_user
    )
    
    return api_response(
        success=True,
        data=certificate.get_summary() if certificate else None,
        message="Certificate retrieved successfully" if certificate else "No certificate found",
        path=str(request.url.path)
    )


@router.post("/verify")
def verify_certificate(
    request: Request,
    certificate_number: str = Query(..., description="Certificate number to verify"),
    db: Session = Depends(get_db),
):
    """
    Verify if a certificate is valid.
    
    - **Public endpoint**
    - Returns validation status and certificate details
    """
    verification = CertificateService.verify_certificate(
        db=db,
        certificate_number=certificate_number
    )
    
    return api_response(
        success=True,
        data=verification,
        message="Certificate verification complete",
        path=str(request.url.path)
    )

