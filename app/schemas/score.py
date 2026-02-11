# from pydantic import BaseModel, ConfigDict
# from uuid import UUID

# class ScoreSubmit(BaseModel):
#     enrollment_id: UUID
#     assessment_id: UUID
#     score: float
#     graded_by: UUID

# class ScoreOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)  #  Pydantic V2
#     id: UUID
#     enrollment_id: UUID
#     assessment_id: UUID
#     score: float
#     graded_by: UUID


# # v2
# # ============================================================================
# # SCHEMAS - Part 6: Score Schemas
# # FILE: app/schemas/score.py
# # ============================================================================

# from pydantic import BaseModel, Field
# from uuid import UUID
# from datetime import datetime
# from typing import Dict, Optional

# class LessonScoreData(BaseModel):
#     assessment: float = Field(..., ge=0)
#     assignment: float = Field(..., ge=0)

# class LessonScoreCreate(BaseModel):
#     lesson_id: UUID
#     scores: Dict[str, LessonScoreData] = Field(..., description="Map of student_id to scores")
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "lesson_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
#                 "scores": {
#                     "student_uuid_1": {
#                         "assessment": 18,
#                         "assignment": 27
#                     },
#                     "student_uuid_2": {
#                         "assessment": 19,
#                         "assignment": 28
#                     }
#                 }
#             }
#         }

# class ModuleScoreCreate(BaseModel):
#     module_id: UUID
#     scores: Dict[str, float] = Field(..., description="Map of student_id to score")
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "module_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
#                 "scores": {
#                     "student_uuid_1": 45,
#                     "student_uuid_2": 48
#                 }
#             }
#         }

# class LessonScoreOut(BaseModel):
#     id: UUID
#     lesson_id: UUID
#     student_id: UUID
#     student_name: str
#     assessment_score: float
#     assignment_score: float
#     total_score: float
#     percentage: float
#     grade: str
#     created_at: datetime
#     updated_at: datetime
    
#     class Config:
#         from_attributes = True

# class ModuleScoreOut(BaseModel):
#     id: UUID
#     module_id: UUID
#     student_id: UUID
#     student_name: str
#     project_score: Optional[float] = None
#     exam_score: Optional[float] = None
#     created_at: datetime
#     updated_at: datetime
    
#     class Config:
#         from_attributes = True

# class StudentCourseScoresOut(BaseModel):
#     student_id: UUID
#     course_id: UUID
#     modules: list['ModulePerformanceOut'] = []
#     overall_percentage: float
#     overall_grade: str


# # v3# app/schemas/score.py
# from pydantic import BaseModel, Field, validator
# from uuid import UUID
# from datetime import datetime
# from typing import Dict, Optional, List, Any
# from enum import Enum

# class AssessmentType(str, Enum):
#     HOMEWORK = "homework"
#     CLASSWORK = "classwork"
#     ASSESSMENT = "assessment"
#     ASSIGNMENT = "assignment"
#     EXAM = "exam"
#     PROJECT = "project"
#     QUIZ = "quiz"
#     TEST = "test"

# # ============================================================================
# # COLUMN-ORIENTED SCHEMAS (for flexible scoring)
# # ============================================================================

# class ScoreColumnCreate(BaseModel):
#     """Schema for creating/updating a score column"""
#     type: AssessmentType = Field(..., description="Type of assessment")
#     title: str = Field(..., min_length=1, max_length=100)
#     max_score: float = Field(..., gt=0)
#     weight: float = Field(..., ge=0, le=1, default=1.0)
#     description: Optional[str] = None
#     order: int = Field(default=0, ge=0)
#     is_required: bool = Field(default=True)
#     is_active: bool = Field(default=True)
    
#     @validator('weight')
#     def validate_weight(cls, v):
#         if v < 0 or v > 1:
#             raise ValueError('Weight must be between 0 and 1')
#         return v

# class ScoreColumnOut(BaseModel):
#     """Output schema for score column"""
#     id: UUID
#     lesson_id: Optional[UUID] = None
#     module_id: Optional[UUID] = None
#     course_id: Optional[UUID] = None
#     scope: str
#     type: AssessmentType
#     title: str
#     description: Optional[str]
#     max_score: float
#     weight: float
#     order: int
#     is_required: bool
#     is_active: bool
#     created_at: datetime
#     updated_at: datetime
    
#     class Config:
#         from_attributes = True

# class ColumnScoreItem(BaseModel):
#     """Individual score for a specific column"""
#     column_id: UUID
#     score: float = Field(..., ge=0)
#     remarks: Optional[str] = Field(default="", max_length=500)

# class StudentColumnScores(BaseModel):
#     """All column scores for a student"""
#     student_id: UUID  # For backward compatibility
#     enrollment_id: Optional[UUID] = None  # Preferred
#     column_scores: List[ColumnScoreItem] = Field(..., min_items=1)
    
#     @validator('enrollment_id', always=True)
#     def ensure_enrollment_id(cls, v, values):
#         """Ensure we have either student_id or enrollment_id"""
#         if not v and 'student_id' in values:
#             return values['student_id']
#         return v

# class BulkColumnScoresCreate(BaseModel):
#     """Schema for bulk creating scores with columns"""
#     lesson_id: UUID
#     columns: List[ScoreColumnCreate]
#     scores: List[StudentColumnScores]
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "lesson_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
#                 "columns": [
#                     {
#                         "type": "homework",
#                         "title": "Homework",
#                         "max_score": 30,
#                         "weight": 0.3,
#                         "order": 0
#                     },
#                     {
#                         "type": "classwork",
#                         "title": "Classwork",
#                         "max_score": 20,
#                         "weight": 0.2,
#                         "order": 1
#                     }
#                 ],
#                 "scores": [
#                     {
#                         "enrollment_id": "16c80861-0e1d-423c-9c0e-b39abc835742",
#                         "column_scores": [
#                             {
#                                 "column_id": "cdd0f333-13d5-4cd0-a4f5-89923bd1daef",
#                                 "score": 25,
#                                 "remarks": "Good work"
#                             },
#                             {
#                                 "column_id": "b60fe517-e2c4-41a8-a632-cda97a87672d",
#                                 "score": 18,
#                                 "remarks": ""
#                             }
#                         ]
#                     }
#                 ]
#             }
#         }

# class BulkColumnScoresOut(BaseModel):
#     """Response for bulk scores creation"""
#     lesson_id: UUID
#     created: int
#     updated: int
#     total_processed: int
#     columns_configured: int

# # ============================================================================
# # LEGACY SCHEMAS (for backward compatibility)
# # ============================================================================

# class LessonScoreData(BaseModel):
#     """Legacy - simple score data"""
#     assessment: float = Field(..., ge=0)
#     assignment: float = Field(..., ge=0)

# class LessonScoreCreate(BaseModel):
#     """Legacy - simple bulk creation"""
#     lesson_id: UUID
#     max_score: float = Field(100, gt=0)
#     scores: List[Dict[str, Any]] = Field(..., description="List of score records")
    
#     @validator('scores')
#     def validate_scores(cls, v):
#         for score in v:
#             if 'enrollment_id' not in score and 'student_id' not in score:
#                 raise ValueError("Each score must have either enrollment_id or student_id")
#             if 'score' not in score:
#                 raise ValueError("Each score must have a score value")
#         return v

# class StudentScoreSummary(BaseModel):
#     """Output schema for student score summary"""
#     enrollment_id: UUID
#     student_id: UUID
#     names: str
#     email: str
#     username: Optional[str]
#     score: float
#     max_score: float
#     percentage: float
#     grade: str
#     remarks: Optional[str]
#     is_recorded: bool
#     recorded_at: Optional[datetime]
    
#     class Config:
#         from_attributes = True

# class LessonScoresOut(BaseModel):
#     """Output schema for lesson scores with students"""
#     lesson_id: UUID
#     lesson_title: str
#     total_students: int
#     recorded_count: int
#     max_score: float
#     students: List[StudentScoreSummary]
    
#     class Config:
#         from_attributes = True

# # ============================================================================
# # NEW OUTPUT SCHEMAS (for column-based responses)
# # ============================================================================

# class StudentColumnScoreDetail(BaseModel):
#     """Detail of student's score for a specific column"""
#     column_id: UUID
#     column_title: str
#     column_type: str
#     score: float
#     max_score: float
#     percentage: float
#     weight: float
#     remarks: str
#     is_recorded: bool

# class StudentColumnSummary(BaseModel):
#     """Student summary with all column scores"""
#     enrollment_id: UUID
#     student_id: UUID
#     names: str
#     email: str
#     username: Optional[str]
#     column_scores: Dict[str, StudentColumnScoreDetail]  # column_id -> detail
#     total_percentage: float
#     total_grade: str
    
#     class Config:
#         from_attributes = True

# class LessonColumnScoresOut(BaseModel):
#     """Full lesson scores with columns and student details"""
#     lesson: Dict[str, Any]
#     summary: Dict[str, Any]
#     columns: List[ScoreColumnOut]
#     students: List[StudentColumnSummary]
    
#     class Config:
#         from_attributes = True
        


# # v3
# # ============================================================================
# # FILE: app/schemas/score.py
# # Pydantic schemas for score operations
# # ============================================================================

# from pydantic import BaseModel, Field, field_validator
# from typing import List, Optional, Dict
# from uuid import UUID
# from datetime import datetime


# class ColumnScoreInput(BaseModel):
#     """Individual score for a specific column"""
#     column_id: str = Field(..., description="Score column ID")
#     score: float = Field(..., ge=0, description="Score value")
#     remarks: Optional[str] = Field("", max_length=500)


# class StudentScoreInput(BaseModel):
#     """Scores for one student across all columns"""
#     student_id: str = Field(..., description="Enrollment ID (not student.id)")
#     column_scores: List[ColumnScoreInput]


# class ColumnConfigInput(BaseModel):
#     """Column configuration"""
#     id: Optional[str] = None  # UUID for existing, None/temp for new
#     type: str = Field(..., description="Assessment type (homework, classwork, quiz, etc.)")
#     title: str = Field(..., min_length=1, max_length=200)
#     description: Optional[str] = Field(None, max_length=500)
#     max_score: float = Field(..., gt=0)
#     weight: float = Field(..., ge=0, le=1)
#     order: Optional[int] = Field(0, ge=0)


# class BulkScoreInput(BaseModel):
#     """Bulk score submission with column configuration"""
#     lesson_id: str
#     columns: List[ColumnConfigInput]
#     scores: List[StudentScoreInput]
    
#     @field_validator('columns')
#     @classmethod
#     def validate_columns(cls, v):
#         """Ensure columns have required fields"""
#         if not v or len(v) == 0:
#             raise ValueError("At least one column is required")
        
#         for col in v:
#             if not col.type or not col.title:
#                 raise ValueError("Each column must have 'type' and 'title'")
#             if col.max_score <= 0:
#                 raise ValueError("Each column must have a positive max_score")
#             if not (0 <= col.weight <= 1):
#                 raise ValueError("Each column weight must be between 0 and 1")
#         return v
    
#     @field_validator('scores')
#     @classmethod
#     def validate_scores(cls, v):
#         """Ensure scores have required fields"""
#         for score in v:
#             if not score.student_id:
#                 raise ValueError("Each score must have student_id (enrollment_id)")
#             if not score.column_scores:
#                 raise ValueError("Each student must have column_scores")
#         return v


# class ScoreOut(BaseModel):
#     """Individual score output"""
#     id: UUID
#     enrollment_id: UUID
#     column_id: UUID
#     score: float
#     max_score: float
#     percentage: float
#     grade: Optional[str]
#     notes: Optional[str]
#     recorded_date: datetime
#     recorder_id: UUID
    
#     class Config:
#         from_attributes = True





# v4
# app/schemas/score.py
# Fixed Pydantic schemas matching frontend structure

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class ColumnScoreItem(BaseModel):
    """Individual score for a column"""
    column_id: str
    score: float = Field(ge=0)
    remarks: str = ""


class StudentColumnScores(BaseModel):
    """All column scores for one student"""
    enrollment_id: Optional[str] = None  # Will be mapped from student_id if missing
    student_id: Optional[str] = None  # Fallback identifier
    column_scores: List[ColumnScoreItem]


class ScoreColumnConfig(BaseModel):
    """Score column configuration"""
    id: Optional[str] = None  # UUID for existing, temp ID for new
    type: str  # 'homework', 'classwork', 'quiz', etc.
    title: str
    description: Optional[str] = None
    max_score: float = Field(gt=0)
    weight: float = Field(ge=0, le=1)  # 0-1 decimal
    order: int = 0


class BulkScoreInput(BaseModel):
    """Bulk score submission payload"""
    lesson_id: str
    columns: List[ScoreColumnConfig]
    scores: List[StudentColumnScores]

    class Config:
        json_schema_extra = {
            "example": {
                "lesson_id": "123e4567-e89b-12d3-a456-426614174000",
                "columns": [
                    {
                        "id": "col-1",
                        "type": "homework",
                        "title": "Homework",
                        "max_score": 30,
                        "weight": 0.3,
                        "order": 1
                    }
                ],
                "scores": [
                    {
                        "enrollment_id": "enrollment-uuid",
                        "student_id": "student-uuid",
                        "column_scores": [
                            {
                                "column_id": "col-1",
                                "score": 25,
                                "remarks": "Good work"
                            }
                        ]
                    }
                ]
            }
        }


# ============================================================================
# SCHEMAS FOR MODULE AND COURSE
# ============================================================================

# class ColumnScoreItem(BaseModel):
#     column_id: str
#     score: float
#     remarks: str = ""


class StudentScores(BaseModel):
    enrollment_id: str | None = None
    student_id: str | None = None
    column_scores: List[ColumnScoreItem]


class ScoreColumnConfig(BaseModel):
    id: str | None = None
    type: str
    title: str
    max_score: float
    weight: float
    order: int = 0


class ModuleBulkScoreInput(BaseModel):
    module_id: str
    columns: List[ScoreColumnConfig]
    scores: List[StudentScores]


class CourseBulkScoreInput(BaseModel):
    course_id: str
    columns: List[ScoreColumnConfig]
    scores: List[StudentScores]

