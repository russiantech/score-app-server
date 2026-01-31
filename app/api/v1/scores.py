# # v3 - Enhanced score routes
# # ============================================================================
# # FILE: app/api/routes/scores.py
# # Score recording endpoints
# # ============================================================================

# from typing import List, Dict, Any
# from fastapi import APIRouter, Depends, Request, HTTPException, status
# from uuid import UUID
# from sqlalchemy.orm import Session
# from pydantic import BaseModel

# from app.services import score_service
# from app.schemas.score import BulkScoreInput
# from app.api.deps.users import tutor_required, get_db, get_current_user
# from app.utils.responses import api_response

# router = APIRouter()


# # class ScoreRecordInput(BaseModel):
# #     """Individual score record"""
# #     enrollment_id: str
# #     score: float
# #     remarks: str = ""


# # class BulkScoreInput(BaseModel):
# #     """Bulk score submission"""
# #     lesson_id: str
# #     max_score: float
# #     scores: List[ScoreRecordInput]


# @router.get("/{lesson_id}/lesson")
# @router.get("/{lesson_id}/lesson/with-students")
# def get_lesson_scores_with_students_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """
#     Get scores for a lesson WITH all enrolled students.
#     Returns both scored and unscored students.
#     """
#     try:
#         data = score_service.get_lesson_scores_with_students(db, lesson_id)
#         return api_response(
#             success=True,
#             message="Lesson scores with students fetched successfully",
#             data=data,
#             path=str(request.url.path)
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )


# # @router.post("/bulk", status_code=201)
# # def bulk_create_or_update_scores_endpoint(
# #     request: Request,
# #     data: BulkScoreInput,
# #     db: Session = Depends(get_db),
# #     current_user = Depends(tutor_required)
# # ):
# #     """
# #     Create or update score records for multiple students.
# #     Handles both new records and updates.
    
# #     Payload:
# #     {
# #         "lesson_id": "uuid",
# #         "max_score": 100,
# #         "scores": [
# #             {
# #                 "enrollment_id": "uuid",
# #                 "score": 85.5,
# #                 "remarks": "Good work"
# #             }
# #         ]
# #     }
# #     """
# #     try:
# #         lesson_id = UUID(data.lesson_id)
# #         scores_data = [record.dict() for record in data.scores]
        
# #         result = score_service.bulk_create_or_update_scores(
# #             db,
# #             lesson_id,
# #             scores_data,
# #             data.max_score,
# #             current_user
# #         )
        
# #         return api_response(
# #             success=True,
# #             message="Scores saved successfully",
# #             data=result,
# #             path=str(request.url.path),
# #             status_code=201
# #         )
# #     except HTTPException as e:
# #         raise e
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail=str(e)
# #         )

# @router.post("/scores/bulk")
# def bulk_scores_endpoint(
#     payload: BulkScoreInput,
#     db: Session = Depends(get_db),
#     current_user = Depends(tutor_required)
# ):
#     return score_service.bulk_create_or_update_scores(
#         db=db,
#         lesson_id=payload.lesson_id,
#         columns_config=[c.model_dump() for c in payload.columns],
#         scores_data=[s.model_dump() for s in payload.scores],
#         current_user=current_user,
#     )


# @router.get("/{lesson_id}/lesson")
# def get_lesson_scores_endpoint(
#     request: Request,
#     lesson_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Get all scores for a lesson (legacy)"""
#     scores = score_service.get_lesson_scores(db, lesson_id)
#     return api_response(
#         success=True,
#         message="Lesson scores fetched successfully",
#         data=scores,
#         path=str(request.url.path)
#     )





# v2
# app/api/routes/scores.py
# Fixed score routes with proper error handling

from fastapi import APIRouter, Depends, Request, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session

from app.services import score_service
from app.schemas.score import BulkScoreInput, CourseBulkScoreInput, ModuleBulkScoreInput
from app.api.deps.users import tutor_required, get_db, get_current_user
from app.utils.responses import api_response

router = APIRouter()


@router.get("/{lesson_id}/lesson")
@router.get("/{lesson_id}/lesson/with-students")
def get_lesson_scores_with_students_endpoint(
    request: Request,
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get scores for a lesson WITH all enrolled students.
    Returns both scored and unscored students with column structure.
    """
    try:
        data = score_service.get_lesson_scores_with_students(db, lesson_id)
        return api_response(
            success=True,
            message="Lesson scores fetched successfully",
            data=data,
            path=str(request.url.path)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/bulk", status_code=201)
def bulk_create_or_update_scores_endpoint(
    request: Request,
    payload: BulkScoreInput,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Create or update score records in bulk with flexible columns.
    
    Payload structure:
    {
        "lesson_id": "uuid",
        "columns": [
            {
                "id": "column-uuid-or-temp-id",
                "type": "homework",
                "title": "Homework Assignment",
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
                        "column_id": "column-uuid",
                        "score": 25,
                        "remarks": "Good work"
                    }
                ]
            }
        ]
    }
    """
    try:
        lesson_id = UUID(payload.lesson_id)
        
        # Convert Pydantic models to dicts
        columns_config = [col.model_dump() for col in payload.columns]
        scores_data = [score.model_dump() for score in payload.scores]
        
        result = score_service.bulk_create_or_update_lesson_scores(
            db=db,
            lesson_id=lesson_id,
            columns_config=columns_config,
            scores_data=scores_data,
            current_user=current_user
        )
        
        return api_response(
            success=True,
            message="Scores saved successfully",
            data=result,
            path=str(request.url.path),
            status_code=201
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save scores: {str(e)}"
        )
    
    
# updated

# # app/api/routes/scores_extended.py
# # Add these routes to your existing scores.py file

# from fastapi import APIRouter, Depends, Request, HTTPException, status
# from uuid import UUID
# from sqlalchemy.orm import Session
# from pydantic import BaseModel
# from typing import List, Dict, Any

# from app.services import score_service
# from app.api.deps.users import tutor_required, get_db, get_current_user
# from app.utils.responses import api_response

# router = APIRouter()


# ============================================================================
# MODULE EXAM ROUTES
# ============================================================================

@router.get("/{module_id}/module")
def get_module_scores_endpoint(
    request: Request,
    module_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get module exam scores with all enrolled students.
    """
    try:
        data = score_service.get_module_scores_with_students(db, module_id)
        return api_response(
            success=True,
            message="Module exam scores fetched successfully",
            data=data,
            path=str(request.url.path)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/module/bulk", status_code=201)
def bulk_create_module_scores_endpoint(
    request: Request,
    payload: ModuleBulkScoreInput,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Create or update module exam scores in bulk.
    """
    try:
        module_id = UUID(payload.module_id)
        columns_config = [col.model_dump() for col in payload.columns]
        scores_data = [score.model_dump() for score in payload.scores]
        
        result = score_service.bulk_create_or_update_module_scores(
            db=db,
            module_id=module_id,
            columns_config=columns_config,
            scores_data=scores_data,
            current_user=current_user
        )
        
        return api_response(
            success=True,
            message="Module exam scores saved successfully",
            data=result,
            path=str(request.url.path),
            status_code=201
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save module scores: {str(e)}"
        )


# ============================================================================
# COURSE PROJECT SCORES ROUTES
# ============================================================================

@router.get("/{course_id}/course")
def get_course_scores_endpoint(
    request: Request,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get course project scores with all enrolled students.
    """
    try:
        data = score_service.get_course_scores_with_students(db, course_id)
        return api_response(
            success=True,
            message="Course project scores fetched successfully",
            data=data,
            path=str(request.url.path)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/course/bulk", status_code=201)
def bulk_create_course_scores_endpoint(
    request: Request,
    payload: CourseBulkScoreInput,
    db: Session = Depends(get_db),
    current_user = Depends(tutor_required)
):
    """
    Create or update course project scores in bulk.
    """
    try:
        course_id = UUID(payload.course_id)
        columns_config = [col.model_dump() for col in payload.columns]
        scores_data = [score.model_dump() for score in payload.scores]
        
        result = score_service.bulk_create_or_update_course_scores(
            db=db,
            course_id=course_id,
            columns_config=columns_config,
            scores_data=scores_data,
            current_user=current_user
        )
        
        return api_response(
            success=True,
            message="Course project scores saved successfully",
            data=result,
            path=str(request.url.path),
            status_code=201
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save course scores: {str(e)}"
        )