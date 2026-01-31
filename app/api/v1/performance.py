# # app/api/v1/performance.py
# """
# Student performance API endpoints.
# """

# from fastapi import APIRouter, Depends, Query, Request, Response
# from sqlalchemy.orm import Session
# from uuid import UUID

# from app.api.deps.users import get_db, get_current_user
# from app.services import performance_service
# from app.models.user import User
# from app.utils.responses import api_response

# router = APIRouter()


# @router.get(
#     "/students/{student_id}",
#     summary="Get student performance"
# )
# def get_student_performance(
#     request: Request,
#     student_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get comprehensive performance data for a student.
    
#     Returns:
#     - Summary statistics
#     - Performance by course
#     - Attendance summary
#     - Performance trends
#     """
#     # Authorization: students can only view their own data
#     # TODO: Add admin/tutor/parent permissions
#     if str(current_user.id) != str(student_id):
#         # Allow admins and tutors to view any student
#         if not any(role.name in ['admin', 'tutor'] for role in current_user.roles):
#             from fastapi import HTTPException
#             raise HTTPException(status_code=403, detail="Not authorized")
    
#     performance = performance_service.get_student_performance(db, student_id)
    
#     return api_response(
#         success=True,
#         message="Performance data retrieved successfully",
#         data=performance,
#         path=str(request.url.path)
#     )


# @router.get(
#     "/students/{student_id}/courses/{course_id}",
#     summary="Get course-specific performance"
# )
# def get_course_performance(
#     request: Request,
#     student_id: UUID,
#     course_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get detailed performance for a specific course.
    
#     Returns granular breakdown of:
#     - Lesson scores
#     - Module exam scores
#     - Course project scores
#     """
#     # Authorization check
#     if str(current_user.id) != str(student_id):
#         if not any(role.name in ['admin', 'tutor'] for role in current_user.roles):
#             from fastapi import HTTPException
#             raise HTTPException(status_code=403, detail="Not authorized")
    
#     performance = performance_service.get_course_performance(
#         db, student_id, course_id
#     )
    
#     return api_response(
#         success=True,
#         message="Course performance retrieved successfully",
#         data=performance,
#         path=str(request.url.path)
#     )


# @router.get(
#     "/students/{student_id}/export",
#     summary="Export performance report"
# )
# def export_performance_report(
#     request: Request,
#     student_id: UUID,
#     format: str = Query("pdf", regex="^(pdf|excel)$"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Generate and download performance report.
    
#     Args:
#         format: 'pdf' or 'excel'
    
#     Returns:
#         Binary file download
#     """
#     # Authorization check
#     if str(current_user.id) != str(student_id):
#         if not any(role.name in ['admin', 'tutor'] for role in current_user.roles):
#             from fastapi import HTTPException
#             raise HTTPException(status_code=403, detail="Not authorized")
    
#     report_data = performance_service.export_performance_report(
#         db, student_id, format
#     )
    
#     # Set appropriate headers for file download
#     content_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     filename = f"performance_report.{format}"
    
#     return Response(
#         content=report_data,
#         media_type=content_type,
#         headers={
#             "Content-Disposition": f"attachment; filename={filename}"
#         }
#     )


"""
Performance API router - Endpoints for student performance and exports
"""
import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Literal
from uuid import UUID
from io import BytesIO

from app.services import performance_service
from app.api.deps.users import get_current_user, get_db
from app.models.user import User

router = APIRouter()


def can_view_student_performance(
    current_user: User,
    student_id: UUID
) -> bool:
    """
    Authorization rules:
    - Student → can view ONLY their own data
    - Admin / Tutor → can view ANY student
    """
    # Self access (student or anyone)
    if str(current_user.id) == str(student_id):
        return True

    # Elevated roles
    return any(
        role.name in ["admin", "tutor"]
        for role in current_user.roles
    )


@router.get("/students/{student_id}")
def get_student_performance(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive performance data for a student.

    Access:
    - Students: own performance only
    - Admins/Tutors: any student
    """
    if not can_view_student_performance(current_user, student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student's performance"
        )

    try:
        return performance_service.get_student_performance(
            db=db,
            student_id=student_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching performance data: {str(e)}"
        )


# @router.get("/students/{student_id}/export/{format}")
# def export_performance_report(
#     student_id: UUID,
#     format: Literal["pdf", "excel"],
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Export student performance report (PDF or Excel).

#     Access:
#     - Students: own report only
#     - Admins/Tutors: any student
#     """
#     if not can_view_student_performance(current_user, student_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to export this student's performance"
#         )

#     try:
#         if format == "pdf":
#             report_data = performance_service.export_performance_pdf(
#                 db, student_id
#             )
#             media_type = "application/pdf"
#             filename = f"performance_report_{student_id}.pdf"

#         else:  # excel
#             report_data = performance_service.export_performance_excel(
#                 db, student_id
#             )
#             media_type = (
#                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )
#             filename = f"performance_report_{student_id}.xlsx"

#         return StreamingResponse(
#             BytesIO(report_data),
#             media_type=media_type,
#             headers={
#                 "Content-Disposition": f"attachment; filename={filename}"
#             }
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error generating report: {str(e)}"
#         )


# v2
@router.get("/students/{student_id}/export/{format}")
def export_performance_report(
    student_id: UUID,
    format: Literal["pdf", "excel"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export student performance report (PDF or Excel).

    Access:
    - Students: own report only
    - Admins/Tutors: any student
    """
    if not can_view_student_performance(current_user, student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this student's performance"
        )

    try:
        # 🔹 Fetch student
        student = (
            db.query(User)
            .filter(User.id == student_id)
            .first()
        )

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

        # 🔹 Build safe student name
        full_name = f"{student.names}"
        safe_name = re.sub(r"[^A-Za-z0-9_]", "", full_name)

        today = date.today().isoformat()

        if format == "pdf":
            report_data = performance_service.export_performance_pdf(
                db, student_id
            )
            media_type = "application/pdf"
            extension = "pdf"

        else:  # excel
            report_data = performance_service.export_performance_excel(
                db, student_id
            )
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            extension = "xlsx"

        filename = (
            f"Performance_Report_{safe_name}_{today}.{extension}"
        )

        return StreamingResponse(
            BytesIO(report_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )

