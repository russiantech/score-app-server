# from pydantic import BaseModel
# from uuid import UUID

# class ScoreEntry(BaseModel):
#     id: UUID
#     title: str
#     type: str
#     score: float | None
#     max_score: float

# class CoursePerformance(BaseModel):
#     course_id: UUID
#     course_title: str
#     assessments: list[ScoreEntry]
#     assignments: list[ScoreEntry]
#     summary: dict

# class StudentPerformanceResponse(BaseModel):
#     student_id: UUID
#     courses: list[CoursePerformance]


# v2
# ============================================================================
# SCHEMAS - Part 8: Performance Schemas
# FILE: app/schemas/performance.py
# ============================================================================

from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class LessonPerformanceOut(BaseModel):
    lesson_id: UUID
    lesson_name: str
    lesson_number: int
    lesson_date: str
    attended: bool
    assessment_score: Optional[float] = None
    assessment_max: float
    assignment_score: Optional[float] = None
    assignment_max: float
    total_score: Optional[float] = None
    total_max: float
    percentage: Optional[float] = None
    grade: Optional[str] = None

class ModulePerformanceOut(BaseModel):
    module_id: UUID
    module_name: str
    module_order: int
    lessons: list[LessonPerformanceOut] = []
    project_score: Optional[float] = None
    project_max: float = 50
    exam_score: Optional[float] = None
    exam_max: float = 100
    module_percentage: Optional[float] = None
    module_grade: Optional[str] = None

class CoursePerformanceOut(BaseModel):
    course_id: UUID
    course_name: str
    course_code: str
    tutor_name: Optional[str] = None
    progress: float
    modules: list[ModulePerformanceOut] = []
    overall_percentage: float
    overall_grade: str
    total_attendance: int
    total_lessons: int
    attendance_percentage: float

