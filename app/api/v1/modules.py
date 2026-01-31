
# ============================================================================
# FILE: app/api/routes/modules.py
# Module management endpoints
# ============================================================================

from fastapi import APIRouter, Depends, Query, Request
from uuid import UUID
from sqlalchemy.orm import Session
from app.services import module_service
from app.schemas.module import ModuleCreate, ModuleUpdate, ModuleOut
from app.api.deps.users import get_db, tutor_required
from app.utils.responses import PageSerializer, api_response

router = APIRouter()

@router.post("", response_model=ModuleOut, status_code=201, dependencies=[Depends(tutor_required)])
def create_module_endpoint(
    request: Request,
    data: ModuleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a module for a course (Admin only)
    
    Payload:
    {
        "course_id": "uuid",
        "name": "Introduction to HTML",
        "order": 1,
        "description": "Learn HTML basics"
    }
    """
    module = module_service.create_module(db, data)
    return api_response(
        success=True,
        message="Module created successfully",
        data=module,
        path=str(request.url.path),
        status_code=201
    )

@router.get("/course/{course_id}", response_model=list[ModuleOut])
def list_course_modules_endpoint(
    request: Request,
    course_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all modules for a course"""
    modules = module_service.list_course_modules(db, course_id)

    serializer = PageSerializer(
        request=request,
        obj=modules,
        resource_name="modules",
        page=page,
        page_size=page_size,
        summary_func=lambda m: m.get_summary(include_relations=True),
    )
    return serializer.get_response("Modules fetched successfully")

# @router.get(
#     "/course/{course_id}",
#     response_model=CourseWithModulesOut,
# )
# def list_course_modules_endpoint(
#     request: Request,
#     course_id: UUID,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=100),
#     db: Session = Depends(get_db),
# ):
#     course, modules = module_service.list_course_with_modules(
#         db, course_id
#     )

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     serializer = PageSerializer(
#         request=request,
#         obj=modules,
#         resource_name="modules",
#         page=page,
#         page_size=page_size,
#         summary_func=lambda m: m.get_summary(include_relations=True),
#     )

#     paginated = serializer.get_response("Modules fetched successfully")

#     return {
#         "course": course.get_summary(include_relations=True),
#         "modules": paginated["data"]["modules"],
#     }


@router.get("/{module_id}", response_model=ModuleOut)
def get_module_endpoint(
    request: Request,
    module_id: UUID,
    db: Session = Depends(get_db),
):
    """Get single module by ID"""
    module = module_service.get_module(db, module_id)
    return api_response(
        success=True,
        message="Module fetched successfully",
        data=module,
        path=str(request.url.path)
    )

@router.put("/{module_id}", response_model=ModuleOut, dependencies=[Depends(tutor_required)])
def update_module_endpoint(
    request: Request,
    module_id: UUID,
    data: ModuleUpdate,
    db: Session = Depends(get_db),
):
    """Update module (Admin only)"""
    module = module_service.update_module(db, module_id, data)
    return api_response(
        success=True,
        message="Module updated successfully",
        data=module,
        path=str(request.url.path)
    )

@router.delete("/{module_id}", status_code=204, dependencies=[Depends(tutor_required)])
def delete_module_endpoint(
    request: Request,
    module_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete module (Admin only)"""
    module_service.delete_module(db, module_id)
    return api_response(
        success=True,
        message="Module deleted successfully",
        path=str(request.url.path),
        status_code=204
    )

