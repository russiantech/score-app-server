
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.api.deps.users import admin_required, student_required, get_current_user, get_db
from app.models.user import User
from app.services import student_service
from app.schemas.student import StudentCreate


from uuid import UUID
from app.utils.responses import api_response

router = APIRouter()

@router.get("/", dependencies=[Depends(admin_required)])
def list_students(db: Session = Depends(get_db)):
    return student_service.list_students(db)

@router.post("/", dependencies=[Depends(admin_required)])
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    return student_service.create_student(db, data)

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

# @router.get("/{student_id}/data")
# def get_student_id_card_endpoint(
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user = Depends(student_required)
# ):
#     """Get student ID card data"""
#     id_card = student_service.get_id_card_data(db, current_user.id)
#     return api_response(
#         success=True,
#         message="ID card data fetched successfully",
#         data=id_card,
#         path=str(request.url.path)
#     )



# # v2
# # ============================================================================
# # API ROUTER - ID Card Endpoints
# # FILE: app/api/v1/id_cards.py
# # ============================================================================

# from fastapi import APIRouter, Depends, UploadFile, File, status
# # from sqlalchemy.orm import Session
# # from uuid import UUID

# # from app.database import get_db
# # from app.api.deps import get_current_user
# # from app.models.user import User

# from app.services.id_card_service import (
#     get_student_id_card_data,
#     upload_student_photo,
#     generate_student_id_card
# )

# # from app.utils.api_response import api_response

# # router = APIRouter(prefix="/id-cards", tags=["ID Cards"])


@router.get("/{student_id}/data")
def fetch_student_id_card_data(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch student data required for ID card generation.
    """

    if not (
        current_user.is_admin
        or current_user.is_tutor
        or current_user.id == student_id
    ):
        return api_response(
            success=False,
            message="Not authorized",
            status_code=status.HTTP_403_FORBIDDEN
        )

    data = student_service.get_student_id_card_data(db, student_id)

    return api_response(
        success=True,
        message="Student ID card data retrieved",
        data=data
    )


# @router.post("/{student_id}/upload-photo")
# async def upload_id_photo(
#     student_id: UUID,
#     photo: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Upload or update student photo.
#     """

#     if current_user.id != student_id:
#         return api_response(
#             success=False,
#             message="Unauthorized",
#             status_code=status.HTTP_403_FORBIDDEN
#         )

#     contents = await photo.read()

#     result = student_service.upload_student_photo(
#         db=db,
#         student_id=student_id,
#         image_bytes=contents
#     )

#     return api_response(
#         success=True,
#         message="Photo uploaded successfully",
#         data=result
#     )


@router.get("/{student_id}/generate")
def generate_id_card(
    student_id: UUID,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate ID card payload.
    """

    if current_user.id != student_id:
        return api_response(
            success=False,
            message="Unauthorized",
            status_code=status.HTTP_403_FORBIDDEN
        )

    data = student_service.generate_student_id_card(
        db=db,
        student_id=student_id,
        course_id=course_id
    )

    return api_response(
        success=True,
        message="ID card generated",
        data=data
    )


# @router.get("/health")
# def health():
#     return api_response(
#         success=True,
#         message="ID Card service healthy"
#     )
    




# v2
# app/api/v1/id_cards.py
"""
Student ID Card generation endpoints - Complete implementation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import base64
from io import BytesIO
from PIL import Image

from app.models.user import User
from app.models.enrollment import Enrollment

# router = APIRouter()


# @router.get("/{student_id}/data")
# async def get_id_card_data(
#     student_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get student data for ID card generation.
#     Students can only access their own data.
#     """
#     # Authorization check
#     if not (
#         current_user.is_admin or 
#         current_user.is_tutor or 
#         str(current_user.id) == str(student_id)
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to access this student's data"
#         )
    
#     try:
#         # Get student
#         student = db.query(User).filter(User.id == student_id).first()
#         if not student:
#             raise HTTPException(404, "Student not found")
        
#         # Check if user has student role
#         if not student.has_role('student'):
#             raise HTTPException(403, "User is not a student")
        
#         # Get enrollments with course details
#         enrollments = db.query(Enrollment).filter(
#             Enrollment.student_id == student_id
#         ).all()
        
#         courses = []
#         for enrollment in enrollments:
#             course = enrollment.course
#             courses.append({
#                 "id": str(course.id),
#                 "title": course.title,
#                 "code": course.code,
#                 "enrolled_date": enrollment.created_at.isoformat() if enrollment.created_at else None
#             })
        
#         return {
#             "student": {
#                 "id": str(student.id),
#                 "names": student.names if student.names else student.username,
#                 "email": student.email,
#                 "student_id": student.username if student.username else str(student.id)[:8].upper(),
#                 "phone": student.phone if hasattr(student, 'phone') else None,
#                 "date_of_birth": student.date_of_birth if hasattr(student, 'date_of_birth') else None,
#                 "profile_picture": student.avatar_url if hasattr(student, 'avatar_url') else None
#             },
#             "courses": courses
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in get_id_card_data: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching ID card data: {str(e)}"
#         )


@router.post("/{student_id}/upload-photo")
async def upload_id_photo(
    student_id: UUID,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload/update student photo for ID card.
    Processes image, resizes it, and returns base64 encoded data.
    """
    # Authorization check
    if str(current_user.id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload your own photo"
        )
    
    try:
        # Validate file type
        if not photo.content_type or not photo.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Read file contents
        contents = await photo.read()
        
        # Validate file size (max 2MB)
        if len(contents) > 2 * 1024 * 1024:
            raise HTTPException(400, "Photo must be less than 2MB")
        
        # Process image
        image = Image.open(BytesIO(contents))
        
        # Resize to standard size (passport photo dimensions)
        max_size = (600, 600)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Save to BytesIO
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Convert to base64
        photo_base64 = base64.b64encode(output.read()).decode('utf-8')
        photo_data = f"data:image/jpeg;base64,{photo_base64}"
        
        # Optionally update student record
        # student = db.query(User).filter(User.id == student_id).first()
        # if student and hasattr(student, 'avatar_url'):
        #     student.avatar_url = photo_data
        #     db.commit()
        
        return {
            "success": True,
            "photo_url": photo_data,
            "message": "Photo uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading photo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo: {str(e)}"
        )


@router.get("/{student_id}/generate-pdf")
async def generate_id_card_pdf(
    student_id: UUID,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate ID card data for PDF export (optional feature).
    Frontend handles rendering via html2canvas.
    """
    # Authorization check
    if str(current_user.id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only generate your own ID card"
        )
    
    try:
        # Get student
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(404, "Student not found")
        
        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id
        ).first()
        
        if not enrollment:
            raise HTTPException(404, "Enrollment not found")
        
        course = enrollment.course
        
        return {
            "student_name": student.names if student.names else student.username,
            "student_id": student.username if student.username else str(student.id)[:8].upper(),
            "email": student.email,
            "course_name": course.title,
            "course_code": course.code,
            "enrolled_date": enrollment.created_at.isoformat() if enrollment.created_at else None,
            "phone": student.phone if hasattr(student, 'phone') else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating ID card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating ID card: {str(e)}"
        )
