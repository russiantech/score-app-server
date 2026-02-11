# def serialize_lesson(lesson):
#     return {
#         "id": lesson.id,
#         "title": lesson.title,
#         "order": lesson.order,
#         "attendance_count": getattr(lesson, "attendance_count", 0),
#         "present_count": getattr(lesson, "present_count", 0),
#         "attendance_rate": getattr(lesson, "attendance_rate", 0),
#     }

def serialize_lesson(lesson):
    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "order": lesson.order,
        "status": lesson.status,          #  THIS
        "date": lesson.date,
        "duration": lesson.duration,
        "attendance_count": getattr(lesson, "attendance_count", 0),
        "present_count": getattr(lesson, "present_count", 0),
        "attendance_rate": getattr(lesson, "attendance_rate", 0),
    }


def serialize_module(module):
    lessons = module.lessons or []

    return {
        "id": module.id,
        "title": module.title,
        "order": module.order,
        "lessons_count": len(lessons),
        "lessons": [serialize_lesson(l) for l in lessons],
    }


def serialize_course(course):
    return {
        "id": course.id,
        "title": course.title,
        "modules": [
            serialize_module(m) for m in (course.modules or [])
        ],
    }
