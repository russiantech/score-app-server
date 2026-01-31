from typing import Optional
from uuid import UUID
import secrets
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from server.app.models.certificates import Certificate
from app.models.user import User, UserRole
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.certificate import CertificateGenerate, CertificateUpdate

class CertificateService:
    
    @staticmethod
    def generate_certificate_number() -> str:
        """Generate unique certificate number"""
        return f"CERT-{date.today().year}-{secrets.token_hex(6).upper()}"

    @staticmethod
    def get_certificates(
        db: Session,
        page: int,
        page_size: int,
        enrollment_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
        search: Optional[str] = None,
        current_user: User = None
    ):
        """Get filtered certificates with pagination"""
        query = db.query(Certificate)
        
        # Role-based filtering
        if current_user.role == UserRole.STUDENT:
            query = query.join(Enrollment).filter(Enrollment.student_id == current_user.id)
        elif current_user.role == UserRole.PARENT:
            children_ids = db.query(User.id).filter(User.parent_id == current_user.id)
            query = query.join(Enrollment).filter(Enrollment.student_id.in_(children_ids))
        
        # Apply filters
        if enrollment_id:
            query = query.filter(Certificate.enrollment_id == enrollment_id)
        if student_id:
            query = query.join(Enrollment).filter(Enrollment.student_id == student_id)
        if course_id:
            query = query.join(Enrollment).filter(Enrollment.course_id == course_id)
        if search:
            query = query.filter(Certificate.certificate_number.ilike(f"%{search}%"))
        
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    @staticmethod
    def get_certificate(db: Session, certificate_id: UUID, current_user: User):
        """Get certificate by ID"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Permission check
        if current_user.role == UserRole.STUDENT:
            enrollment = db.query(Enrollment).filter(
                Enrollment.id == certificate.enrollment_id,
                Enrollment.student_id == current_user.id
            ).first()
            if not enrollment:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return certificate

    @staticmethod
    def get_certificate_by_number(db: Session, certificate_number: str):
        """Get certificate by number (public endpoint)"""
        certificate = db.query(Certificate).filter(
            Certificate.certificate_number == certificate_number
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        return certificate

    @staticmethod
    def generate_certificate(
        db: Session,
        certificate_data: CertificateGenerate,
        current_user: User
    ):
        """Generate new certificate"""
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Only instructors can generate certificates")
        
        # Verify enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.id == certificate_data.enrollment_id
        ).first()
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        
        # Check if enrollment is completed
        if enrollment.status != EnrollmentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Can only generate certificate for completed enrollments"
            )
        
        # Check if certificate already exists
        existing = db.query(Certificate).filter(
            Certificate.enrollment_id == certificate_data.enrollment_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Certificate already exists for this enrollment"
            )
        
        # Generate certificate
        certificate_number = CertificateService.generate_certificate_number()
        
        certificate = Certificate(
            enrollment_id=certificate_data.enrollment_id,
            certificate_number=certificate_number,
            issue_date=date.today(),
            certificate_url=certificate_data.certificate_url
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        return certificate

    @staticmethod
    def update_certificate(
        db: Session,
        certificate_id: UUID,
        certificate_data: CertificateUpdate,
        current_user: User
    ):
        """Update certificate"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can update certificates")
        
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        for key, value in certificate_data.dict(exclude_unset=True).items():
            setattr(certificate, key, value)
        
        db.commit()
        db.refresh(certificate)
        
        return certificate

    @staticmethod
    def revoke_certificate(db: Session, certificate_id: UUID, current_user: User):
        """Revoke certificate"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can revoke certificates")
        
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        db.delete(certificate)
        db.commit()

    @staticmethod
    def verify_certificate(db: Session, certificate_number: str):
        """Verify certificate validity"""
        certificate = db.query(Certificate).filter(
            Certificate.certificate_number == certificate_number
        ).first()
        
        if not certificate:
            return {
                "valid": False,
                "message": "Certificate not found"
            }
        
        enrollment = db.query(Enrollment).filter(
            Enrollment.id == certificate.enrollment_id
        ).first()
        
        return {
            "valid": True,
            "certificate_number": certificate_number,
            "student_name": enrollment.student.name,
            "course_name": enrollment.course.name,
            "issue_date": str(certificate.issue_date),
            "message": "Certificate is valid"
        }
