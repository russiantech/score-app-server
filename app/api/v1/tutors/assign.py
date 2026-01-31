
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps.users import admin_required, get_db
from app.models.user import User
from app.schemas.tutors import (
    TutorCourseCreate,
    TutorCourseFilters,
    TutorCourseUpdate,
    BulkTutorCourseCreate,
    BulkTutorCourseDelete,
    ReassignTutorCourseRequest,
)

# from app.services import tutor_service
from app.utils.responses import PageSerializer, api_response

# from . import router
from fastapi import APIRouter

from app.services.tutors.assign import *

router = APIRouter(
    prefix="/tutors",
    tags=["Tutor • Admin"],
    # dependencies=[Depends(admin_required)]
)

@router.get(
    "",
    summary="List tutor assignments",
    description="Retrieve a paginated list of tutor assignments with optional filters",
)
def list_assignments_endpoint(
    request: Request,
    filters: TutorCourseFilters = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Get all tutor assignments with filtering, sorting, and pagination.
    """
    assignments, total = list_assignments(
        db=db,
        filters=filters
    )

    def assignment_serializer(assignment):
        return assignment.get_summary(include_relations=filters.include_relations)

    serializer = PageSerializer(
        request=request,
        obj=assignments,
        resource_name="assignments",
        summary_func=assignment_serializer,
        page=filters.page,
        page_size=filters.page_size
    )

    return serializer.get_response("Assignments fetched successfully")


@router.get(
    "/stats",
    summary="Get assignment statistics",
    description="Get comprehensive statistics about tutor assignments",
)
def get_assignment_stats_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Get statistics about tutor assignments.
    """
    stats = get_assignment_stats(db)

    return api_response(
        success=True,
        data=stats,
        message="Statistics fetched successfully",
    )


@router.get(
    " /{assignment_id}/assignment",
    summary="Get assignment by ID",
    description="Retrieve a single assignment by its ID",
)
def get_assignment_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    include_relations: bool = Query(default=True),
):
    """
    Get a single assignment by ID.
    """
    assignment = db.query(CourseTutor).filter(
        CourseTutor.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return api_response(
        success=True,
        data=assignment.get_summary(include_relations=include_relations),
        message="Assignment fetched successfully",
    )


@router.post(
    "",
    summary="Create assignment",
    description="Assign a tutor to a course",
)
def create_assignment_endpoint(
    assignment_data: TutorCourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Create a new tutor assignment.
    """
    try:
        assignment = create_assignment(
            db=db,
            assignment_data=assignment_data,
        )

        return api_response(
            assignment.get_summary(include_relations=True),
            message="Tutor assigned successfully",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch(
    "/{assignment_id}",
    summary="Update assignment",
    description="Update an assignment's status or notes",
)
def update_assignment_endpoint(
    assignment_id: UUID,
    update_data: TutorCourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Update a tutor assignment.
    """
    try:
        assignment = db.query(CourseTutor).filter(
            CourseTutor.id == assignment_id
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if update_data.status:
            assignment = update_assignment_status(
                db=db,
                assignment_id=assignment_id,
                status=update_data.status.value
            )

        if update_data.notes is not None:
            assignment.notes = update_data.notes
            db.commit()
            db.refresh(assignment)

        return api_response(
            assignment.get_summary(include_relations=True),
            message="Assignment updated successfully",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch(
    "/{assignment_id}/status",
    summary="Update assignment status",
    description="Change the status of an assignment (active/inactive/revoked)",
)
def update_assignment_status_endpoint(
    assignment_id: UUID,
    status: str = Query(..., description="New status (active, inactive, revoked)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Update the status of a tutor assignment.
    """
    try:
        assignment = update_assignment_status(
            db=db,
            assignment_id=assignment_id,
            status=status
        )

        return api_response(
            assignment.get_summary(include_relations=True),
            message=f"Assignment status updated to {status}",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete(
    "/{assignment_id}",
    summary="Delete assignment",
    description="Unassign a tutor from a course",
)
def delete_assignment_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Delete a tutor assignment (unassign tutor from course).
    """
    try:
        delete_assignment(db, assignment_id)

        return api_response(
            None,
            message="Tutor unassigned successfully",
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/tutor/{tutor_id}",
    summary="Get assignments by tutor",
    description="Get all courses assigned to a specific tutor",
)
def get_tutor_assignments_endpoint(
    tutor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Get all assignments for a specific tutor.
    """
    assignments = get_tutor_assignments(db, tutor_id)

    return api_response(
        success=True,
        data=[a.get_summary(include_relations=True) for a in assignments],
        message="Tutor assignments fetched successfully",
    )


@router.get(
    "/course/{course_id}",
    summary="Get assignments by course",
    description="Get all tutors assigned to a specific course",
)
def get_course_assignments_endpoint(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Get all assignments for a specific course.
    """
    assignments = get_course_assignments(db, course_id)

    return api_response(
        success=True,
        data=[a.get_summary(include_relations=True) for a in assignments],
        message="Course assignments fetched successfully",
    )


@router.post(
    "/bulk",
    summary="Bulk create assignments",
    description="Assign a tutor to multiple courses at once",
)
def bulk_create_assignments_endpoint(
    bulk_data: BulkTutorCourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Bulk create assignments for one tutor to multiple courses.
    """
    try:
        result = bulk_create_assignments(
            db=db,
            bulk_data=bulk_data
        )

        return api_response(
            success=True,
            data={
                "created": [a.get_summary(include_relations=True) for a in result["created"]],
                "failed": result["failed"],
                "summary": result["summary"]
            },
            message=f"Bulk assignment completed: {result['summary']['successful']} successful, {result['summary']['failed']} failed",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/bulk-delete",
    summary="Bulk delete assignments",
    description="Delete multiple assignments at once",
)
def bulk_delete_assignments_endpoint(
    delete_data: BulkTutorCourseDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Bulk delete assignments.
    """
    result = bulk_delete_assignments(
        db=db,
        assignment_ids=delete_data.assignment_ids
    )

    return api_response(
        success=True,
        data=result,
        message=f"Bulk deletion completed: {result['deleted']} deleted, {len(result['failed'])} failed",
    )


@router.post(
    "/reassign",
    summary="Reassign course",
    description="Reassign a course from one tutor to another",
)
def reassign_course_endpoint(
    reassignment_data: ReassignTutorCourseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """
    Reassign a course to a different tutor.
    """
    try:
        new_assignment = reassign_course(
            db=db,
            assignment_id=reassignment_data.assignment_id,
            new_tutor_id=reassignment_data.new_tutor_id,
            reason=reassignment_data.reason
        )

        return api_response(
            new_assignment.get_summary(include_relations=True),
            message="Course reassigned successfully",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
