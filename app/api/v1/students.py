
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps.users import admin_required, get_db
from app.services import student_service
from app.schemas.student import StudentCreate

router = APIRouter()

@router.get("/", dependencies=[Depends(admin_required)])
def list_students(db: Session = Depends(get_db)):
    return student_service.list_students(db)

@router.post("/", dependencies=[Depends(admin_required)])
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    return student_service.create_student(db, data)



# v2

# ============================================================================
# FILE: app/api/routes/student.py
# Student-specific endpoints
# ============================================================================

from fastapi import APIRouter, Depends, Request
from uuid import UUID
from sqlalchemy.orm import Session
from app.services import student_service
from app.api.deps.users import student_required, get_current_user, get_db
from app.utils.responses import api_response

# router = APIRouter()

@router.get("/dashboard")
def get_student_dashboard_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(student_required)
):
    """Get student dashboard data"""
    dashboard = student_service.get_dashboard(db, current_user.id)
    return api_response(
        success=True,
        message="Dashboard data fetched successfully",
        data=dashboard,
        path=str(request.url.path)
    )

@router.get("/courses")
def get_student_courses_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(student_required)
):
    """Get courses student is enrolled in"""
    courses = student_service.get_student_courses(db, current_user.id)
    return api_response(
        success=True,
        message="Courses fetched successfully",
        data=courses,
        path=str(request.url.path)
    )

@router.get("/courses/{course_id}/performance")
def get_course_performance_endpoint(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(student_required)
):
    """Get student's performance in a specific course"""
    performance = student_service.get_course_performance(db, current_user.id, course_id)
    return api_response(
        success=True,
        message="Performance data fetched successfully",
        data=performance,
        path=str(request.url.path)
    )

@router.get("/profile/id-card")
def get_student_id_card_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(student_required)
):
    """Get student ID card data"""
    id_card = student_service.get_id_card_data(db, current_user.id)
    return api_response(
        success=True,
        message="ID card data fetched successfully",
        data=id_card,
        path=str(request.url.path)
    )

