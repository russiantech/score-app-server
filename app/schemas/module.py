# ============================================================================
# SCHEMAS - Part 2: Course & Module Schemas
# FILE: app/schemas/module.py
# ============================================================================

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.schemas.course import CourseOut

class ModuleBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    order: int = Field(..., ge=1)
    description: Optional[str] = None

class ModuleCreate(ModuleBase):
    course_id: UUID

class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    order: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None

class ModuleOut(ModuleBase):
    id: UUID
    course_id: UUID
    lessons_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ModuleWithLessonsOut(ModuleOut):
    lessons: list['LessonOut'] = []
    


class CourseWithModulesOut(BaseModel):
    course: CourseOut
    modules: list[ModuleOut]
