# ============================================================================
# Performance Export Service
# FILE: app/services/export_service.py
# ============================================================================

from uuid import UUID
from typing import Dict, Any, List
from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from sqlalchemy.orm import Session
from app.services.score_service import get_student_performance_summary
from app.services.attendance_service import get_student_attendance_summary


def generate_performance_pdf(
    db: Session,
    student_id: UUID,
    course_id: UUID = None
) -> BytesIO:
    """
    Generate comprehensive PDF performance report for a student.
    """
    # Get data
    performance = get_student_performance_summary(db, student_id, course_id)
    attendance = get_student_attendance_summary(db, student_id, course_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("Academic Performance Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Student Info
    story.append(Paragraph(f"Student ID: {student_id}", styles['Normal']))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary Section
    story.append(Paragraph("Performance Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Courses', str(performance['total_courses'])],
        ['Total Assessments', str(sum(c['total_assessments'] for c in performance['courses']))],
        ['Overall Average', f"{sum(c['overall_average'] for c in performance['courses']) / len(performance['courses']):.1f}%" if performance['courses'] else '0%'],
        ['Attendance Rate', f"{attendance.get('attendance_rate', 0)}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Course Details
    for course_data in performance['courses']:
        story.append(PageBreak())
        story.append(Paragraph(f"Course: {course_data['course']['title']}", heading_style))
        story.append(Paragraph(f"Code: {course_data['course']['code']}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Course summary
        course_summary = [
            ['Overall Average', f"{course_data['overall_average']}%"],
            ['Overall Grade', course_data['overall_grade']],
            ['Total Assessments', str(course_data['total_assessments'])]
        ]
        
        for label, value in course_summary:
            story.append(Paragraph(f"<b>{label}:</b> {value}", styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Lesson Scores
        if course_data['lesson_scores']:
            story.append(Paragraph("Lesson Assessments", heading_style))
            
            lesson_data = [['Type', 'Title', 'Score', 'Grade', 'Date']]
            for score in course_data['lesson_scores']:
                lesson_data.append([
                    score['type'].capitalize(),
                    score['title'],
                    f"{score['score']}/{score['max_score']} ({score['percentage']}%)",
                    score['grade'],
                    datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d')
                ])
            
            lesson_table = Table(lesson_data, colWidths=[1*inch, 2*inch, 1.5*inch, 0.8*inch, 1*inch])
            lesson_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(lesson_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Module Exams
        if course_data['module_scores']:
            story.append(Paragraph("Module Exams", heading_style))
            
            module_data = [['Title', 'Score', 'Grade', 'Date']]
            for score in course_data['module_scores']:
                module_data.append([
                    score['title'],
                    f"{score['score']}/{score['max_score']} ({score['percentage']}%)",
                    score['grade'],
                    datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d')
                ])
            
            module_table = Table(module_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 1*inch])
            module_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(module_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Course Projects
        if course_data['course_scores']:
            story.append(Paragraph("Course Projects", heading_style))
            
            project_data = [['Title', 'Score', 'Grade', 'Date']]
            for score in course_data['course_scores']:
                project_data.append([
                    score['title'],
                    f"{score['score']}/{score['max_score']} ({score['percentage']}%)",
                    score['grade'],
                    datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d')
                ])
            
            project_table = Table(project_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 1*inch])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9C27B0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(project_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_performance_excel(
    db: Session,
    student_id: UUID,
    course_id: UUID = None
) -> BytesIO:
    """
    Generate Excel workbook with detailed performance data.
    """
    # Get data
    performance = get_student_performance_summary(db, student_id, course_id)
    attendance = get_student_attendance_summary(db, student_id, course_id)
    
    # Create Excel writer
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        
        # Summary Sheet
        summary_data = {
            'Metric': [
                'Student ID',
                'Report Date',
                'Total Courses',
                'Total Assessments',
                'Overall Average',
                'Attendance Rate'
            ],
            'Value': [
                str(student_id),
                datetime.now().strftime('%Y-%m-%d'),
                performance['total_courses'],
                sum(c['total_assessments'] for c in performance['courses']),
                f"{sum(c['overall_average'] for c in performance['courses']) / len(performance['courses']):.2f}%" if performance['courses'] else '0%',
                f"{attendance.get('attendance_rate', 0)}%"
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Course Overview Sheet
        course_overview = []
        for course_data in performance['courses']:
            course_overview.append({
                'Course Code': course_data['course']['code'],
                'Course Title': course_data['course']['title'],
                'Overall Average': f"{course_data['overall_average']}%",
                'Grade': course_data['overall_grade'],
                'Lesson Assessments': len(course_data['lesson_scores']),
                'Module Exams': len(course_data['module_scores']),
                'Projects': len(course_data['course_scores'])
            })
        
        pd.DataFrame(course_overview).to_excel(writer, sheet_name='Course Overview', index=False)
        
        # Detailed Scores per Course
        for course_data in performance['courses']:
            sheet_name = course_data['course']['code'][:31]  # Excel sheet name limit
            
            all_scores = []
            
            # Add lesson scores
            for score in course_data['lesson_scores']:
                all_scores.append({
                    'Category': 'Lesson',
                    'Type': score['type'].capitalize(),
                    'Title': score['title'],
                    'Score': score['score'],
                    'Max Score': score['max_score'],
                    'Percentage': f"{score['percentage']}%",
                    'Grade': score['grade'],
                    'Date': datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d'),
                    'Remarks': score.get('remarks', '')
                })
            
            # Add module scores
            for score in course_data['module_scores']:
                all_scores.append({
                    'Category': 'Module',
                    'Type': 'Exam',
                    'Title': score['title'],
                    'Score': score['score'],
                    'Max Score': score['max_score'],
                    'Percentage': f"{score['percentage']}%",
                    'Grade': score['grade'],
                    'Date': datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d'),
                    'Remarks': score.get('remarks', '')
                })
            
            # Add course scores
            for score in course_data['course_scores']:
                all_scores.append({
                    'Category': 'Course',
                    'Type': 'Project',
                    'Title': score['title'],
                    'Score': score['score'],
                    'Max Score': score['max_score'],
                    'Percentage': f"{score['percentage']}%",
                    'Grade': score['grade'],
                    'Date': datetime.fromisoformat(score['recorded_date']).strftime('%Y-%m-%d'),
                    'Remarks': score.get('remarks', '')
                })
            
            if all_scores:
                pd.DataFrame(all_scores).to_excel(writer, sheet_name=sheet_name, index=False)
    
    buffer.seek(0)
    return buffer


# ============================================================================
# API Route Implementation
# ============================================================================

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.deps.users import get_current_user, get_db

router = APIRouter()

@router.get("/students/{student_id}/performance/export/pdf")
async def export_performance_pdf(
    student_id: UUID,
    course_id: UUID = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export student performance as PDF"""
    # Permission check
    if current_user.id != student_id and not current_user.has_role('admin', 'parent'):
        raise HTTPException(403, "Access denied")
    
    pdf_buffer = generate_performance_pdf(db, student_id, course_id)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=performance_report_{student_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )


@router.get("/students/{student_id}/performance/export/excel")
async def export_performance_excel(
    student_id: UUID,
    course_id: UUID = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export student performance as Excel"""
    # Permission check
    if current_user.id != student_id and not current_user.has_role('admin', 'parent'):
        raise HTTPException(403, "Access denied")
    
    excel_buffer = generate_performance_excel(db, student_id, course_id)
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=performance_report_{student_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )
