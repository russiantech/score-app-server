# ============================================================================
# SCHEMAS - Part 9: Dashboard Schemas
# FILE: app/schemas/dashboard.py
# ============================================================================

from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class TutorCourseOverview(BaseModel):
    id: UUID
    name: str
    code: str
    modules_count: int
    lessons_count: int
    students_count: int

class TutorDashboardOut(BaseModel):
    tutor_id: UUID
    tutor_name: str
    total_courses: int
    total_students: int
    total_lessons: int
    courses: list[TutorCourseOverview]

class StudentCourseOverview(BaseModel):
    id: UUID
    name: str
    code: str
    progress: float
    grade: str
    tutor_name: Optional[str] = None

class StudentDashboardOut(BaseModel):
    student_id: UUID
    student_name: str
    student_id_number: str
    total_courses: int
    courses: list[StudentCourseOverview]

class ParentChildOverview(BaseModel):
    id: UUID
    name: str
    student_id: str
    enrolled_courses: int
    overall_progress: float
    average_grade: str

class ParentDashboardOut(BaseModel):
    parent_id: UUID
    parent_name: str
    total_children: int
    children: list[ParentChildOverview]

