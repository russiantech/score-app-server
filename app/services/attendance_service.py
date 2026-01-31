# # app/services/attendance_service.py
# # Fixed attendance service with proper enrollment_id mapping

# from typing import Optional, List, Dict, Any
# from uuid import UUID
# from datetime import date
# from fastapi import HTTPException, status
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import and_

# from app.models.attendance import Attendance, AttendanceStatus
# from app.models.user import User
# from app.models.enrollment import Enrollment
# from app.models.lesson import Lesson
# from app.models.course import Course
# from app.models.modules import Module


# def get_lesson_attendance_with_students(
#     db: Session,
#     lesson_id: UUID
# ) -> Dict[str, Any]:
#     """
#     Get attendance for a lesson with ALL enrolled students.
#     Includes students without recorded attendance.
#     """
#     # Fetch lesson + module
#     lesson = (
#         db.query(Lesson)
#         .options(joinedload(Lesson.module))
#         .filter(Lesson.id == lesson_id)
#         .first()
#     )

#     if not lesson:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Lesson not found"
#         )

#     module = lesson.module
#     if not module:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Module not found"
#         )

#     # Fetch enrollments
#     enrollments = (
#         db.query(Enrollment)
#         .options(joinedload(Enrollment.student))
#         .filter(
#             Enrollment.course_id == module.course_id,
#         )
#         .all()
#     )

#     # Existing attendance records
#     existing_attendance = (
#         db.query(Attendance)
#         .filter(Attendance.lesson_id == lesson_id)
#         .all()
#     )

#     attendance_map = {
#         att.enrollment_id: att for att in existing_attendance
#     }

#     students_data = []
#     recorded_count = 0

#     for enrollment in enrollments:
#         attendance = attendance_map.get(enrollment.id)
#         is_recorded = attendance is not None

#         if is_recorded:
#             recorded_count += 1

#         students_data.append({
#             "enrollment_id": str(enrollment.id),
#             "student_id": str(enrollment.student.id),
#             "names": enrollment.student.names,
#             "email": enrollment.student.email,
#             "username": enrollment.student.username,
#             "status": attendance.status.value if attendance else None,
#             "remarks": attendance.notes if attendance else "",
#             "date": str(attendance.date) if attendance else None,
#             "attendance_id": str(attendance.id) if attendance else None,
#             "is_recorded": is_recorded,
#         })

#     return {
#         "lesson": {
#             "id": str(lesson.id),
#             "title": lesson.title,
#             "module_id": str(module.id),
#             "course_id": str(module.course_id),
#         },
#         "summary": {
#             "total_students": len(students_data),
#             "recorded_count": recorded_count,
#         },
#         "students": students_data,
#     }


# def bulk_create_or_update_attendance(
#     db: Session,
#     lesson_id: UUID,
#     attendance_data: List[Dict[str, Any]],
#     current_user: User
# ) -> Dict[str, Any]:
#     """
#     Create or update attendance records for multiple students.
#     Properly handles enrollment_id mapping from student_id.
#     """
#     # Permission check
#     if not (current_user.is_tutor or current_user.is_admin):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only tutors and admins can record attendance"
#         )
    
#     # Verify lesson exists
#     lesson = db.query(Lesson).options(
#         joinedload(Lesson.module)
#     ).filter(Lesson.id == lesson_id).first()
    
#     if not lesson:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Lesson not found"
#         )
    
#     # For tutors: verify they teach this course
#     if current_user.is_tutor and not current_user.is_admin:
#         # Check if tutor teaches this course
#         course = db.query(Course).filter(Course.id == lesson.module.course_id).first()
#         if course and current_user not in course.tutors:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to record attendance for this course"
#             )
    
#     created = 0
#     updated = 0
#     errors = []
#     today = date.today()
    
#     for record in attendance_data:
#         # Get enrollment_id (prioritize enrollment_id, fallback to student_id)
#         enrollment_id = record.get("enrollment_id")
        
#         if not enrollment_id:
#             # Map from student_id to enrollment_id
#             student_id = record.get("student_id")
#             if not student_id:
#                 errors.append("Missing both enrollment_id and student_id")
#                 continue
            
#             try:
#                 student_uuid = UUID(student_id)
#                 enrollment = db.query(Enrollment).filter(
#                     Enrollment.student_id == student_uuid,
#                     Enrollment.course_id == lesson.module.course_id
#                 ).first()
                
#                 if enrollment:
#                     enrollment_id = str(enrollment.id)
#                 else:
#                     errors.append(f"No enrollment found for student {student_id}")
#                     continue
#             except (ValueError, AttributeError) as e:
#                 errors.append(f"Invalid student_id: {student_id}")
#                 continue
        
#         try:
#             enrollment_uuid = UUID(enrollment_id)
#         except ValueError:
#             errors.append(f"Invalid enrollment_id: {enrollment_id}")
#             continue
        
#         status_value = record.get("status", "present")
#         remarks = record.get("remarks", "")
        
#         # Validate status
#         try:
#             attendance_status = AttendanceStatus(status_value.lower())
#         except ValueError:
#             errors.append(f"Invalid status: {status_value}")
#             continue
        
#         # Check if attendance already exists
#         existing = db.query(Attendance).filter(
#             and_(
#                 Attendance.enrollment_id == enrollment_uuid,
#                 Attendance.lesson_id == lesson_id
#             )
#         ).first()
        
#         if existing:
#             # Update existing record
#             existing.status = attendance_status
#             existing.notes = remarks
#             existing.date = today
#             existing.recorded_by = current_user.id
#             updated += 1
#         else:
#             # Create new record
#             attendance = Attendance(
#                 enrollment_id=enrollment_uuid,
#                 lesson_id=lesson_id,
#                 student_id=enrollment_uuid,  # Will be set via enrollment
#                 recorded_by=current_user.id,
#                 status=attendance_status,
#                 notes=remarks,
#                 date=today
#             )
#             db.add(attendance)
#             created += 1
    
#     db.commit()
    
#     result = {
#         "lesson_id": str(lesson_id),
#         "created": created,
#         "updated": updated,
#         "total_processed": created + updated
#     }
    
#     if errors:
#         result["errors"] = errors
    
#     return result


# # ============================================================================
# # LEGACY FUNCTIONS (keep for backward compatibility)
# # ============================================================================

# def get_lesson_attendance(
#     db: Session,
#     lesson_id: UUID
# ) -> List[Attendance]:
#     """Get all attendance records for a lesson (legacy)"""
#     return db.query(Attendance).options(
#         joinedload(Attendance.enrollment).joinedload(Enrollment.student),
#         joinedload(Attendance.lesson),
#     ).filter(
#         Attendance.lesson_id == lesson_id
#     ).all()


# def record_bulk_attendance(
#     db: Session,
#     data: Dict[str, Any],
#     current_user: User
# ) -> Dict[str, Any]:
#     """Record attendance for multiple students in a lesson (legacy route)"""
#     lesson_id = data.get("lesson_id")
#     attendance_dict = data.get("attendance", {})
    
#     if not lesson_id or not attendance_dict:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid data format"
#         )
    
#     # Verify lesson exists
#     lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
#     if not lesson:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Lesson not found"
#         )
    
#     # For tutors: verify they teach this course
#     if current_user.is_tutor and not current_user.is_admin:
#         course = db.query(Course).filter(Course.id == lesson.module.course_id).first()
#         if course and current_user not in course.tutors:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to record attendance for this course"
#             )
    
#     recorded = []
#     today = date.today()
    
#     for student_id_str, is_present in attendance_dict.items():
#         try:
#             student_id = UUID(student_id_str)
#         except ValueError:
#             continue
        
#         # Find enrollment for this student in the course
#         enrollment = db.query(Enrollment).filter(
#             Enrollment.student_id == student_id,
#             Enrollment.course_id == lesson.module.course_id
#         ).first()
        
#         if not enrollment:
#             continue
        
#         # Check if attendance already exists
#         existing = db.query(Attendance).filter(
#             and_(
#                 Attendance.enrollment_id == enrollment.id,
#                 Attendance.lesson_id == lesson_id,
#                 Attendance.date == today
#             )
#         ).first()
        
#         if existing:
#             # Update existing
#             existing.status = AttendanceStatus.PRESENT if is_present else AttendanceStatus.ABSENT
#             recorded.append(existing)
#         else:
#             # Create new
#             attendance = Attendance(
#                 lesson_id=lesson_id,
#                 enrollment_id=enrollment.id,
#                 student_id=student_id,
#                 recorded_by=current_user.id,
#                 status=AttendanceStatus.PRESENT if is_present else AttendanceStatus.ABSENT,
#                 date=today
#             )
#             db.add(attendance)
#             recorded.append(attendance)
    
#     db.commit()
#     for record in recorded:
#         db.refresh(record)
    
#     return {
#         "lesson_id": lesson_id,
#         "total_recorded": len(recorded),
#         "present_count": sum(1 for a in recorded if a.status == AttendanceStatus.PRESENT)
#     }


# def get_student_course_attendance(
#     db: Session,
#     student_id: UUID,
#     course_id: UUID
# ) -> List[Attendance]:
#     """Get student's attendance for all lessons in a course"""
#     # Get all lessons in the course through modules
#     lessons = db.query(Lesson).join(Module).filter(
#         Module.course_id == course_id
#     ).all()
    
#     lesson_ids = [lesson.id for lesson in lessons]
    
#     if not lesson_ids:
#         return []
    
#     # Get the enrollment for this student in the course
#     enrollment = db.query(Enrollment).filter(
#         Enrollment.student_id == student_id,
#         Enrollment.course_id == course_id
#     ).first()
    
#     if not enrollment:
#         return []
    
#     return db.query(Attendance).options(
#         joinedload(Attendance.lesson),
#     ).filter(
#         Attendance.enrollment_id == enrollment.id,
#         Attendance.lesson_id.in_(lesson_ids)
#     ).all()



# v2
# app/services/attendance_service.py
# Fixed attendance service with proper enrollment_id mapping

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.modules import Module


def get_lesson_attendance_with_students(
    db: Session,
    lesson_id: UUID
) -> Dict[str, Any]:
    """
    Get attendance for a lesson with ALL enrolled students.
    Includes students without recorded attendance.
    """
    # Fetch lesson + module
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.module))
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    module = lesson.module
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # Fetch enrollments
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.student))
        .filter(
            Enrollment.course_id == module.course_id,
        )
        .all()
    )

    # Existing attendance records
    existing_attendance = (
        db.query(Attendance)
        .filter(Attendance.lesson_id == lesson_id)
        .all()
    )

    attendance_map = {
        att.enrollment_id: att for att in existing_attendance
    }

    students_data = []
    recorded_count = 0

    for enrollment in enrollments:
        attendance = attendance_map.get(enrollment.id)
        is_recorded = attendance is not None

        if is_recorded:
            recorded_count += 1

        students_data.append({
            "enrollment_id": str(enrollment.id),
            "student_id": str(enrollment.student.id),
            "names": enrollment.student.names,
            "email": enrollment.student.email,
            "username": enrollment.student.username,
            "status": attendance.status.value if attendance else None,
            "remarks": attendance.notes if attendance else "",
            "date": str(attendance.date) if attendance else None,
            "attendance_id": str(attendance.id) if attendance else None,
            "is_recorded": is_recorded,
        })

    return {
        "lesson": {
            "id": str(lesson.id),
            "title": lesson.title,
            "module_id": str(module.id),
            "course_id": str(module.course_id),
        },
        "summary": {
            "total_students": len(students_data),
            "recorded_count": recorded_count,
        },
        "students": students_data,
    }


def bulk_create_or_update_attendance(
    db: Session,
    lesson_id: UUID,
    attendance_data: List[Dict[str, Any]],
    current_user: User
) -> Dict[str, Any]:
    """
    Create or update attendance records for multiple students.
    Properly handles enrollment_id mapping from student_id.
    """
    # Permission check
    if not (current_user.is_tutor or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors and admins can record attendance"
        )
    
    # Verify lesson exists
    lesson = db.query(Lesson).options(
        joinedload(Lesson.module)
    ).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # For tutors: verify they teach this course, 
    
    # This does not work properly:
    # if current_user.is_tutor and not current_user.is_admin:
    #     # Check if tutor teaches this course
    #     course = db.query(Course).filter(Course.id == lesson.module.course_id).first()
    #     if course and current_user not in course.tutors_assigned:
    #         raise HTTPException(
    #             status_code=status.HTTP_403_FORBIDDEN,
    #             detail=f"Not authorized to record attendance for this course {course.tutors_assigned}"
    #         )
    
    # This also works fine:
    # Even Better (More Efficient — No Python Object Compare)
    # Avoid object comparison — check by query:

    """ from app.models.tutors import CourseTutor, CourseTutorStatus

    if current_user.is_tutor and not current_user.is_admin:

        is_assigned = db.query(CourseTutor).filter(
            CourseTutor.course_id == lesson.module.course_id,
            CourseTutor.tutor_id == current_user.id,
            CourseTutor.status == CourseTutorStatus.ACTIVE
        ).first()

        if not is_assigned:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to record attendance for this course"
            ) """

    # For tutors: verify they teach this course
    if current_user.is_tutor and not current_user.is_admin:

        course = db.query(Course).filter(
            Course.id == lesson.module.course_id
        ).first()

        if not course:
            raise HTTPException(404, "Course not found")

        if course not in current_user.my_assigned_courses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to record attendance for this course"
            )
    
    created = 0
    updated = 0
    errors = []
    today = date.today()
    
    for record in attendance_data:
        # Get enrollment_id (prioritize enrollment_id, fallback to student_id)
        enrollment_id = record.get("enrollment_id")
        
        if not enrollment_id:
            # Map from student_id to enrollment_id
            student_id = record.get("student_id")
            if not student_id:
                errors.append("Missing both enrollment_id and student_id")
                continue
            
            try:
                student_uuid = UUID(student_id)
                enrollment = db.query(Enrollment).filter(
                    Enrollment.student_id == student_uuid,
                    Enrollment.course_id == lesson.module.course_id
                ).first()
                
                if enrollment:
                    enrollment_id = str(enrollment.id)
                else:
                    errors.append(f"No enrollment found for student {student_id}")
                    continue
            except (ValueError, AttributeError) as e:
                errors.append(f"Invalid student_id: {student_id}")
                continue
        
        try:
            enrollment_uuid = UUID(enrollment_id)
        except ValueError:
            errors.append(f"Invalid enrollment_id: {enrollment_id}")
            continue
        
        status_value = record.get("status", "present")
        remarks = record.get("remarks", "")
        
        # Validate status
        try:
            attendance_status = AttendanceStatus(status_value.lower())
        except ValueError:
            errors.append(f"Invalid status: {status_value}")
            continue
        
        # Check if attendance already exists
        existing = db.query(Attendance).filter(
            and_(
                Attendance.enrollment_id == enrollment_uuid,
                Attendance.lesson_id == lesson_id
            )
        ).first()
        
        # Get the actual student_id from the enrollment
        enrollment_record = db.query(Enrollment).filter(
            Enrollment.id == enrollment_uuid
        ).first()
        
        if not enrollment_record:
            errors.append(f"Enrollment not found: {enrollment_uuid}")
            continue
        
        actual_student_id = enrollment_record.student_id
        
        if existing:
            # Update existing record
            existing.status = attendance_status
            existing.notes = remarks
            existing.date = today
            existing.recorded_by = current_user.id
            updated += 1
        else:
            # Create new record
            attendance = Attendance(
                enrollment_id=enrollment_uuid,
                lesson_id=lesson_id,
                student_id=actual_student_id,  # Use actual student_id from enrollment
                recorded_by=current_user.id,
                status=attendance_status,
                notes=remarks,
                date=today
            )
            db.add(attendance)
            created += 1
    
    db.commit()
    
    result = {
        "lesson_id": str(lesson_id),
        "created": created,
        "updated": updated,
        "total_processed": created + updated
    }
    
    if errors:
        result["errors"] = errors
    
    return result


# ============================================================================
# LEGACY FUNCTIONS (keep for backward compatibility)
# ============================================================================

def get_lesson_attendance(
    db: Session,
    lesson_id: UUID
) -> List[Attendance]:
    """Get all attendance records for a lesson (legacy)"""
    return db.query(Attendance).options(
        joinedload(Attendance.enrollment).joinedload(Enrollment.student),
        joinedload(Attendance.lesson),
    ).filter(
        Attendance.lesson_id == lesson_id
    ).all()


def record_bulk_attendance(
    db: Session,
    data: Dict[str, Any],
    current_user: User
) -> Dict[str, Any]:
    """Record attendance for multiple students in a lesson (legacy route)"""
    lesson_id = data.get("lesson_id")
    attendance_dict = data.get("attendance", {})
    
    if not lesson_id or not attendance_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data format"
        )
    
    # Verify lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # For tutors: verify they teach this course
    if current_user.is_tutor and not current_user.is_admin:
        course = db.query(Course).filter(Course.id == lesson.module.course_id).first()
        if course and current_user not in course.tutors:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to record attendance for this course"
            )
    
    recorded = []
    today = date.today()
    
    for student_id_str, is_present in attendance_dict.items():
        try:
            student_id = UUID(student_id_str)
        except ValueError:
            continue
        
        # Find enrollment for this student in the course
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == lesson.module.course_id
        ).first()
        
        if not enrollment:
            continue
        
        # Check if attendance already exists
        existing = db.query(Attendance).filter(
            and_(
                Attendance.enrollment_id == enrollment.id,
                Attendance.lesson_id == lesson_id,
                Attendance.date == today
            )
        ).first()
        
        if existing:
            # Update existing
            existing.status = AttendanceStatus.PRESENT if is_present else AttendanceStatus.ABSENT
            recorded.append(existing)
        else:
            # Create new
            attendance = Attendance(
                lesson_id=lesson_id,
                enrollment_id=enrollment.id,
                student_id=student_id,
                recorded_by=current_user.id,
                status=AttendanceStatus.PRESENT if is_present else AttendanceStatus.ABSENT,
                date=today
            )
            db.add(attendance)
            recorded.append(attendance)
    
    db.commit()
    for record in recorded:
        db.refresh(record)
    
    return {
        "lesson_id": lesson_id,
        "total_recorded": len(recorded),
        "present_count": sum(1 for a in recorded if a.status == AttendanceStatus.PRESENT)
    }


def get_student_course_attendance(
    db: Session,
    student_id: UUID,
    course_id: UUID
) -> List[Attendance]:
    """Get student's attendance for all lessons in a course"""
    # Get all lessons in the course through modules
    lessons = db.query(Lesson).join(Module).filter(
        Module.course_id == course_id
    ).all()
    
    lesson_ids = [lesson.id for lesson in lessons]
    
    if not lesson_ids:
        return []
    
    # Get the enrollment for this student in the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        return []
    
    return db.query(Attendance).options(
        joinedload(Attendance.lesson),
    ).filter(
        Attendance.enrollment_id == enrollment.id,
        Attendance.lesson_id.in_(lesson_ids)
    ).all()

