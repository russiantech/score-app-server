
# # ============================================================================
# # FILE: app/api/routes/lessons.py
# # Lesson management endpoints
# # ============================================================================


# v4
# FILE: app/api/v1/lessons.py

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.api.deps.users import tutor_required, get_current_user, get_db
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut
from app.services.lesson_service import (
    create_lesson,
    get_lesson,
    update_lesson,
    delete_lesson,
    list_module_lessons
)
from app.utils.responses import PageSerializer, api_response

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.put("/{lesson_id}", response_model=LessonOut)
def update_lesson_endpoint(
    request: Request,
    lesson_id: UUID,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Update a lesson (Partial update - all fields optional)
    
    Payload (all optional):
    {
        "name": "Updated Lesson Name",
        "number": 2,
        "date": "2026-02-02",
        "description": "Updated description",
        "assessment_max": 20,
        "assignment_max": 30,
        "status": "upcoming"
    }
    """
    try:
        lesson = update_lesson(db, lesson_id, data, current_user.id)
        
        return api_response(
            success=True,
            message="Lesson updated successfully",
            data=LessonOut.model_validate(lesson),
            path=str(request.url.path)
        )
    # except HTTPException as e:
    #     raise e
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Failed to update lesson: {str(e)}"
    #     )
    except Exception as e:
        db.rollback()
        logger.exception(f"Lesson update failed: {str(e)}")  # logs full stack trace
        raise HTTPException(
            status_code=500,
            detail="Unable to create lesson at this time."
        )

# Optionally add a PATCH endpoint if you need it
@router.patch("/{lesson_id}", response_model=LessonOut)
def patch_lesson_endpoint(
    request: Request,
    lesson_id: UUID,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Patch a lesson (Partial update - alias for PUT)
    This is identical to PUT but some clients prefer PATCH
    """
    try:
        lesson = update_lesson(db, lesson_id, data, current_user.id)
        
        return api_response(
            success=True,
            message="Lesson updated successfully",
            data=LessonOut.model_validate(lesson),
            path=str(request.url.path)
        )
    # except HTTPException as e:
    #     raise e
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Failed to update lesson: {str(e)}"
    #     )
    except Exception as e:
        db.rollback()
        logger.exception(f"Lesson patch failed: {str(e)}")  # logs full stack trace
        raise e
        # raise HTTPException(
        #     status_code=500,
        #     detail="Unable to create lesson at this time."
        # )

@router.post("", response_model=LessonOut, status_code=201)
def create_lesson_endpoint(
    request: Request,
    data: LessonCreate,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Create a new lesson
    
    Payload:
    {
        "module_id": "uuid",
        "name": "Lesson Name",
        "number": 1,
        "date": "2026-02-02",
        "description": "Lesson description",
        "assessment_max": 20,
        "assignment_max": 30,
        "status": "draft"
    }
    """
    try:
        lesson = create_lesson(db, data, current_user.id)
        
        return api_response(
            success=True,
            message="Lesson created successfully",
            data=LessonOut.model_validate(lesson),
            path=str(request.url.path),
            status_code=201
        )
    
    # except HTTPException as e:
    #     raise e
    # except Exception as e:
    #     logger.exception(f"Lesson creation failed: {str(e)}")  # logs full stack trace
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Failed to create lesson."
    #     )
    
    except Exception as e:
        db.rollback()
        logger.exception(f"Lesson creation failed: {str(e)}")  # logs full stack trace
        raise e
        # raise HTTPException(
        #     status_code=500,
        #     detail="Unable to create lesson at this time."
        # )

@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson_endpoint(
    request: Request,
    lesson_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single lesson by ID"""
    lesson = get_lesson(db, lesson_id)
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return api_response(
        success=True,
        message="Lesson fetched successfully",
        data=LessonOut.model_validate(lesson),
        path=str(request.url.path)
    )


# @router.delete("/{lesson_id}", status_code=204)
# def delete_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     """Delete a lesson"""
#     try:
#         delete_lesson(db, lesson_id)
        
#         return api_response(
#             success=True,
#             message="Lesson deleted successfully",
#             path=str(request.url.path),
#             status_code=204
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete lesson: {str(e)}"
#         )


@router.delete("/{lesson_id}", status_code=204)
def delete_lesson_endpoint(
    request: Request,
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(tutor_required),
):
    delete_lesson(db, lesson_id)

    return api_response(
        success=True,
        message="Lesson deleted successfully",
        path=str(request.url.path),
        status_code=204
    )

@router.get("/module/{module_id}", response_model=List[LessonOut])
def list_module_lessons_endpoint(
    request: Request,
    module_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("number", description="Sort by field (number, date, created_at)"),
    order: str = Query("asc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all lessons for a module"""
    lessons = list_module_lessons(
        db, 
        module_id, 
        status=status,
        sort_by=sort_by,
        order=order
    )
    
    serializer = PageSerializer(
        request=request,
        items=lessons,
        resource_name="lessons",
        page=page,
        page_size=page_size,
    )
    
    return serializer.get_response("Lessons fetched successfully")

