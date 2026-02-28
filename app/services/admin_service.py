# v2
# ============================================================================
# SERVICES - Part 7: Admin Service (CORRECTED)
# FILE: app/services/admin_service.py
# ============================================================================

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, select
from datetime import datetime, timedelta

from app.schemas.admin import AdminStatsOut, DashboardOverviewOut

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.modules import Module
from app.models.scores import Score
from app.models.user import User
from app.models.parents import ParentChildren, LinkStatus

def get_statistics(db: Session) -> AdminStatsOut:
    """Get comprehensive admin statistics"""

    # ---------------------------
    # Users
    # ---------------------------
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()

    # ---------------------------
    # Roles
    # ---------------------------
    total_students = db.query(User).filter(
        User.roles.any(name="student")
    ).count()

    total_tutors = db.query(User).filter(
        User.roles.any(name="tutor")
    ).count()

    total_parents = db.query(User).filter(
        User.roles.any(name="parent")
    ).count()

    total_admins = db.query(User).filter(
        User.roles.any(name="admin")
    ).count()

    # ---------------------------
    # Active by role
    # ---------------------------
    active_students = db.query(User).filter(
        User.roles.any(name="student"),
        User.is_active.is_(True)
    ).count()

    active_tutors = db.query(User).filter(
        User.roles.any(name="tutor"),
        User.is_active.is_(True)
    ).count()

    active_parents = db.query(User).filter(
        User.roles.any(name="parent"),
        User.is_active.is_(True)
    ).count()

    # ---------------------------
    # Courses
    # ---------------------------
    total_courses = db.query(Course).count()
    active_courses = db.query(Course).filter(Course.is_active.is_(True)).count()
    inactive_courses = total_courses - active_courses

    courses_without_instructors = db.query(Course).filter(
        ~Course.tutors_assigned.any()
    ).count()

    # ---------------------------
    # Modules / Lessons
    # ---------------------------
    total_modules = db.query(Module).count()
    total_lessons = db.query(Lesson).count()

    # ---------------------------
    # Enrollments
    # ---------------------------
    total_enrollments = db.query(Enrollment).count()
    seven_days_ago = datetime.now() - timedelta(days=7)

    recent_enrollments = db.query(Enrollment).filter(
        Enrollment.created_at >= seven_days_ago
    ).count()

    # ---------------------------
    # Assessments
    # ---------------------------
    total_assessments = db.query(Score).count()

    # ---------------------------
    # Average class size
    # ---------------------------
    avg_subquery = (
        db.query(
            Enrollment.course_id,
            func.count(Enrollment.student_id).label("student_count")
        )
        .group_by(Enrollment.course_id)
        .subquery()
    )

    avg_class_size = (
        db.query(func.avg(avg_subquery.c.student_count))
        .scalar()
        or 0
    )

    # ---------------------------
    # Students without parents (FIXED)
    # ---------------------------
    students_with_active_parents = (
        db.query(distinct(ParentChildren.child_id))
        .join(User, User.id == ParentChildren.child_id)
        .filter(
            ParentChildren.status == LinkStatus.ACTIVE,
            User.roles.any(name="student"),
        )
        .count()
    )

    students_without_parents = max(
        total_students - students_with_active_parents, 0
    )

    # ---------------------------
    # Response
    # ---------------------------
    return AdminStatsOut(
        total_users=total_users,
        active_users=active_users,
        total_courses=total_courses,
        total_modules=total_modules,
        total_lessons=total_lessons,
        total_tutors=total_tutors,
        total_students=total_students,
        total_parents=total_parents,
        total_admins=total_admins,
        active_courses=active_courses,
        inactive_courses=inactive_courses,
        active_students=active_students,
        active_tutors=active_tutors,
        active_parents=active_parents,
        inactive_parents=total_parents - active_parents,
        recent_enrollments=recent_enrollments,
        total_enrollments=total_enrollments,
        total_assessments=total_assessments,
        average_class_size=round(avg_class_size, 1),
        courses_without_tutors=courses_without_instructors,
        students_without_parents=students_without_parents,
    )


def get_recent_activities(db: Session, limit: int = 10) -> list:
    """Get recent system activities"""
    # Assuming you have an Activity model
    # If not, you might need to create one or remove this function
    # For now, return empty list
    return []

# def get_recent_activities(db: Session, limit: int = 10) -> list:
#     """Get recent system activities"""
#     activities = db.query(Activity).order_by(
#         Activity.timestamp.desc()
#     ).limit(limit).all() 
    
#     return activities

def get_dashboard_overview(db: Session) -> DashboardOverviewOut:
    """Get complete dashboard data"""
    stats = get_statistics(db)
    activities = get_recent_activities(db)
    
    return DashboardOverviewOut(
        stats=stats,
        activities=activities
    )


