# app/schemas/attendance.py
# Fixed attendance schemas to match frontend payload

import enum
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime, date
from typing import Dict, Optional, List

class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    HOLIDAY = "holiday"


class AttendanceRecordInput(BaseModel):
    """Individual attendance record for one student"""
    enrollment_id: Optional[str] = None  # Will be mapped from student_id if not provided
    student_id: Optional[str] = None     # Fallback identifier
    status: str = "present"
    remarks: str = ""

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ['present', 'absent', 'late', 'excused', 'holiday']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


class AttendanceBulkCreate(BaseModel):
    """Bulk attendance submission"""
    lesson_id: str
    attendances: List[AttendanceRecordInput]

    class Config:
        json_schema_extra = {
            "example": {
                "lesson_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "attendances": [
                    {
                        "student_id": "student-uuid-1",
                        "status": "present",
                        "remarks": ""
                    },
                    {
                        "student_id": "student-uuid-2",
                        "status": "absent",
                        "remarks": "Sick"
                    }
                ]
            }
        }


# Legacy schemas for backward compatibility
class AttendanceCreate(BaseModel):
    lesson_id: UUID
    student_id: UUID
    is_present: bool = True


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


class AttendanceOut(BaseModel):
    id: UUID
    lesson_id: UUID
    student_id: UUID
    student_name: str
    is_present: bool
    recorded_at: datetime
    
    class Config:
        from_attributes = True
    
