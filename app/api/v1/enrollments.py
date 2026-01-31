# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.api.deps.users import admin_required, get_db
# from app.schemas.enrollment import EnrollmentCreate
# from app.services import enrollment_service

# router = APIRouter()    

# @router.post("/", dependencies=[Depends(admin_required)])
# def enroll_student(data: EnrollmentCreate, db: Session = Depends(get_db)):
#     return enrollment_service.enroll_student(db, data)


# # v2
# # ============================================================================
# # FILE: app/api/routes/enrollments.py
# # Enrollment management endpoints
# # ============================================================================

# from fastapi import APIRouter, Depends, Request
# from uuid import UUID
# from sqlalchemy.orm import Session
# from app.services import enrollment_service
# from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut
# from app.api.deps.users import admin_required, get_current_user, get_db
# from app.utils.responses import PageSerializer, api_response

# router = APIRouter()

# @router.post("", response_model=EnrollmentOut, status_code=201, dependencies=[Depends(admin_required)])
# def create_enrollment_endpoint(
#     request: Request,
#     data: EnrollmentCreate,
#     db: Session = Depends(get_db),
# ):
#     """
#     Enroll a student in a course (Admin only)
    
#     Payload:
#     {
#         "student_id": "uuid",
#         "course_id": "uuid"
#     }
#     """
#     enrollment = enrollment_service.enroll_student(db, data.student_id, data.course_id)
#     return api_response(
#         success=True,
#         message="Student enrolled successfully",
#         data=enrollment,
#         path=str(request.url.path),
#         status_code=201
#     )

# @router.get("", response_model=list[EnrollmentOut])
# def list_enrollments_endpoint(
#     request: Request,
#     course_id: UUID | None = None,
#     student_id: UUID | None = None,
#     page: int = 1,
#     page_size: int = 20,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """
#     List enrollments with optional filters
    
#     Query params:
#     - course_id: filter by course
#     - student_id: filter by student
#     """
#     enrollments = enrollment_service.list_enrollments(
#         db, 
#         course_id=course_id, 
#         student_id=student_id
#     )
    
#     serializer = PageSerializer(
#         request=request,
#         obj=enrollments,
#         resource_name="enrollments",
#         page=page,
#         page_size=page_size
#     )
#     return serializer.get_response("Enrollments fetched successfully")

# @router.delete("/{enrollment_id}", status_code=204, dependencies=[Depends(admin_required)])
# def delete_enrollment_endpoint(
#     request: Request,
#     enrollment_id: UUID,
#     db: Session = Depends(get_db),
# ):
#     """Unenroll student from course (Admin only)"""
#     enrollment_service.unenroll_student(db, enrollment_id)
#     return api_response(
#         success=True,
#         message="Student unenrolled successfully",
#         path=str(request.url.path),
#         status_code=204
#     )


# # v3
# from fastapi import APIRouter, Depends, Query, Request, HTTPException
# from sqlalchemy.orm import Session
# from typing import Optional
# from uuid import UUID

# from app.api.deps.users import get_db
# from app.models.user import User
# from app.schemas.enrollment import EnrollmentFilters

# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.api.deps.users import admin_required, get_db
# from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut
# from app.services import enrollment_service


# # router = APIRouter(prefix="/enrollments", tags=["enrollments"])
# router = APIRouter()


# @router.get(
#     "",
#     response_model=list[EnrollmentOut],
#     summary="List enrollments",
#     description="Retrieve a paginated list of enrollments with optional filters",
# )
# def list_enrollments_endpoint(
#     request: Request,
#     search: Optional[str] = Query(default=None),
#     status: Optional[str] = Query(default=None, regex="^(active|completed|dropped)$"),
#     student_id: Optional[UUID] = Query(default=None),
#     course_id: Optional[UUID] = Query(default=None),
#     sort_by: str = Query(default="enrolled_at", regex="^(enrolled_at|student_name|course_name|progress)$"),
#     order: str = Query(default="desc", regex="^(asc|desc)$"),
#     page: int = Query(default=1, ge=1),
#     page_size: int = Query(default=10, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     filters = EnrollmentFilters(
#         search=search,
#         status=status,
#         student_id=student_id,
#         course_id=course_id,
#         sort_by=sort_by,
#         order=order,
#         page=page,
#         page_size=page_size,
#     )

#     enrollments, total = enrollment_service.list_enrollments(db, filters=filters)
#     total_pages = (total + page_size - 1) // page_size

#     return {
#         "success": True,
#         "message": "Enrollments fetched successfully",
#         "data": {
#             "enrollments": enrollments,
#             "meta": {
#                 "total": total,
#                 "page": page,
#                 "page_size": page_size,
#                 "total_pages": total_pages,
#                 "has_next": page < total_pages,
#                 "has_prev": page > 1,
#             }
#         }
#     }


# @router.get(
#     "/stats",
#     summary="Get enrollment statistics",
# )
# def get_enrollment_stats_endpoint(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     stats = enrollment_service.get_enrollment_stats(db)
    
#     return {
#         "success": True,
#         "message": "Statistics fetched successfully",
#         "data": stats
#     }


# @router.post(
#     "",
#     response_model=EnrollmentOut,
#     summary="Create enrollment",
#     description="Enroll a student in a course",
# )
# def create_enrollment_endpoint(
#     enrollment_data: EnrollmentCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     try:
#         enrollment = enrollment_service.create_enrollment(
#             db=db,
#             student_id=enrollment_data.student_id,
#             course_id=enrollment_data.course_id
#         )
        
#         return {
#             "success": True,
#             "message": "Student enrolled successfully",
#             "data": enrollment
#         }
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.delete(
#     "/{enrollment_id}",
#     summary="Delete enrollment",
#     description="Unenroll a student from a course",
# )
# def delete_enrollment_endpoint(
#     enrollment_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     try:
#         enrollment_service.delete_enrollment(db, enrollment_id)
        
#         return {
#             "success": True,
#             "message": "Student unenrolled successfully",
#             "data": None
#         }
#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
    


# v3
# ============================================================================
# ROUTER - Enrollments
# FILE: app/api/v1/enrollments.py
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps.users import admin_required, get_db, tutor_required
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentFilters,
)
from app.services import enrollment_service
from app.utils.responses import PageSerializer, api_response
# from app.utils.pagination import PageSerializer


router = APIRouter()

# @router.get(
#     "",
#     summary="List enrollments",
#     description="Retrieve a paginated list of enrollments with optional filters",
# )
# def list_enrollments_endpoint(
#     filters: EnrollmentFilters = Depends(),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     enrollments, total = enrollment_service.list_enrollments(
#         db=db,
#         filters=filters
#     )

#     data = [
#         {
#             **e.get_summary(),
#             "status": e.status.value,
#             "student": e.student.get_summary() if e.student else None,
#             "course": e.course.get_summary() if e.course else None,
#         }
#         for e in enrollments
#     ]

#     return api_response(
#         PageSerializer.serialize(
#             items=data,
#             total=total,
#             page=filters.page,
#             page_size=filters.page_size,
#         ),
#         message="Enrollments fetched successfully",
#     )


from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps.users import admin_required, get_db
from app.models.user import User
from app.schemas.enrollment import EnrollmentFilters
from app.services import enrollment_service
from app.utils.responses import PageSerializer

router = APIRouter()


@router.get(
    "",
    summary="List enrollments",
    description="Retrieve a paginated list of enrollments with optional filters",
)
def list_enrollments_endpoint(
    request: Request,
    filters: EnrollmentFilters = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(tutor_required),
    include_relations: bool = Query(default=False),  # ← Optional control
):
    enrollments, total = enrollment_service.list_enrollments(
        db=db,
        filters=filters
    )

    # serializer = PageSerializer(
    #     request=request,
    #     obj=enrollments,
    #     resource_name="enrollments",
    #     page=filters.page,
    #     page_size=filters.page_size,
    # )
    
    # serializer = PageSerializer(
    #     request=request,
    #     obj=enrollments,
    #     resource_name="enrollments",
    #     page=filters.page,
    #     page_size=filters.page_size,
    #     summary_func = enrollments.get_summary(include_relations=True,),
    #     # include_relations=True,  # ← Controls relation loading
    # )
    
    def enrollment_serializer(enrollment):
        return enrollment.get_summary(include_relations=include_relations)

    serializer = PageSerializer(
        request=request,
        obj=enrollments,
        resource_name="enrollments",
        summary_func=enrollment_serializer,
        page=filters.page,
        page_size=filters.page_size
    )

    return serializer.get_response("Enrollments fetched successfully")



# @router.get("/enrollments-0", response_model=List[EnrollmentOut])
# def list_enrollments_endpoint0(
#     request: Request,
#     course_id: Optional[UUID] = Query(None, description="Filter by course ID"),
#     student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user = Depends(admin_required)
# ):
#     """
#     List enrollments with optional filters (Admin only)
#     """
#     filters = {}
#     if course_id:
#         filters["course_id"] = course_id
#     if student_id:
#         filters["student_id"] = student_id
    
#     enrollments, total = enrollment_service.list_enrollments(
#         db=db,
#         filters=filters
#     )

#     serializer = PageSerializer(
#         request=request,
#         obj=enrollments,
#         resource_name="enrollments",
#         page=page,
#         page_size=page_size,
#     )

#     return serializer.get_response("Enrollments fetched successfully")


@router.get(
    "/stats",
    summary="Get enrollment statistics",
)
def get_enrollment_stats_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    stats = enrollment_service.get_enrollment_stats(db)

    return api_response(
        success=True,
        data=stats,
        message="Statistics fetched successfully",
    )


# @router.post(
#     "",
#     summary="Create enrollment",
#     description="Enroll a student in a course",
# )
# def create_enrollment_endpoint(
#     enrollment_data: EnrollmentCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     try:
#         enrollment = enrollment_service.create_enrollment(
#             db=db,
#             student_id=enrollment_data.student_id,
#             course_id=enrollment_data.course_id,
#         )

#         return api_response(
#             {
#                 **enrollment.get_summary(),
#                 "status": enrollment.status.value,
#             },
#             message="Student enrolled successfully",
#         )

#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc))

# @router.post(
#     "",
#     summary="Create enrollment",
#     description="Enroll a student in a course",
# )
# def create_enrollment_endpoint(
#     enrollment_data: EnrollmentCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(admin_required),
# ):
#     try:
#         enrollment = enrollment_service.create_enrollment(
#             db=db,
#             enrollment_data=enrollment_data,
#         )

#         return api_response(
#             {
#                 **enrollment.get_summary(),
#                 "status": enrollment.status.value,
#             },
#             message="Student enrolled successfully",
#         )

#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc))

# Fixed endpoint - prevents circular reference serialization
@router.post(
    "",
    summary="Create enrollment",
    description="Enroll a student in a course",
)
def create_enrollment_endpoint(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    try:
        enrollment = enrollment_service.create_enrollment(
            db=db,
            enrollment_data=enrollment_data,
        )
        
        # ✅ FIXED: Return only the summary dict, not the object
        return api_response(
            enrollment.get_summary(),  # This already includes status.value
            message="Student enrolled successfully",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete(
    "/{enrollment_id}",
    summary="Delete enrollment",
    description="Unenroll a student from a course",
)
def delete_enrollment_endpoint(
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    try:
        enrollment_service.delete_enrollment(db, enrollment_id)

        return api_response(
            None,
            message="Student unenrolled successfully",
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

