
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from fastapi import HTTPException, status
from typing import List, Dict, Any

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.modules import Module
from app.models.user import User
from app.models.tutors import CourseTutor, CourseTutorStatus
# from app.models.tutor_assignment import CourseTutor, CourseTutorStatus


def get_dashboard(db: Session, tutor_id: UUID) -> Dict[str, Any]:
    """
    Get tutor dashboard data including courses, students, and lessons.
    """
    # Get tutor
    tutor = db.query(User).filter(User.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found"
        )
    
    # Check if user has tutor role
    if not tutor.has_role('tutor'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a tutor"
        )
    
    # Get active assignments for this tutor
    assignments = (
        db.query(CourseTutor)
        .options(joinedload(CourseTutor.course))
        .filter(CourseTutor.tutor_id == tutor_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .all()
    )
    
    # Extract courses from assignments
    courses = [assignment.course for assignment in assignments if assignment.course]
    
    total_students = 0
    total_lessons = 0
    course_data = []
    
    for course in courses:
        # Count enrolled students
        student_count = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course.id)
            .count()
        )
        total_students += student_count
        
        # Count lessons in this course
        lesson_count = (
            db.query(Lesson)
            .join(Module)
            .filter(Module.course_id == course.id)
            .count()
        )
        total_lessons += lesson_count
        
        course_data.append({
            "id": str(course.id),
            "title": course.title,
            "code": course.code,
            "description": course.description,
            "student_count": student_count,
            "lesson_count": lesson_count,
            "is_active": course.is_active,
        })
    
    return {
        "tutor_id": str(tutor_id),
        "tutor_name": tutor.names if tutor.names else tutor.username,
        "tutor_email": tutor.email,
        "total_courses": len(courses),
        "total_students": total_students,
        "total_lessons": total_lessons,
        "courses": course_data
    }


def get_tutor_courses(db: Session, tutor_id: UUID) -> List[Dict[str, Any]]:
    """
    Get courses assigned to a tutor through assignments.
    """
    # Verify tutor exists
    tutor = db.query(User).filter(User.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found"
        )
    
    # Get active assignments
    assignments = (
        db.query(CourseTutor)
        .options(joinedload(CourseTutor.course))
        .filter(CourseTutor.tutor_id == tutor_id)
        # .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .all()
    )
    
    courses = []
    for assignment in assignments:
        if assignment.course:
            course = assignment.course
            
            # Get student count
            student_count = (
                db.query(Enrollment)
                .filter(Enrollment.course_id == course.id)
                .count()
            )
            
            # Get lesson count
            lesson_count = (
                db.query(Lesson)
                .join(Module)
                .filter(Module.course_id == course.id)
                .count()
            )
            
            courses.append({
                "id": str(course.id),
                "title": course.title,
                "code": course.code,
                "description": course.description,
                "is_active": course.is_active,
                "enrolled_count": student_count,
                "lesson_count": lesson_count,
                "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                "assignment_notes": assignment.notes,
            })
    
    return courses


# def get_my_courses(db: Session, tutor_id: UUID) -> List[Dict[str, Any]]:
#     """
#     Get courses for the currently authenticated tutor.
#     This is a convenience method that calls get_tutor_courses.
#     """
#     return get_tutor_courses(db, tutor_id)


def get_course_students(
    db: Session,
    course_id: UUID,
    tutor_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get students enrolled in a course.
    Verifies that the tutor has access to this course.
    """
    # Verify tutor exists
    tutor = db.query(User).filter(User.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found"
        )
    
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Verify tutor is assigned to this course
    assignment = (
        db.query(CourseTutor)
        .filter(CourseTutor.tutor_id == tutor_id)
        .filter(CourseTutor.course_id == course_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .first()
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course"
        )
    
    # Get enrollments with student details
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.student))
        .filter(Enrollment.course_id == course_id)
        .all()
    )
    
    students = []
    for enrollment in enrollments:
        if enrollment.student:
            students.append({
                "id": str(enrollment.student.id),
                "names": enrollment.student.names,
                "email": enrollment.student.email,
                "username": enrollment.student.username,
                "enrollment_id": str(enrollment.id),
                "enrollment_status": enrollment.status.value if hasattr(enrollment.status, 'value') else enrollment.status,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                "progress": getattr(enrollment, 'progress', 0),
            })
    
    return students


def get_tutor_workload(db: Session, tutor_id: UUID) -> Dict[str, Any]:
    """
    Get detailed workload information for a tutor.
    """
    # Verify tutor exists
    tutor = db.query(User).filter(User.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found"
        )
    
    # Get active assignments
    active_assignments = (
        db.query(CourseTutor)
        .options(joinedload(CourseTutor.course))
        .filter(CourseTutor.tutor_id == tutor_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .count()
    )
    
    # Get total students across all courses
    total_students = (
        db.query(Enrollment)
        .join(CourseTutor, Enrollment.course_id == CourseTutor.course_id)
        .filter(CourseTutor.tutor_id == tutor_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .distinct(Enrollment.student_id)
        .count()
    )
    
    # Get course details
    courses = get_tutor_courses(db, tutor_id)
    
    return {
        "tutor_id": str(tutor_id),
        "tutor_name": tutor.names,
        "active_courses": active_assignments,
        "total_students": total_students,
        "courses": courses
    }

