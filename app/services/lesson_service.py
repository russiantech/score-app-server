from typing import Optional, List, Tuple
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from fastapi import HTTPException, status
from app.models.lesson import Lesson
from app.models.modules import Module
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonFilters, LessonUpdate, LessonStatus
from app.models.tutors import CourseTutor, CourseTutorStatus

def update_lesson_status(lesson: Lesson):
    """
    Auto-update lesson status based on date and attendance/score completion.
    """
    today = date.today()

    if lesson.date and lesson.date > today:
        lesson.status = LessonStatus.UPCOMING
    elif getattr(lesson, 'attendance_count', 0) and getattr(lesson, 'present_count', 0) >= lesson.attendance_count:
        lesson.status = LessonStatus.COMPLETED
    else:
        lesson.status = LessonStatus.ONGOING


def create_lesson(db: Session, data: LessonCreate, user_id: UUID) -> Lesson:
    """Create a new lesson with permission check"""

    module = db.query(Module).options(joinedload(Module.course)).filter(Module.id == data.module_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")

    # if not user.has_role('admin') and not (user.has_role('tutor') and user in module.course.tutors_assigned):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create lessons")

    # from app.models.tutors import CourseTutor, CourseTutorStatus # imported above already

    if not user.has_role('admin'):

        is_assigned = db.query(CourseTutor).filter(
            CourseTutor.course_id == module.course_id,
            CourseTutor.tutor_id == user.id,
            # CourseTutor.status == CourseTutorStatus.ACTIVE
        ).first()

        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create lessons for this course"
            )

    # Check duplicate order
    existing = db.query(Lesson).filter(Lesson.module_id == data.module_id, Lesson.order == data.order).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lesson order {data.order} already exists")

    lesson = Lesson(**data.model_dump())

    try:
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create lesson: {str(e)}")


def update_lesson(db: Session, lesson_id: UUID, data: LessonUpdate, user_id: UUID, check_permission: bool = True) -> Lesson:
    """Update a lesson with partial update support"""
    # print(data)
    lesson = db.query(Lesson).options(joinedload(Lesson.module).joinedload(Module.course)).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    if check_permission:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
        
        # if not user.has_role('admin') and not (user.has_role('tutor') and user in lesson.module.course.tutors_assigned):
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this lesson")

        if not user.has_role('admin'):

            is_assigned = db.query(CourseTutor).filter(
                CourseTutor.course_id == lesson.module.course_id,
                CourseTutor.tutor_id == user.id,
                CourseTutor.status == CourseTutorStatus.ACTIVE
            ).first()

            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this lesson"
                )

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")

    if 'order' in update_data:
        existing = db.query(Lesson).filter(
            Lesson.module_id == lesson.module_id,
            Lesson.order == update_data['order'],
            Lesson.id != lesson_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lesson order {update_data['order']} already exists")

    for field, value in update_data.items():
        setattr(lesson, field, value)

    try:
        db.commit()
        db.refresh(lesson)
        return lesson
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update lesson: {str(e)}")


def delete_lesson(db: Session, lesson_id: UUID) -> None:
    lesson = get_lesson(db, lesson_id)
    db.delete(lesson)
    db.commit()


def get_lesson(db: Session, lesson_id: UUID) -> Lesson:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


def list_lessons(db: Session, filters: LessonFilters) -> Tuple[List[Lesson], int]:
    query = db.query(Lesson).filter(Lesson.course_id == filters.course_id).order_by(Lesson.order)
    total = query.count()
    lessons = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size).all()
    return lessons, total


def list_module_lessons(db: Session, module_id: UUID) -> List[Lesson]:
    return db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order).all()

