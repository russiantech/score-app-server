
# v2 - organization
# ============================================================================
# app/api/v1/router.py
# API v1 Main Router
# ============================================================================

from fastapi import APIRouter
from app.core.config import get_app_config

# v1 feature routers
from app.api.v1 import (
    auth,
    users,
    roles,
    admin,
    students,
    parents,
    courses,
    modules,
    lessons,
    assessments,
    scores,
    enrollments,
    attendance,
    tutors,
    performance,
)

# Role-based routers
# from app.api.v1.roles import (
#     tutor,
#     student,
#     parent,
# )

# ----------------------------------------------------------------------------
# API Config
# ----------------------------------------------------------------------------

config = get_app_config()

v1_router = APIRouter(
    prefix=config.general_config.api_prefix,
    # tags=["API v1"],
)

# ----------------------------------------------------------------------------
# Authentication & Core Users
# ----------------------------------------------------------------------------

v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1_router.include_router(users.router, prefix="/users", tags=["v1 • Users"])
v1_router.include_router(roles.router, prefix="/roles", tags=["Roles"])

# ----------------------------------------------------------------------------
# Admin Routes
# ----------------------------------------------------------------------------

v1_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# ----------------------------------------------------------------------------
# Academic Resources
# ----------------------------------------------------------------------------

v1_router.include_router(courses.router, prefix="/courses", tags=["v1 • Courses"])
v1_router.include_router(modules.router, prefix="/modules", tags=["Modules"])
v1_router.include_router(lessons.router, prefix="/lessons", tags=["Lessons"])
v1_router.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])

# ----------------------------------------------------------------------------
# Enrollment, Scores & Attendance
# ----------------------------------------------------------------------------

v1_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
v1_router.include_router(scores.router, prefix="/scores", tags=["Scores"])
v1_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])

# ----------------------------------------------------------------------------
# User-Type Resources
# ----------------------------------------------------------------------------

v1_router.include_router(tutors.assign.router)
v1_router.include_router(tutors.dashboard.router)

# v1_router.include_router(tutors.dashboard.router, prefix="/tutors", tags=["Tutor"])
v1_router.include_router(students.router, prefix="/students", tags=["Students"])
v1_router.include_router(parents.router, prefix="/parents", tags=["Parents"])

# ----------------------------------------------------------------------------
# Role-Specific Dashboards & Actions
# ----------------------------------------------------------------------------
v1_router.include_router(performance.router, prefix="/performance", tags=["Performance"])

# v1_router.include_router(tutor.router, prefix="/tutor", tags=["Tutor"])
# v1_router.include_router(student.router, prefix="/student", tags=["Student"])
# v1_router.include_router(parent.router, prefix="/parent", tags=["Parent"])
