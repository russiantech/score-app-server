# from fastapi import APIRouter, Depends
# from app.models.assessment import Assessment
# from app.services import lesson_service
# from sqlalchemy.orm import Session
# from app.api.deps.users import get_db, tutor_required
# from app.schemas.lesson import LessonCreate, LessonOut
# from app.models.lesson import Lesson

# router = APIRouter()

# # @router.get("/course/{course_id}", response_model=list[LessonOut])
# # def get_lessons(course_id: str, db: Session = Depends(get_db)):
# #     return db.query(Lesson).filter(Lesson.course_id == course_id).all()

# @router.post("/", dependencies=[Depends(tutor_required)])
# def create_lesson(data: LessonCreate, db: Session = Depends(get_db)):
#     return lesson_service.create_lesson(db, data)

# @router.get("/course/{course_id}")
# def get_lessons(course_id: str, db: Session = Depends(get_db)):
#     return lesson_service.lessons_by_course(db, course_id)

# @router.get("/{lesson_id}")
# def get_assessments(lesson_id: str, db: Session = Depends(get_db)):
#     return db.query(Assessment).filter(Assessment.lesson_id == lesson_id).all()



# # v2
# # ============================================================================
# # FILE: app/api/routes/lessons.py
# # Lesson management endpoints
# # ============================================================================

# from fastapi import APIRouter, Depends, Request
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import lesson_service
# from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut
# from app.api.deps.users import tutor_required, get_current_user, get_db
# from app.utils.responses import PageSerializer, api_response

# router = APIRouter()

# @router.post("", response_model=LessonOut, status_code=201, dependencies=[Depends(tutor_required)])
# def create_lesson_endpoint(
#     request: Request,
#     data: LessonCreate,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     """
#     Create a lesson for a module (Tutor only)
    
#     Payload:
#     {
#         "module_id": "uuid",
#         "name": "HTML Basics",
#         "number": 1,
#         "date": "2024-12-10",
#         "description": "Introduction to HTML tags",
#         "assessment_max": 20,
#         "assignment_max": 30
#     }
#     """
#     lesson = lesson_service.create_lesson(db, data, current_user.id)
#     return api_response(
#         success=True,
#         message="Lesson created successfully",
#         data=lesson,
#         path=str(request.url.path),
#         status_code=201
#     )

# @router.get("/module/{module_id}", response_model=list[LessonOut])
# def list_module_lessons_endpoint(
#     request: Request,
#     module_id: UUID,
#     page: int = 1,
#     page_size: int = 50,
#     db: Session = Depends(get_db),
# ):
#     """List all lessons for a module"""
#     lessons = lesson_service.list_module_lessons(db, module_id)
    
#     serializer = PageSerializer(
#         request=request,
#         obj=lessons,
#         resource_name="lessons",
#         page=page,
#         page_size=page_size
#     )
#     return serializer.get_response("Lessons fetched successfully")

# @router.get("/{lesson_id}", response_model=LessonOut)
# def get_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Get single lesson by ID"""
#     lesson = lesson_service.get_lesson(db, lesson_id)
#     return api_response(
#         success=True,
#         message="Lesson fetched successfully",
#         data=lesson,
#         path=str(request.url.path)
#     )

# @router.put("/{lesson_id}", response_model=LessonOut, dependencies=[Depends(tutor_required)])
# def update_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     data: LessonUpdate,
#     db: Session = Depends(get_db),
# ):
#     """Update lesson (Tutor only)"""
#     lesson = lesson_service.update_lesson(db, lesson_id, data)
#     return api_response(
#         success=True,
#         message="Lesson updated successfully",
#         data=lesson,
#         path=str(request.url.path)
#     )

# @router.delete("/{lesson_id}", status_code=204, dependencies=[Depends(tutor_required)])
# def delete_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Delete lesson (Tutor only)"""
#     lesson_service.delete_lesson(db, lesson_id)
#     return api_response(
#         success=True,
#         message="Lesson deleted successfully",
#         path=str(request.url.path),
#         status_code=204
#     )




# # v3
# # ============================================================================
# # FILE: app/api/routes/lessons.py
# # Lesson management endpoints (Tutor access)
# # ============================================================================

# from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
# from uuid import UUID
# from sqlalchemy.orm import Session
# from typing import List, Optional

# from app.services import lesson_service
# from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut
# from app.api.deps.users import tutor_required, get_db
# from app.utils.responses import PageSerializer, api_response

# router = APIRouter()

# # @router.post("", response_model=LessonOut, status_code=201)
# # def create_lesson_endpoint(
# #     request: Request,
# #     data: LessonCreate,
# #     db: Session = Depends(get_db),
# #     current_user = Depends(tutor_required)
# # ):
# #     """
# #     Create a lesson for a module (Tutor only)
    
# #     Payload:
# #     {
# #         "module_id": "uuid",
# #         "name": "HTML Basics",
# #         "number": 1,
# #         "date": "2024-12-10",
# #         "description": "Introduction to HTML tags",
# #         "assessment_max": 20,
# #         "assignment_max": 30
# #     }
# #     """
# #     try:
# #         lesson = lesson_service.create_lesson(db, data, current_user.id)
# #         return api_response(
# #             success=True,
# #             message="Lesson created successfully",
# #             data=lesson,
# #             path=str(request.url.path),
# #             status_code=201
# #         )
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail=str(e)
# #         )

# # v2 - let exception propagate - remove try..except:
# @router.post("", response_model=LessonOut, status_code=201)
# def create_lesson_endpoint(
#     request: Request,
#     data: LessonCreate,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     lesson = lesson_service.create_lesson(db, data, current_user.id)
#     return api_response(
#         success=True,
#         message="Lesson created successfully",
#         data=lesson,
#         path=str(request.url.path),
#         status_code=201
#     )

# @router.get("/module/{module_id}", response_model=List[LessonOut])
# def list_module_lessons_endpoint(
#     request: Request,
#     module_id: UUID,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=100),
#     db: Session = Depends(get_db),
# ):
#     """List all lessons for a module"""
#     lessons = lesson_service.list_module_lessons(db, module_id)
    
#     serializer = PageSerializer(
#         request=request,
#         obj=lessons,
#         resource_name="lessons",
#         page=page,
#         page_size=page_size
#     )
#     return serializer.get_response("Lessons fetched successfully")

# @router.get("/{lesson_id}", response_model=LessonOut)
# def get_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Get single lesson by ID"""
#     lesson = lesson_service.get_lesson(db, lesson_id)
#     return api_response(
#         success=True,
#         message="Lesson fetched successfully",
#         data=lesson,
#         path=str(request.url.path)
#     )

# @router.patch("/{lesson_id}", response_model=LessonOut)
# def update_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     data: LessonUpdate,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     """Update lesson (Tutor only - must be assigned to course)"""
#     try:
#         print("LessonUpdate fields:", LessonUpdate.model_fields)
#         lesson = lesson_service.update_lesson(db, lesson_id, data, current_user.id)
#         return api_response(
#             success=True,
#             message="Lesson updated successfully",
#             data=lesson,
#             path=str(request.url.path)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=str(e)
#         )


# @router.delete("/{lesson_id}", status_code=204)
# def delete_lesson_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     """Delete lesson (Tutor only - must be assigned to course)"""
#     try:
#         lesson_service.delete_lesson(db, lesson_id, current_user.id)
#         return api_response(
#             success=True,
#             message="Lesson deleted successfully",
#             path=str(request.url.path),
#             status_code=204
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=str(e)
#         )




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
        "status": "scheduled"
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lesson: {str(e)}"
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lesson: {str(e)}"
        )

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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson: {str(e)}"
        )

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

