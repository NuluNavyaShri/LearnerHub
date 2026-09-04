from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from database import get_db
from helpers import compute_progress, is_enrolled

router = APIRouter(tags=["progress"])


@router.post("/lessons/{lesson_id}/complete", response_model=schemas.ProgressOut)
def complete_lesson(lesson_id: int, payload: schemas.CompleteLessonRequest, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()

    # Rule: cannot mark complete unless enrolled in the course
    if not is_enrolled(db, payload.learner_id, course.id):
        raise HTTPException(status_code=403, detail="You must be enrolled in this course to track progress")

    # Idempotent: marking the same lesson complete twice should not error/duplicate
    existing = (
        db.query(models.LessonProgress)
        .filter(
            models.LessonProgress.learner_id == payload.learner_id,
            models.LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )
    if not existing:
        record = models.LessonProgress(
            learner_id=payload.learner_id,
            lesson_id=lesson_id,
            course_id=course.id,
        )
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()  # race: another request already inserted it - fine, treat as already complete

    return _progress_response(db, payload.learner_id, course)


def _progress_response(db: Session, learner_id: int, course: models.Course) -> schemas.ProgressOut:
    total, completed, percent, completed_ids = compute_progress(db, learner_id, course)
    return schemas.ProgressOut(
        course_id=course.id,
        total_lessons=total,
        completed_lessons=completed,
        progress_percent=percent,
        completed_lesson_ids=completed_ids,
        eligible_for_rating=(total > 0 and percent >= 50.0),
        eligible_for_quiz=(total > 0 and percent >= 100.0),
    )


@router.get("/courses/{course_id}/progress", response_model=schemas.ProgressOut)
def get_progress(course_id: int, learner_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _progress_response(db, learner_id, course)
