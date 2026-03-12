# v3
# ============================================================================
# SERVICES - Part 9: Student Service (CORRECTED)
# FILE: app/services/student_service.py
# ============================================================================

from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Dict, Any, List
from fastapi import HTTPException, status

from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.modules import Module
from app.models.lesson import Lesson
from app.models.scores import Score

def calculate_grade(percentage: float) -> str:
    """Calculate grade from percentage"""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"

def get_dashboard(db: Session, student_id: UUID) -> Dict[str, Any]:
    """Get student dashboard data"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if user has student role
    if not student.has_role('student'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student"
        )
    
    # Get parents (guardians)
    parents = student.parents
    
    # Get enrollments with courses
    enrollments = db.query(Enrollment).filter(
        Enrollment.student_id == student_id
    ).options(joinedload(Enrollment.course)).all()
    
    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Calculate progress and grade
        progress = calculate_course_progress(db, student_id, course.id)
        grade = calculate_course_grade(db, student_id, course.id)
        
        # Get tutor names
        tutor_names = [instructor.names or instructor.username 
                      for instructor in course.instructors]
        
        courses.append({
            "id": course.id,
            "title": course.title,
            "code": course.code,
            "description": course.description,
            "progress": progress,
            "grade": grade,
            "tutor_names": tutor_names if tutor_names else ["Not Assigned"],
            "enrollment_date": enrollment.created_at,
            "status": enrollment.status if hasattr(enrollment, 'status') else "active"
        })
    
    return {
        "student_id": student_id,
        "student_name": student.names if student.names else student.username,
        "student_email": student.email,
        "student_id_number": str(student_id)[:8].upper(),
        "parents": [
            {
                "id": parent.id,
                "name": parent.names if parent.names else parent.username,
                "email": parent.email,
                "phone": parent.phone,
                "relationship": get_parent_relationship(db, parent.id, student_id)
            }
            for parent in parents
        ],
        "total_courses": len(courses),
        "courses": courses
    }

def get_parent_relationship(db: Session, parent_id: UUID, student_id: UUID) -> str:
    """Get relationship type between parent and student"""
    from sqlalchemy import and_
    from app.models.association_tables import parent_students
    
    result = db.execute(
        parent_students.select().where(
            and_(
                parent_students.c.parent_id == parent_id,
                parent_students.c.student_id == student_id
            )
        )
    ).first()
    
    return result.relationship if result else "guardian"

def get_student_courses(db: Session, student_id: UUID) -> List[Course]:
    """Get student's enrolled courses"""
    enrollments = db.query(Enrollment).filter(
        Enrollment.student_id == student_id
    ).options(joinedload(Enrollment.course)).all()
    
    return [enrollment.course for enrollment in enrollments]

def get_course_performance(db: Session, student_id: UUID, course_id: UUID) -> Dict[str, Any]:
    """Get student's detailed performance in a course"""
    # Verify enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this course"
        )
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get modules with lessons
    modules = db.query(Module).filter(
        Module.course_id == course_id
    ).order_by(Module.order).all()
    
    module_performances = []
    
    for module in modules:
        lessons = db.query(Lesson).filter(
            Lesson.module_id == module.id
        ).order_by(Lesson.number).all()
        
        lesson_performances = []
        for lesson in lessons:
            # Get score for this lesson and student
            score = db.query(Score).filter(
                Score.lesson_id == lesson.id,
                Score.enrollment_id == enrollment.id
            ).first()
            
            lesson_performances.append({
                "lesson_id": str(lesson.id),
                "lesson_name": lesson.title,
                "number": lesson.number,
                "score": score.score if score else None,
                "max_score": score.max_score if score else None,
                "percentage": score.percentage if score else None,
                "grade": score.grade if score else None,
                "notes": score.notes if score else None
            })
        
        module_performances.append({
            "module_id": str(module.id),
            "module_name": module.name,
            "module_order": module.order,
            "lessons": lesson_performances
        })
    
    # Calculate overall course grade
    overall_grade = calculate_course_grade(db, student_id, course_id)
    
    return {
        "course_id": str(course_id),
        "course_name": course.title,
        "course_code": course.code,
        "course_description": course.description,
        "overall_grade": overall_grade,
        "overall_progress": calculate_course_progress(db, student_id, course_id),
        "modules": module_performances,
        "instructors": [
            {
                "id": str(instructor.id),
                "name": instructor.names or instructor.username,
                "email": instructor.email
            }
            for instructor in course.instructors
        ]
    }

def get_id_card_data(db: Session, student_id: UUID) -> Dict[str, Any]:
    """Get student ID card data"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if user is a student
    if not any(role.name == 'student' for role in student.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student"
        )
    
    return {
        "student_id": str(student_id),
        "student_name": student.names or student.username,
        "student_id_number": str(student_id)[:8].upper(),
        "email": student.email,
        "phone": student.phone,
        "enrolled_date": student.created_at.date() if student.created_at else None,
        "avatar_url": student.avatar_url,
        "is_active": student.is_active,
        "is_verified": student.is_verified
    }

def calculate_course_progress(db: Session, student_id: UUID, course_id: UUID) -> float:
    """Calculate student's progress in a course"""
    # Get enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        return 0.0
    
    # Get total lessons in course
    total_lessons = db.query(Lesson).join(Module).filter(
        Module.course_id == course_id
    ).count()
    
    if total_lessons == 0:
        return 0.0
    
    # Get completed lessons (where score exists)
    completed = db.query(Score).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        Score.enrollment_id == enrollment.id
    ).count()
    
    return round((completed / total_lessons) * 100, 1)

def calculate_course_grade(db: Session, student_id: UUID, course_id: UUID) -> str:
    """Calculate student's overall grade in a course"""
    # Get enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        return "N/A"
    
    # Get all scores for this enrollment
    scores = db.query(Score).filter(
        Score.enrollment_id == enrollment.id
    ).all()
    
    if not scores:
        return "N/A"
    
    # Calculate weighted average
    total_weighted_score = 0
    total_weight = 0
    
    for score in scores:
        weight = getattr(score, 'weight', 1.0)
        total_weighted_score += score.percentage * weight
        total_weight += weight
    
    if total_weight == 0:
        return "N/A"
    
    avg_percentage = total_weighted_score / total_weight
    return calculate_grade(avg_percentage)


# more--- v2

# ============================================================================
# SERVICES - ID Card Service
# FILE: app/services/id_card_service.py
# ============================================================================

from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Dict, Any, List
from fastapi import HTTPException, status
import base64
from io import BytesIO
from PIL import Image

from app.models.user import User
from app.models.enrollment import Enrollment


def get_student_id_card_data(db: Session, student_id: UUID) -> Dict[str, Any]:
    """
    Get student data and enrolled courses for ID card generation.
    """

    student = db.query(User).filter(User.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    if not student.has_role("student"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student"
        )

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .options(joinedload(Enrollment.course))
        .all()
    )

    courses = []

    for enrollment in enrollments:
        course = enrollment.course

        courses.append({
            "id": course.id,
            "title": course.title,
            "code": course.code,
            "enrolled_date": enrollment.created_at
        })

    return {
        "student": {
            "id": student.id,
            "names": student.names if student.names else student.username,
            "email": student.email,
            "student_id": student.username or str(student.id)[:8].upper(),
            "phone": student.phone,
            "date_of_birth": getattr(student, "date_of_birth", None),
            "profile_picture": getattr(student, "avatar_url", None)
        },
        "courses": courses
    }


def upload_student_photo(db: Session, student_id: UUID, image_bytes: bytes) -> Dict[str, Any]:
    """
    Upload and process student ID photo.
    """

    student = db.query(User).filter(User.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    if len(image_bytes) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo must be less than 2MB"
        )

    try:
        image = Image.open(BytesIO(image_bytes))

        max_size = (600, 600)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        output = BytesIO()
        image.save(output, format="JPEG", quality=85)
        output.seek(0)

        encoded = base64.b64encode(output.read()).decode("utf-8")
        photo_data = f"data:image/jpeg;base64,{encoded}"

        return {
            "photo_url": photo_data,
            "student_id": student_id
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process photo"
        )


def generate_student_id_card(
    db: Session,
    student_id: UUID,
    course_id: UUID
) -> Dict[str, Any]:
    """
    Generate ID card payload for rendering or PDF export.
    """

    student = db.query(User).filter(User.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).options(joinedload(Enrollment.course)).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    course = enrollment.course

    return {
        "student": {
            "name": student.names if student.names else student.username,
            "student_id": student.username or str(student.id)[:8].upper(),
            "email": student.email,
            "phone": student.phone
        },
        "course": {
            "id": course.id,
            "title": course.title,
            "code": course.code
        },
        
        "enrollment_date": enrollment.created_at
    }



