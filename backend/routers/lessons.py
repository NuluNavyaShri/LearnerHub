from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(tags=["lessons"])


@router.post("/courses/{course_id}/lessons", response_model=schemas.LessonOut)
def add_lesson(course_id: int, payload: schemas.LessonCreate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    order = payload.order
    if order is None:
        max_order = (
            db.query(models.Lesson)
            .filter(models.Lesson.course_id == course_id)
            .count()
        )
        order = max_order  # append to end

    lesson = models.Lesson(
        course_id=course_id,
        title=payload.title,
        content=payload.content,
        duration_minutes=payload.duration_minutes,
        order=order,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/courses/{course_id}/lessons", response_model=List[schemas.LessonOut])
def list_lessons(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course.lessons


@router.put("/lessons/{lesson_id}", response_model=schemas.LessonOut)
def update_lesson(lesson_id: int, payload: schemas.LessonUpdate, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return {"detail": "Lesson deleted"}


@router.put("/courses/{course_id}/lessons/reorder", response_model=List[schemas.LessonOut])
def reorder_lessons(course_id: int, lesson_ids_in_order: List[int], db: Session = Depends(get_db)):
    """Body: a JSON array of lesson ids in the desired order."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lessons_by_id = {l.id: l for l in course.lessons}
    if set(lesson_ids_in_order) != set(lessons_by_id.keys()):
        raise HTTPException(status_code=400, detail="Lesson id set does not match course lessons")

    for idx, lid in enumerate(lesson_ids_in_order):
        lessons_by_id[lid].order = idx

    db.commit()
    return sorted(course.lessons, key=lambda l: l.order)
