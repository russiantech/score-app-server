from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"
    refunded = "refunded"

# Payment Status Enum
class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    canceled = "canceled"

# # app/db/enums.py
# from sqlalchemy import Enum
# AssessmentTypeEnum = Enum(
#     'HOMEWORK',
#     'CLASSWORK',
#     'QUIZ',
#     'TEST',
#     'EXAM',
#     'PROJECT',
#     'PARTICIPATION',
#     'OTHER',
#     name='assessmenttype'
# )

# v2

from enum import Enum

class LessonStatus(str, Enum):
    COMPLETED = "completed"
    ONGOING = "ongoing"
    UPCOMING = "upcoming"
    CANCELLED = "cancelled"

# ============================================================================
# STANDARDIZED SCORING HIERARCHY & AsSESSMENT TYPES
# ============================================================================

import enum

class AssessmentType(str, enum.Enum):
    """Standardized assessment types with clear hierarchy"""
    
    # LESSON LEVEL (Required - Always created)
    HOMEWORK = "homework"        # Required for every lesson
    CLASSWORK = "classwork"      # Required for every lesson
    
    # LESSON LEVEL (Optional)
    QUIZ = "quiz"                # Optional per lesson
    TEST = "test"                # Optional per lesson
    
    # MODULE LEVEL (Standard)
    EXAM = "exam"                # Standard for modules (midterm/final)
    
    # COURSE LEVEL (Standard)
    PROJECT = "project"          # Standard for courses
    
    # SUPPLEMENTARY
    PARTICIPATION = "participation"
    OTHER = "other"


class AssessmentScope(str, enum.Enum):
    """Defines where assessments are recorded"""
    LESSON = "lesson"
    MODULE = "module"
    COURSE = "course"


# ============================================================================
# STANDARD CONFIGURATIONS
# ============================================================================

STANDARD_LESSON_ASSESSMENTS = [
    {
        "type": AssessmentType.HOMEWORK,
        "title": "Homework",
        "max_score": 30.0,
        "weight": 0.3,
        "required": True,
        "order": 1
    },
    {
        "type": AssessmentType.CLASSWORK,
        "title": "Classwork",
        "max_score": 20.0,
        "weight": 0.2,
        "required": True,
        "order": 2
    },
    {
        "type": AssessmentType.QUIZ,
        "title": "Quiz",
        "max_score": 50.0,
        "weight": 0.5,
        "required": False,  # Optional, created on demand
        "order": 3
    }
]

STANDARD_MODULE_ASSESSMENTS = [
    {
        "type": AssessmentType.EXAM,
        "title": "Module Exam",
        "max_score": 100.0,
        "weight": 1.0,
        "required": True,
        "order": 1
    }
]

STANDARD_COURSE_ASSESSMENTS = [
    {
        "type": AssessmentType.PROJECT,
        "title": "Course Project",
        "max_score": 100.0,
        "weight": 1.0,
        "required": True,
        "order": 1
    }
]



""" 
Usage Example:
# Then reuse everywhere:

from app.db.enums import AssessmentTypeEnum
assessment_type = Column(
    AssessmentTypeEnum,
    nullable=False
)

"""