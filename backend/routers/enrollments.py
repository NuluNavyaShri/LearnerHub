from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from helpers import compute_progress, is_enrolled

router = APIRouter(tags=["enrollments"])


@router.post("/courses/{course_id}/enroll", response_model=schemas.EnrollmentOut)
def enroll(course_id: int, payload: schemas.EnrollRequest, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    learner = db.query(models.User).filter(models.User.id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    if learner.role != models.Role.learner:
        raise HTTPException(status_code=403, detail="Only learners can enroll in courses")

    # Prevent duplicate enrollment
    existing = is_enrolled(db, payload.learner_id, course_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    enrollment = models.Enrollment(learner_id=payload.learner_id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    total, completed, percent, _ = compute_progress(db, payload.learner_id, course)
    return schemas.EnrollmentOut(
        course_id=course.id,
        title=course.title,
        category=course.category,
        instructor_name=course.instructor_name,
        total_lessons=total,
        completed_lessons=completed,
        progress_percent=percent,
        enrolled_at=enrollment.enrolled_at,
    )


@router.get("/learners/{learner_id}/enrollments", response_model=List[schemas.EnrollmentOut])
def my_learning(learner_id: int, db: Session = Depends(get_db)):
    learner = db.query(models.User).filter(models.User.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    enrollments = (
        db.query(models.Enrollment).filter(models.Enrollment.learner_id == learner_id).all()
    )
    out = []
    for e in enrollments:
        course = e.course
        total, completed, percent, _ = compute_progress(db, learner_id, course)
        out.append(
            schemas.EnrollmentOut(
                course_id=course.id,
                title=course.title,
                category=course.category,
                instructor_name=course.instructor_name,
                total_lessons=total,
                completed_lessons=completed,
                progress_percent=percent,
                enrolled_at=e.enrolled_at,
            )
        )
    return out
