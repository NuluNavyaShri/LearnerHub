from sqlalchemy.orm import Session

import models


def get_avg_rating(db: Session, course_id: int):
    ratings = db.query(models.Rating).filter(models.Rating.course_id == course_id).all()
    if not ratings:
        return 0.0, 0
    total = sum(r.stars for r in ratings)
    return round(total / len(ratings), 2), len(ratings)


def get_total_duration(course: models.Course) -> int:
    return sum(l.duration_minutes or 0 for l in course.lessons)


def get_lesson_count(course: models.Course) -> int:
    return len(course.lessons)


def get_completed_lesson_ids(db: Session, learner_id: int, course_id: int):
    rows = (
        db.query(models.LessonProgress.lesson_id)
        .filter(
            models.LessonProgress.learner_id == learner_id,
            models.LessonProgress.course_id == course_id,
        )
        .all()
    )
    return [r[0] for r in rows]


def compute_progress(db: Session, learner_id: int, course: models.Course):
    """Returns (total_lessons, completed_lessons, percent, completed_ids).
    Guards against divide-by-zero for courses with no lessons."""
    total = get_lesson_count(course)
    completed_ids = get_completed_lesson_ids(db, learner_id, course.id)
    completed = len(completed_ids)
    percent = 0.0 if total == 0 else round((completed / total) * 100, 2)
    return total, completed, percent, completed_ids


def is_enrolled(db: Session, learner_id: int, course_id: int) -> bool:
    return (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.learner_id == learner_id,
            models.Enrollment.course_id == course_id,
        )
        .first()
        is not None
    )
