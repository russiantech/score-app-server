# ============================================================================
# SERVICE - Tutor Assignments
# FILE: app/services/tutor_assignment_service.py
# ============================================================================

from typing import Optional, Tuple, List
from sqlalchemy import or_, desc, asc, and_, func
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from datetime import datetime

from app.models.tutors import CourseTutor, CourseTutorStatus
from app.schemas.tutors import (
    TutorCourseCreate,
    TutorCourseFilters,
    BulkTutorCourseCreate,
)
from app.models.course import Course
from app.models.user import User
from app.models.rbac import Role


def list_assignments(
    db: Session,
    filters: Optional[TutorCourseFilters] = None
) -> Tuple[List[CourseTutor], int]:
    """
    Get filtered, sorted, and paginated list of tutor assignments.
    Prevents N+1 queries when relations are included.
    """
    query = (
        db.query(CourseTutor)
        .options(
            joinedload(CourseTutor.tutor),
            joinedload(CourseTutor.course)
        )
    )

    filters = filters or TutorCourseFilters()

    # Apply search filter
    if filters.search:
        term = f"%{filters.search.lower()}%"
        query = (
            query
            .join(CourseTutor.tutor)
            .join(CourseTutor.course)
            .filter(
                or_(
                    User.names.ilike(term),
                    User.email.ilike(term),
                    Course.title.ilike(term),
                    Course.code.ilike(term)
                )
            )
        )

    # Apply status filter
    if filters.status and filters.status != 'all':
        query = query.filter(CourseTutor.status == CourseTutorStatus(filters.status))

    # Apply tutor filter
    if filters.tutor_id:
        query = query.filter(CourseTutor.tutor_id == filters.tutor_id)

    # Apply course filter
    if filters.course_id:
        query = query.filter(CourseTutor.course_id == filters.course_id)

    # Apply sorting
    sort_col = getattr(CourseTutor, filters.sort_by, CourseTutor.created_at)
    query = query.order_by(desc(sort_col) if filters.order == "desc" else asc(sort_col))

    # Get total count
    total = query.count()

    # Apply pagination
    assignments = (
        query
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
        .all()
    )

    return assignments, total


def create_assignment(
    db: Session,
    assignment_data: TutorCourseCreate
) -> CourseTutor:
    """
    Create a new tutor assignment.
    """
    # Check if assignment already exists
    existing = db.query(CourseTutor).filter(
        CourseTutor.tutor_id == assignment_data.tutor_id,
        CourseTutor.course_id == assignment_data.course_id,
        CourseTutor.status != CourseTutorStatus.REVOKED
    ).first()

    if existing:
        raise ValueError("This tutor is already assigned to this course")

    # Verify tutor exists and has tutor role
    tutor = db.query(User).filter(User.id == assignment_data.tutor_id).first()
    if not tutor:
        raise ValueError("Tutor not found")
    
    if not tutor.has_role('tutor'):
        raise ValueError("User is not a tutor")

    # Verify course exists
    course = db.query(Course).filter(Course.id == assignment_data.course_id).first()
    if not course:
        raise ValueError("Course not found")

    # Create assignment
    assignment = CourseTutor(
        tutor_id=assignment_data.tutor_id,
        course_id=assignment_data.course_id,
        notes=assignment_data.notes,
        status=CourseTutorStatus.ACTIVE,
        created_at=datetime.utcnow()
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def delete_assignment(db: Session, assignment_id: UUID) -> None:
    """
    Delete a tutor assignment (unassign tutor from course).
    """
    assignment = db.query(CourseTutor).filter(
        CourseTutor.id == assignment_id
    ).first()

    if not assignment:
        raise ValueError("Assignment not found")

    db.delete(assignment)
    db.commit()


def update_assignment_status(
    db: Session,
    assignment_id: UUID,
    status: str
) -> CourseTutor:
    """
    Update the status of a tutor assignment.
    """
    assignment = db.query(CourseTutor).filter(
        CourseTutor.id == assignment_id
    ).first()

    if not assignment:
        raise ValueError("Assignment not found")

    assignment.status = CourseTutorStatus(status)
    
    if status == CourseTutorStatus.REVOKED:
        assignment.revoked_at = datetime.utcnow()

    db.commit()
    db.refresh(assignment)

    return assignment


def get_assignment_stats(db: Session) -> dict:
    """
    Get tutor assignment statistics.
    """
    # Total assignments
    total_assignments = db.query(CourseTutor).count()

    # Active assignments
    active_assignments = (
        db.query(CourseTutor)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .count()
    )

    # Inactive assignments
    inactive_assignments = (
        db.query(CourseTutor)
        .filter(CourseTutor.status == CourseTutorStatus.INACTIVE)
        .count()
    )

    # Revoked assignments
    revoked_assignments = (
        db.query(CourseTutor)
        .filter(CourseTutor.status == CourseTutorStatus.REVOKED)
        .count()
    )

    # Total tutors
    total_tutors = (
        db.query(User)
        .filter(User.roles.any(Role.name == "tutor"))
        .filter(User.is_active.is_(True))
        .count()
    )

    # Tutors with at least one active assignment
    tutors_assigned = (
        db.query(CourseTutor.tutor_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .distinct()
        .count()
    )

    # Tutors without assignments
    tutors_unassigned = total_tutors - tutors_assigned

    # Total courses
    total_courses = (
        db.query(Course)
        .filter(Course.is_active.is_(True))
        .count()
    )

    # Courses with at least one active assignment
    courses_assigned = (
        db.query(CourseTutor.course_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .distinct()
        .count()
    )

    # Courses without assignments
    courses_unassigned = total_courses - courses_assigned

    # Average courses per tutor (for tutors with assignments)
    avg_courses_per_tutor = 0
    if tutors_assigned > 0:
        avg_courses_per_tutor = round(active_assignments / tutors_assigned, 2)

    return {
        "total_assignments": total_assignments,
        "active_assignments": active_assignments,
        "inactive_assignments": inactive_assignments,
        "revoked_assignments": revoked_assignments,
        "total_tutors": total_tutors,
        "tutors_assigned": tutors_assigned,
        "tutors_unassigned": tutors_unassigned,
        "total_courses": total_courses,
        "courses_assigned": courses_assigned,
        "courses_unassigned": courses_unassigned,
        "avg_courses_per_tutor": avg_courses_per_tutor,
    }


def get_tutor_assignments(
    db: Session,
    tutor_id: UUID
) -> List[CourseTutor]:
    """
    Get all assignments for a specific tutor.
    """
    return (
        db.query(CourseTutor)
        .options(joinedload(CourseTutor.course))
        .filter(CourseTutor.tutor_id == tutor_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .all()
    )


def get_course_assignments(
    db: Session,
    course_id: UUID
) -> List[CourseTutor]:
    """
    Get all assignments for a specific course.
    """
    return (
        db.query(CourseTutor)
        .options(joinedload(CourseTutor.tutor))
        .filter(CourseTutor.course_id == course_id)
        .filter(CourseTutor.status == CourseTutorStatus.ACTIVE)
        .all()
    )


def bulk_create_assignments(
    db: Session,
    bulk_data: BulkTutorCourseCreate
) -> dict:
    """
    Bulk create assignments for multiple courses to one tutor.
    """
    # Verify tutor exists
    tutor = db.query(User).filter(User.id == bulk_data.tutor_id).first()
    if not tutor:
        raise ValueError("Tutor not found")
    
    if not tutor.has_role('tutor'):
        raise ValueError("User is not a tutor")

    created = []
    failed = []

    for course_id in bulk_data.course_ids:
        try:
            # Check if course exists
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                failed.append({
                    "course_id": str(course_id),
                    "error": "Course not found"
                })
                continue

            # Check if assignment already exists
            existing = db.query(CourseTutor).filter(
                CourseTutor.tutor_id == bulk_data.tutor_id,
                CourseTutor.course_id == course_id,
                CourseTutor.status != CourseTutorStatus.REVOKED
            ).first()

            if existing:
                failed.append({
                    "course_id": str(course_id),
                    "error": "Assignment already exists"
                })
                continue

            # Create assignment
            assignment = CourseTutor(
                tutor_id=bulk_data.tutor_id,
                course_id=course_id,
                notes=bulk_data.notes,
                status=CourseTutorStatus.ACTIVE,
                created_at=datetime.utcnow()
            )
            db.add(assignment)
            created.append(assignment)

        except Exception as e:
            failed.append({
                "course_id": str(course_id),
                "error": str(e)
            })

    # Commit all successful assignments
    if created:
        db.commit()
        for assignment in created:
            db.refresh(assignment)

    return {
        "created": created,
        "failed": failed,
        "summary": {
            "total": len(bulk_data.course_ids),
            "successful": len(created),
            "failed": len(failed)
        }
    }


def bulk_delete_assignments(
    db: Session,
    assignment_ids: List[UUID]
) -> dict:
    """
    Bulk delete assignments.
    """
    deleted = 0
    failed = []

    for assignment_id in assignment_ids:
        try:
            assignment = db.query(CourseTutor).filter(
                CourseTutor.id == assignment_id
            ).first()

            if not assignment:
                failed.append({
                    "assignment_id": str(assignment_id),
                    "error": "Assignment not found"
                })
                continue

            db.delete(assignment)
            deleted += 1

        except Exception as e:
            failed.append({
                "assignment_id": str(assignment_id),
                "error": str(e)
            })

    # Commit all deletions
    if deleted > 0:
        db.commit()

    return {
        "deleted": deleted,
        "failed": failed
    }


def reassign_course(
    db: Session,
    assignment_id: UUID,
    new_tutor_id: UUID,
    reason: Optional[str] = None
) -> CourseTutor:
    """
    Reassign a course from one tutor to another.
    """
    # Get the existing assignment
    old_assignment = db.query(CourseTutor).filter(
        CourseTutor.id == assignment_id
    ).first()

    if not old_assignment:
        raise ValueError("Assignment not found")

    # Verify new tutor exists
    new_tutor = db.query(User).filter(User.id == new_tutor_id).first()
    if not new_tutor:
        raise ValueError("New tutor not found")
    
    if not new_tutor.has_role('tutor'):
        raise ValueError("User is not a tutor")

    # Check if new tutor already assigned to this course
    existing = db.query(CourseTutor).filter(
        CourseTutor.tutor_id == new_tutor_id,
        CourseTutor.course_id == old_assignment.course_id,
        CourseTutor.status != CourseTutorStatus.REVOKED
    ).first()

    if existing:
        raise ValueError("New tutor is already assigned to this course")

    # Revoke old assignment
    old_assignment.status = CourseTutorStatus.REVOKED
    old_assignment.revoked_at = datetime.utcnow()

    # Create new assignment
    new_assignment = CourseTutor(
        tutor_id=new_tutor_id,
        course_id=old_assignment.course_id,
        notes=reason or f"Reassigned from tutor {old_assignment.tutor_id}",
        status=CourseTutorStatus.ACTIVE,
        created_at=datetime.utcnow()
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return new_assignment
