# ============================================================================
# SCHEMAS - Part 7: Admin Schemas
# FILE: app/schemas/admin.py
# ============================================================================

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    total_courses: int
    total_modules: int
    total_lessons: int
    total_tutors: int
    total_students: int
    total_parents: int
    active_courses: int
    inactive_courses: int
    active_students: int
    active_tutors: int
    active_parents: int
    inactive_parents: int
    recent_enrollments: int
    total_enrollments: int
    total_assessments: int
    average_class_size: float
    courses_without_tutors: int
    students_without_parents: int

class RecentActivityOut(BaseModel):
    id: UUID
    type: str  # enrollment, course, user, assessment, attendance
    message: str
    timestamp: datetime
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class DashboardOverviewOut(BaseModel):
    stats: AdminStatsOut
    activities: list[RecentActivityOut]
    
