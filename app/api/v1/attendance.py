# app/api/routes/attendance.py
# Fixed attendance routes with proper schema handling

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.deps.users import get_db, get_current_user, tutor_required
from app.services import attendance_service
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceOut,
)
from app.utils.responses import api_response

router = APIRouter()


@router.get("/{lesson_id}/lesson")
def get_lesson_attendance_with_students_endpoint(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get attendance for a lesson with ALL enrolled students.
    Returns both marked and unmarked students.
    """
    try:
        data = attendance_service.get_lesson_attendance_with_students(db, lesson_id)
        return api_response(
            success=True,
            message="Lesson attendance fetched successfully",
            data=data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/bulk", status_code=201)
def bulk_create_attendance_endpoint(
    payload: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Create or update attendance records in bulk.
    
    Payload structure:
    {
        "lesson_id": "lesson-uuid",
        "attendances": [
            {
                "student_id": "student-uuid",
                "status": "present",
                "remarks": ""
            }
        ]
    }
    """
    try:
        lesson_id = UUID(payload.lesson_id)
        
        # Convert Pydantic models to dicts
        attendance_data = [record.model_dump() for record in payload.attendances]
        
        result = attendance_service.bulk_create_or_update_attendance(
            db=db,
            lesson_id=lesson_id,
            attendance_data=attendance_data,
            current_user=current_user
        )
        
        return api_response(
            success=True,
            message="Attendance saved successfully",
            data=result,
            status_code=201
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save attendance: {str(e)}"
        )


# ============================================================================
# LEGACY ROUTES (keep for backward compatibility)
# ============================================================================

@router.get("/{lesson_id}")
def get_lesson_attendance_legacy(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all attendance records for a lesson (legacy)"""
    attendance = attendance_service.get_lesson_attendance(db, lesson_id)
    return api_response(
        success=True,
        message="Attendance records retrieved",
        data=attendance
    )


@router.get("/student/{student_id}/course/{course_id}")
def get_student_course_attendance_endpoint(
    student_id: UUID,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get student's attendance for all lessons in a course"""
    attendance = attendance_service.get_student_course_attendance(
        db, student_id, course_id
    )
    return api_response(
        success=True,
        message="Student attendance retrieved",
        data=attendance
    )

