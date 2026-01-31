# app/schemas/certificate.py
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime
import uuid

class CertificateBase(BaseModel):
    enrollment_id: uuid.UUID
    title: str
    certificate_url: Optional[str] = None

class CertificateGenerate(CertificateBase):
    pass

class CertificateUpdate(BaseModel):
    title: Optional[str] = None
    certificate_url: Optional[str] = None
    expiry_date: Optional[date] = None

class CertificateInDB(CertificateBase):
    id: uuid.UUID
    student_id: uuid.UUID
    issued_by: uuid.UUID
    certificate_number: str
    issue_date: date
    expiry_date: Optional[date] = None
    qr_code_url: Optional[str] = None
    verification_token: Optional[str] = None
    is_revoked: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CertificateVerification(BaseModel):
    valid: bool
    certificate_number: str
    student_name: str
    course_name: str
    issue_date: date
    message: str

