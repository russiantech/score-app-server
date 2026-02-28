"""
Lesson Service - Production Grade
Handles all lesson CRUD operations with proper error handling, 
logging, and enum serialization.

"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from fastapi import HTTPException, status
from app.models.lesson import Lesson
from app.models.modules import Module
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonFilters, LessonUpdate, LessonStatus
from app.models.tutors import CourseTutor, CourseTutorStatus

logger = logging.getLogger(__name__)


def update_lesson_status(lesson: Lesson) -> None:
    """
    Auto-update lesson status based on date and attendance completion.
    
    Business Rules:
    - Future lessons: UPCOMING
    - Completed attendance: COMPLETED  
    - Otherwise: ONGOING
    """
    today = date.today()

    if lesson.date and lesson.date > today:
        lesson.status = LessonStatus.UPCOMING
    elif (getattr(lesson, 'attendance_count', 0) and 
          getattr(lesson, 'present_count', 0) >= lesson.attendance_count):
        lesson.status = LessonStatus.COMPLETED
    else:
        lesson.status = LessonStatus.ONGOING


def _check_lesson_permission(
    db: Session, 
    user_id: UUID, 
    course_id: UUID,
    action: str = "manage"
) -> None:
    """
    Centralized permission checking for lesson operations.
    
    Raises:
        HTTPException: If user lacks permission
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Admins and devs have full access
    if user.has_role('admin', 'dev', 'tutor'):
        return
    
    # Check if tutor is assigned to this course
    is_assigned = db.query(CourseTutor).filter(
        CourseTutor.course_id == course_id,
        CourseTutor.tutor_id == user.id,
        CourseTutor.status == CourseTutorStatus.ACTIVE
    ).first()
    
    if not is_assigned:
        logger.warning(
            f"Permission denied: User {user_id} attempted to {action} "
            f"lesson in course {course_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to {action} lessons for this course"
        )


def create_lesson(db: Session, data: LessonCreate, user_id: UUID) -> Lesson:
    """
    Create a new lesson with full validation and permission checks.
    
    Args:
        db: Database session
        data: Validated lesson creation data
        user_id: ID of user creating the lesson
        
    Returns:
        Created lesson instance
        
    Raises:
        HTTPException: On validation or permission errors
    """
    try:
        # Fetch module with course for permission check
        module = db.query(Module).options(
            joinedload(Module.course)
        ).filter(Module.id == data.module_id).first()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        # Check permissions
        _check_lesson_permission(db, user_id, module.course_id, "create")
        
        # Check for duplicate order
        existing = db.query(Lesson).filter(
            Lesson.module_id == data.module_id,
            Lesson.order == data.order
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lesson with order {data.order} already exists in this module"
            )
        
        # Create lesson with explicit field mapping (BULLETPROOF ENUM HANDLING)
        lesson = Lesson(
            module_id=data.module_id,
            title=data.title,
            order=data.order,
            date=data.date,
            description=data.description,
            assessment_max=data.assessment_max,
            assignment_max=data.assignment_max,
            status=data.status.value if hasattr(data.status, 'value') else data.status,  # Force enum value
            created_by=user_id
        )
        
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        
        logger.info(
            f"Lesson created: {lesson.id} in module {module.id} by user {user_id}"
        )
        
        return lesson
        
    except HTTPException:
        db.rollback()
        raise
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data violates database constraints"
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error creating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create lesson at this time"
        )
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


def update_lesson(
    db: Session, 
    lesson_id: UUID, 
    data: LessonUpdate, 
    user_id: UUID,
    check_permission: bool = True
) -> Lesson:
    """
    Update a lesson with partial update support.
    
    Args:
        db: Database session
        lesson_id: ID of lesson to update
        data: Partial update data
        user_id: ID of user performing update
        check_permission: Whether to enforce permission checks
        
    Returns:
        Updated lesson instance
        
    Raises:
        HTTPException: On validation or permission errors
    """
    try:
        # Fetch lesson with related data
        lesson = db.query(Lesson).options(
            joinedload(Lesson.module).joinedload(Module.course)
        ).filter(Lesson.id == lesson_id).first()
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Check permissions if required
        if check_permission:
            _check_lesson_permission(
                db, user_id, lesson.module.course_id, "update"
            )
        
        # Get update data (exclude unset fields)
        update_data = data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        # Check for order conflicts
        if 'order' in update_data:
            existing = db.query(Lesson).filter(
                Lesson.module_id == lesson.module_id,
                Lesson.order == update_data['order'],
                Lesson.id != lesson_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lesson order {update_data['order']} already exists"
                )
        
        # Apply updates with explicit enum handling
        for field, value in update_data.items():
            if field == 'status' and hasattr(value, 'value'):
                # Force enum to value for status field
                setattr(lesson, field, value.value)
            else:
                setattr(lesson, field, value)
        
        db.commit()
        db.refresh(lesson)
        
        logger.info(f"Lesson updated: {lesson_id} by user {user_id}")
        
        return lesson
        
    except HTTPException:
        db.rollback()
        raise
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data violates database constraints"
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error updating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update lesson at this time"
        )
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error updating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


def delete_lesson(db: Session, lesson_id: UUID, user_id: UUID) -> None:
    """
    Delete a lesson with permission checks.
    
    Args:
        db: Database session
        lesson_id: ID of lesson to delete
        user_id: ID of user performing deletion
        
    Raises:
        HTTPException: On validation or permission errors
    """
    try:
        lesson = db.query(Lesson).options(
            joinedload(Lesson.module).joinedload(Module.course)
        ).filter(Lesson.id == lesson_id).first()
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Check permissions
        _check_lesson_permission(
            db, user_id, lesson.module.course_id, "delete"
        )
        
        db.delete(lesson)
        db.commit()
        
        logger.info(f"Lesson deleted: {lesson_id} by user {user_id}")
        
    except HTTPException:
        db.rollback()
        raise
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error deleting lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete lesson at this time"
        )


def get_lesson(db: Session, lesson_id: UUID) -> Lesson:
    """
    Retrieve a single lesson by ID.
    
    Args:
        db: Database session
        lesson_id: ID of lesson to retrieve
        
    Returns:
        Lesson instance
        
    Raises:
        HTTPException: If lesson not found
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return lesson


def list_module_lessons(
    db: Session, 
    module_id: UUID,
    status: Optional[str] = None,
    sort_by: str = "order",
    order: str = "asc"
) -> List[Lesson]:
    """
    List all lessons for a module with optional filtering and sorting.
    
    Args:
        db: Database session
        module_id: ID of module
        status: Optional status filter
        sort_by: Field to sort by
        order: Sort order (asc/desc)
        
    Returns:
        List of lessons
    """
    query = db.query(Lesson).filter(Lesson.module_id == module_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Lesson.status == status)
    
    # Apply sorting
    sort_field = getattr(Lesson, sort_by, Lesson.order)
    if order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())
    
    return query.all()


def list_lessons(db: Session, filters: LessonFilters) -> Tuple[List[Lesson], int]:
    """
    List lessons with pagination and filters.
    
    Args:
        db: Database session
        filters: Filter parameters
        
    Returns:
        Tuple of (lessons list, total count)
    """
    query = db.query(Lesson).filter(Lesson.module_id == filters.module_id)
    
    # Apply search if provided
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            (Lesson.title.ilike(search_term)) | 
            (Lesson.description.ilike(search_term))
        )
    
    total = query.count()
    
    # Apply pagination
    lessons = query.order_by(Lesson.order).offset(
        (filters.page - 1) * filters.page_size
    ).limit(filters.page_size).all()
    
    return lessons, total

