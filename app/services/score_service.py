# app/services/score_service.py
# Complete Score Service with proper validation and error handling

from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.scores import Score, AssessmentScope
# from app.models.score import ScoreColumn
from app.models.scores import AssessmentScope, AssessmentType, Score, ScoreColumn
from app.models.modules import Module
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.modules import Module
from app.models.enrollment import Enrollment
# from app.models.assessment import AssessmentType
from app.models.user import User


def calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage"""
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 75: return "B+"
    if percentage >= 70: return "B"
    if percentage >= 65: return "C+"
    if percentage >= 60: return "C"
    if percentage >= 55: return "D+"
    if percentage >= 50: return "D"
    return "F"


# ============================================================================
# LESSON LEVEL SCORING
# ============================================================================

def get_lesson_scores_with_students(
    db: Session,
    lesson_id: UUID
) -> Dict[str, Any]:
    """
    Get scores for a lesson with ALL enrolled students.
    Auto-initializes columns if none exist.
    """
    # Fetch lesson
    lesson = db.query(Lesson).options(
        joinedload(Lesson.module)
    ).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    module = lesson.module
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Get or create score columns
    columns = db.query(ScoreColumn).filter(
        ScoreColumn.lesson_id == lesson_id,
        ScoreColumn.is_active == True
    ).order_by(ScoreColumn.order).all()
    
    # Initialize default columns if none exist
    if not columns:
        default_columns = [
            {
                "type": AssessmentType.HOMEWORK,
                "title": "Homework",
                "max_score": 30.0,
                "weight": 0.3,
                "order": 1
            },
            {
                "type": AssessmentType.CLASSWORK,
                "title": "Classwork",
                "max_score": 20.0,
                "weight": 0.2,
                "order": 2
            },
            {
                "type": AssessmentType.QUIZ,
                "title": "Quiz",
                "max_score": 50.0,
                "weight": 0.5,
                "order": 3
            }
        ]
        
        for col_data in default_columns:
            column = ScoreColumn(
                lesson_id=lesson_id,
                scope=AssessmentScope.LESSON,  # Add scope
                type=col_data["type"],
                title=col_data["title"],
                max_score=col_data["max_score"],
                weight=col_data["weight"],
                order=col_data["order"]
            )
            db.add(column)
            columns.append(column)
        
        db.flush()
    
    # Get all enrollments for this course
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.student)
    ).filter(
        Enrollment.course_id == module.course_id
    ).all()
    
    # Get existing scores
    existing_scores = db.query(Score).join(ScoreColumn).filter(
        ScoreColumn.lesson_id == lesson_id
    ).all()
    
    # Build score map: {enrollment_id: {column_id: score}}
    score_map: Dict[UUID, Dict[UUID, Score]] = {}
    for score in existing_scores:
        if score.enrollment_id not in score_map:
            score_map[score.enrollment_id] = {}
        score_map[score.enrollment_id][score.column_id] = score
    
    # Build student data
    students_data = []
    for enrollment in enrollments:
        student_scores = {}
        total_weighted = 0.0
        total_weight = 0.0
        
        for column in columns:
            score_record = score_map.get(enrollment.id, {}).get(column.id)
            
            if score_record:
                percentage = score_record.calculate_percentage()
                total_weighted += percentage * column.weight
                total_weight += column.weight
            
            student_scores[str(column.id)] = {
                "score": float(score_record.score) if score_record else 0.0,
                "max_score": float(column.max_score),
                "percentage": float(score_record.percentage) if score_record else 0.0,
                "remarks": score_record.notes if score_record else "",
                "score_id": str(score_record.id) if score_record else None,
                "is_recorded": score_record is not None
            }
        
        total_percentage = (total_weighted / total_weight) if total_weight > 0 else 0.0
        
        students_data.append({
            "enrollment_id": str(enrollment.id),
            "student_id": str(enrollment.student.id),
            "names": enrollment.student.names,
            "email": enrollment.student.email,
            "username": enrollment.student.username,
            "scores": student_scores,
            "total_percentage": round(total_percentage, 2),
            "grade": calculate_grade(total_percentage)
        })
    
    return {
        "lesson": {
            "id": str(lesson.id),
            "title": lesson.title,
            "module_id": str(module.id),
            "course_id": str(module.course_id)
        },
        "summary": {
            "total_students": len(students_data),
            "recorded_count": sum(
                1 for s in students_data 
                if any(score_data["is_recorded"] for score_data in s["scores"].values())
            ),
            "total_columns": len(columns)
        },
        "columns": [
            {
                "id": str(col.id),
                "type": col.type.value,
                "title": col.title,
                "description": col.description,
                "max_score": float(col.max_score),
                "weight": float(col.weight),
                "order": col.order
            }
            for col in columns
        ],
        "students": students_data
    }


def bulk_create_or_update_lesson_scores(
    db: Session,
    lesson_id: UUID,
    columns_config: List[Dict[str, Any]],
    scores_data: List[Dict[str, Any]],
    current_user: User
) -> Dict[str, Any]:
    """
    Create or update score records with flexible columns.
    Properly handles enrollment_id mapping and scope.
    """
    # Permission check
    if not (current_user.is_tutor or current_user.is_admin):
        raise HTTPException(403, "Permission denied")
    
    # Verify lesson exists
    lesson = db.query(Lesson).options(
        joinedload(Lesson.module)
    ).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    
    # Update or create columns
    column_id_map = {}  # Maps frontend column IDs to database IDs
    
    for col_config in columns_config:
        col_id = col_config.get("id")
        
        if col_id:
            # Try to update existing column
            try:
                col_uuid = UUID(col_id)
                column = db.query(ScoreColumn).filter(
                    ScoreColumn.id == col_uuid,
                    ScoreColumn.lesson_id == lesson_id
                ).first()
                
                if column:
                    column.type = AssessmentType(col_config["type"])
                    column.title = col_config["title"]
                    column.max_score = col_config["max_score"]
                    column.weight = col_config["weight"]
                    column.order = col_config.get("order", 0)
                    column_id_map[col_id] = str(column.id)
                    continue
            except (ValueError, AttributeError):
                # Not a valid UUID, treat as new
                pass
        
        # Create new column with scope
        column = ScoreColumn(
            lesson_id=lesson_id,
            scope=AssessmentScope.LESSON,  # Set scope for lesson-level columns
            type=AssessmentType(col_config["type"]),
            title=col_config["title"],
            max_score=col_config["max_score"],
            weight=col_config["weight"],
            order=col_config.get("order", 0)
        )
        db.add(column)
        db.flush()
        
        # Map frontend ID to database ID
        temp_id = col_config.get("id", f"temp_{column.id}")
        column_id_map[temp_id] = str(column.id)
    
    # Process scores
    created = 0
    updated = 0
    errors = []
    
    for student_data in scores_data:
        # Get enrollment_id (prioritize enrollment_id, fallback to student_id)
        enrollment_id = student_data.get("enrollment_id")
        
        if not enrollment_id:
            # If no enrollment_id, try to find it from student_id
            student_id = student_data.get("student_id")
            if student_id:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.student_id == UUID(student_id),
                    Enrollment.course_id == lesson.module.course_id
                ).first()
                
                if enrollment:
                    enrollment_id = str(enrollment.id)
                else:
                    errors.append(f"No enrollment found for student {student_id}")
                    continue
            else:
                errors.append("Missing both enrollment_id and student_id")
                continue
        
        try:
            enrollment_uuid = UUID(enrollment_id)
        except ValueError:
            errors.append(f"Invalid enrollment_id: {enrollment_id}")
            continue
        
        # Process each column score
        for col_score in student_data.get("column_scores", []):
            frontend_col_id = col_score["column_id"]
            
            # Map to database column ID
            db_col_id_str = column_id_map.get(frontend_col_id, frontend_col_id)
            
            try:
                db_col_id = UUID(db_col_id_str)
            except ValueError:
                errors.append(f"Invalid column_id: {frontend_col_id}")
                continue
            
            score_value = float(col_score.get("score", 0))
            remarks = col_score.get("remarks", "")
            
            # Get column for max_score
            column = db.query(ScoreColumn).filter(
                ScoreColumn.id == db_col_id
            ).first()
            
            if not column:
                errors.append(f"Column not found: {db_col_id}")
                continue
            
            # Calculate percentage and grade
            percentage = (score_value / column.max_score) * 100 if column.max_score > 0 else 0
            grade = calculate_grade(percentage)
            
            # Check if score exists
            existing = db.query(Score).filter(
                and_(
                    Score.enrollment_id == enrollment_uuid,
                    Score.column_id == db_col_id
                )
            ).first()
            
            if existing:
                # Update existing
                existing.score = score_value
                existing.max_score = column.max_score
                existing.percentage = percentage
                existing.grade = grade
                existing.notes = remarks
                existing.recorder_id = current_user.id
                updated += 1
            else:
                # Create new
                score = Score(
                    enrollment_id=enrollment_uuid,
                    column_id=db_col_id,
                    recorder_id=current_user.id,
                    score=score_value,
                    max_score=column.max_score,
                    percentage=percentage,
                    grade=grade,
                    notes=remarks
                )
                db.add(score)
                created += 1
    
    db.commit()
    
    result = {
        "lesson_id": str(lesson_id),
        "created": created,
        "updated": updated,
        "total_processed": created + updated,
        "columns_configured": len(columns_config)
    }
    
    if errors:
        result["errors"] = errors
    
    return result


# ============================================================================
# MODULE LEVEL SCORING
# ============================================================================

def get_module_scores_with_students(
    db: Session,
    module_id: UUID
) -> Dict[str, Any]:
    """
    Get exam scores for a module with ALL enrolled students.
    Auto-initializes module exam column if none exists.
    """
    # Fetch module
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Get or create score column for module exam
    columns = db.query(ScoreColumn).filter(
        ScoreColumn.module_id == module_id,
        ScoreColumn.is_active == True
    ).order_by(ScoreColumn.order).all()
    
    # Initialize default module exam column if none exist
    if not columns:
        column = ScoreColumn(
            module_id=module_id,
            scope=AssessmentScope.MODULE,
            type=AssessmentType.EXAM,
            title=f"{module.title} - Exam",
            max_score=100.0,
            weight=1.0,
            order=1
        )
        db.add(column)
        db.flush()
        columns = [column]
    
    # Get all enrollments for this course
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.student)
    ).filter(
        Enrollment.course_id == module.course_id
    ).all()
    
    # Get existing scores
    existing_scores = db.query(Score).join(ScoreColumn).filter(
        ScoreColumn.module_id == module_id
    ).all()
    
    # Build score map: {enrollment_id: score}
    score_map: Dict[UUID, Score] = {}
    for score in existing_scores:
        score_map[score.enrollment_id] = score
    
    # Build student data
    students_data = []
    for enrollment in enrollments:
        score_record = score_map.get(enrollment.id)
        column = columns[0]  # Module typically has one exam
        
        students_data.append({
            "enrollment_id": str(enrollment.id),
            "student_id": str(enrollment.student.id),
            "names": enrollment.student.names,
            "email": enrollment.student.email,
            "username": enrollment.student.username,
            "exam_score": float(score_record.score) if score_record else 0.0,
            "max_score": float(column.max_score),
            "percentage": float(score_record.percentage) if score_record else 0.0,
            "grade": score_record.grade if score_record else None,
            "remarks": score_record.notes if score_record else "",
            "score_id": str(score_record.id) if score_record else None,
            "is_recorded": score_record is not None
        })
    
    return {
        "module": {
            "id": str(module.id),
            "title": module.title,
            "course_id": str(module.course_id)
        },
        "summary": {
            "total_students": len(students_data),
            "recorded_count": sum(1 for s in students_data if s["is_recorded"]),
        },
        "students": students_data
    }


def bulk_create_or_update_module_scores(
    db: Session,
    module_id: UUID,
    columns_config: List[Dict[str, Any]],
    scores_data: List[Dict[str, Any]],
    current_user: User
) -> Dict[str, Any]:
    """
    Create or update module exam scores.
    """
    # Permission check
    if not (current_user.is_tutor or current_user.is_admin):
        raise HTTPException(403, "Permission denied")
    
    # Verify module exists
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(404, "Module not found")
    
    # Update or create columns
    column_id_map = {}
    
    for col_config in columns_config:
        col_id = col_config.get("id")
        
        if col_id and col_id != 'module_exam':
            # Try to update existing column
            try:
                col_uuid = UUID(col_id)
                column = db.query(ScoreColumn).filter(
                    ScoreColumn.id == col_uuid,
                    ScoreColumn.module_id == module_id
                ).first()
                
                if column:
                    column.type = AssessmentType(col_config["type"])
                    column.title = col_config["title"]
                    column.max_score = col_config["max_score"]
                    column.weight = col_config["weight"]
                    column.order = col_config.get("order", 0)
                    column_id_map[col_id] = str(column.id)
                    continue
            except (ValueError, AttributeError):
                pass
        
        # Create new column
        column = ScoreColumn(
            module_id=module_id,
            scope=AssessmentScope.MODULE,
            type=AssessmentType(col_config.get("type", "exam")),
            title=col_config["title"],
            max_score=col_config["max_score"],
            weight=col_config["weight"],
            order=col_config.get("order", 0)
        )
        db.add(column)
        db.flush()
        
        temp_id = col_config.get("id", f"temp_{column.id}")
        column_id_map[temp_id] = str(column.id)
    
    # Process scores (same logic as lesson scores)
    created = 0
    updated = 0
    errors = []
    
    for student_data in scores_data:
        enrollment_id = student_data.get("enrollment_id")
        
        if not enrollment_id:
            student_id = student_data.get("student_id")
            if student_id:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.student_id == UUID(student_id),
                    Enrollment.course_id == module.course_id
                ).first()
                
                if enrollment:
                    enrollment_id = str(enrollment.id)
                else:
                    errors.append(f"No enrollment found for student {student_id}")
                    continue
            else:
                errors.append("Missing both enrollment_id and student_id")
                continue
        
        try:
            enrollment_uuid = UUID(enrollment_id)
        except ValueError:
            errors.append(f"Invalid enrollment_id: {enrollment_id}")
            continue
        
        for col_score in student_data.get("column_scores", []):
            frontend_col_id = col_score["column_id"]
            db_col_id_str = column_id_map.get(frontend_col_id, frontend_col_id)
            
            try:
                db_col_id = UUID(db_col_id_str)
            except ValueError:
                errors.append(f"Invalid column_id: {frontend_col_id}")
                continue
            
            score_value = float(col_score.get("score", 0))
            remarks = col_score.get("remarks", "")
            
            column = db.query(ScoreColumn).filter(
                ScoreColumn.id == db_col_id
            ).first()
            
            if not column:
                errors.append(f"Column not found: {db_col_id}")
                continue
            
            percentage = (score_value / column.max_score) * 100 if column.max_score > 0 else 0
            grade = calculate_grade(percentage)
            
            existing = db.query(Score).filter(
                and_(
                    Score.enrollment_id == enrollment_uuid,
                    Score.column_id == db_col_id
                )
            ).first()
            
            if existing:
                existing.score = score_value
                existing.max_score = column.max_score
                existing.percentage = percentage
                existing.grade = grade
                existing.notes = remarks
                existing.recorder_id = current_user.id
                updated += 1
            else:
                score = Score(
                    enrollment_id=enrollment_uuid,
                    column_id=db_col_id,
                    recorder_id=current_user.id,
                    score=score_value,
                    max_score=column.max_score,
                    percentage=percentage,
                    grade=grade,
                    notes=remarks
                )
                db.add(score)
                created += 1
    
    db.commit()
    
    result = {
        "module_id": str(module_id),
        "created": created,
        "updated": updated,
        "total_processed": created + updated
    }
    
    if errors:
        result["errors"] = errors
    
    return result


# ============================================================================
# COURSE LEVEL SCORING
# ============================================================================

def get_course_scores_with_students(
    db: Session,
    course_id: UUID
) -> Dict[str, Any]:
    """
    Get project scores for a course with ALL enrolled students.
    Supports multiple rubric items.
    """
    # Fetch course
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get or create score columns for course project
    columns = db.query(ScoreColumn).filter(
        ScoreColumn.course_id == course_id,
        ScoreColumn.is_active == True
    ).order_by(ScoreColumn.order).all()
    
    # Initialize default project rubric if none exist
    if not columns:
        default_rubric = [
            {"title": "Requirements", "max_score": 25, "weight": 0.25, "order": 1},
            {"title": "Implementation", "max_score": 35, "weight": 0.35, "order": 2},
            {"title": "Documentation", "max_score": 20, "weight": 0.20, "order": 3},
            {"title": "Presentation", "max_score": 20, "weight": 0.20, "order": 4}
        ]
        
        for rubric_item in default_rubric:
            column = ScoreColumn(
                course_id=course_id,
                scope=AssessmentScope.COURSE,
                type=AssessmentType.PROJECT,
                title=rubric_item["title"],
                max_score=rubric_item["max_score"],
                weight=rubric_item["weight"],
                order=rubric_item["order"]
            )
            db.add(column)
            columns.append(column)
        
        db.flush()
    
    # Get all enrollments for this course
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.student)
    ).filter(
        Enrollment.course_id == course_id
    ).all()
    
    # Get existing scores
    existing_scores = db.query(Score).join(ScoreColumn).filter(
        ScoreColumn.course_id == course_id
    ).all()
    
    # Build score map: {enrollment_id: {column_id: score}}
    score_map: Dict[UUID, Dict[UUID, Score]] = {}
    for score in existing_scores:
        if score.enrollment_id not in score_map:
            score_map[score.enrollment_id] = {}
        score_map[score.enrollment_id][score.column_id] = score
    
    # Build student data
    students_data = []
    for enrollment in enrollments:
        rubric_scores = {}
        total_score = 0
        max_total = 0
        
        for column in columns:
            score_record = score_map.get(enrollment.id, {}).get(column.id)
            score_value = float(score_record.score) if score_record else 0.0
            
            rubric_scores[str(column.id)] = score_value
            total_score += score_value
            max_total += column.max_score
        
        percentage = (total_score / max_total * 100) if max_total > 0 else 0
        
        students_data.append({
            "enrollment_id": str(enrollment.id),
            "student_id": str(enrollment.student.id),
            "names": enrollment.student.names,
            "email": enrollment.student.email,
            "username": enrollment.student.username,
            "rubric_scores": rubric_scores,
            "total_score": total_score,
            "max_score": max_total,
            "percentage": round(percentage, 2),
            "grade": calculate_grade(percentage),
            "remarks": "",
            "score_id": None,
            "is_recorded": any(
                enrollment.id in score_map and col.id in score_map[enrollment.id] 
                for col in columns
            )
        })
    
    return {
        "course": {
            "id": str(course.id),
            "title": course.title,
            "code": course.code
        },
        "summary": {
            "total_students": len(students_data),
            "recorded_count": sum(1 for s in students_data if s["is_recorded"]),
        },
        "rubric_items": [
            {
                "id": str(col.id),
                "title": col.title,
                "max_score": float(col.max_score),
                "weight": float(col.weight)
            }
            for col in columns
        ],
        "students": students_data
    }


def bulk_create_or_update_course_scores(
    db: Session,
    course_id: UUID,
    columns_config: List[Dict[str, Any]],
    scores_data: List[Dict[str, Any]],
    current_user: User
) -> Dict[str, Any]:
    """
    Create or update course project scores.
    Supports flexible rubric configuration.
    """
    # Permission check
    if not (current_user.is_tutor or current_user.is_admin):
        raise HTTPException(403, "Permission denied")
    
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(404, "Course not found")
    
    # Process columns (same logic as lesson/module)
    column_id_map = {}
    
    for col_config in columns_config:
        col_id = col_config.get("id")
        
        if col_id:
            try:
                col_uuid = UUID(col_id)
                column = db.query(ScoreColumn).filter(
                    ScoreColumn.id == col_uuid,
                    ScoreColumn.course_id == course_id
                ).first()
                
                if column:
                    column.type = AssessmentType(col_config.get("type", "project"))
                    column.title = col_config["title"]
                    column.max_score = col_config["max_score"]
                    column.weight = col_config["weight"]
                    column.order = col_config.get("order", 0)
                    column_id_map[col_id] = str(column.id)
                    continue
            except (ValueError, AttributeError):
                pass
        
        # Create new column
        column = ScoreColumn(
            course_id=course_id,
            scope=AssessmentScope.COURSE,
            type=AssessmentType.PROJECT,
            title=col_config["title"],
            max_score=col_config["max_score"],
            weight=col_config["weight"],
            order=col_config.get("order", 0)
        )
        db.add(column)
        db.flush()
        
        temp_id = col_config.get("id", f"temp_{column.id}")
        column_id_map[temp_id] = str(column.id)
    
    # Process scores (same logic as before)
    created = 0
    updated = 0
    errors = []
    
    for student_data in scores_data:
        enrollment_id = student_data.get("enrollment_id") or student_data.get("student_id")
        
        if not enrollment_id:
            continue
        
        try:
            enrollment_uuid = UUID(enrollment_id)
        except ValueError:
            continue
        
        for col_score in student_data.get("column_scores", []):
            frontend_col_id = col_score["column_id"]
            db_col_id_str = column_id_map.get(frontend_col_id, frontend_col_id)
            
            try:
                db_col_id = UUID(db_col_id_str)
            except ValueError:
                continue
            
            score_value = float(col_score.get("score", 0))
            remarks = col_score.get("remarks", "")
            
            column = db.query(ScoreColumn).filter(
                ScoreColumn.id == db_col_id
            ).first()
            
            if not column:
                continue
            
            percentage = (score_value / column.max_score) * 100 if column.max_score > 0 else 0
            grade = calculate_grade(percentage)
            
            existing = db.query(Score).filter(
                and_(
                    Score.enrollment_id == enrollment_uuid,
                    Score.column_id == db_col_id
                )
            ).first()
            
            if existing:
                existing.score = score_value
                existing.max_score = column.max_score
                existing.percentage = percentage
                existing.grade = grade
                existing.notes = remarks
                existing.recorder_id = current_user.id
                updated += 1
            else:
                score = Score(
                    enrollment_id=enrollment_uuid,
                    column_id=db_col_id,
                    recorder_id=current_user.id,
                    score=score_value,
                    max_score=column.max_score,
                    percentage=percentage,
                    grade=grade,
                    notes=remarks
                )
                db.add(score)
                created += 1
    
    db.commit()
    
    return {
        "course_id": str(course_id),
        "created": created,
        "updated": updated,
        "total_processed": created + updated
    }


def calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage"""
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 75: return "B+"
    if percentage >= 70: return "B"
    if percentage >= 65: return "C+"
    if percentage >= 60: return "C"
    if percentage >= 55: return "D+"
    if percentage >= 50: return "D"
    return "F"

