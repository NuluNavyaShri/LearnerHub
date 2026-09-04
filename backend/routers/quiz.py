from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from helpers import compute_progress, is_enrolled

router = APIRouter(prefix="/courses/{course_id}/quiz", tags=["quiz"])


@router.get("", response_model=List[schemas.QuizQuestionOut])
def get_quiz(course_id: int, learner_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not is_enrolled(db, learner_id, course_id):
        raise HTTPException(status_code=403, detail="You must be enrolled to access the quiz")

    total, completed, percent, _ = compute_progress(db, learner_id, course)
    if total == 0 or percent < 100.0:
        raise HTTPException(
            status_code=403,
            detail="The quiz unlocks after you complete 100% of the course lessons",
        )

    questions = (
        db.query(models.QuizQuestion).filter(models.QuizQuestion.course_id == course_id).all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz has been published for this course")
    return questions


@router.post("/attempt", response_model=schemas.QuizAttemptOut)
def attempt_quiz(course_id: int, payload: schemas.QuizSubmitRequest, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not is_enrolled(db, payload.learner_id, course_id):
        raise HTTPException(status_code=403, detail="You must be enrolled to attempt the quiz")

    # Re-verify 100% completion server-side; never trust the client's claim
    total, completed, percent, _ = compute_progress(db, payload.learner_id, course)
    if total == 0 or percent < 100.0:
        raise HTTPException(
            status_code=403,
            detail="The quiz unlocks after you complete 100% of the course lessons",
        )

    questions = (
        db.query(models.QuizQuestion).filter(models.QuizQuestion.course_id == course_id).all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz has been published for this course")

    score = 0
    for q in questions:
        submitted = payload.answers.get(str(q.id))
        if submitted and submitted.lower() == q.correct_option.lower():
            score += 1

    passed = score / len(questions) >= 0.6  # 60% to pass, arbitrary but reasonable default

    attempt = models.QuizAttempt(
        learner_id=payload.learner_id,
        course_id=course_id,
        score=score,
        total=len(questions),
        passed=passed,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/attempts", response_model=List[schemas.QuizAttemptOut])
def list_attempts(course_id: int, learner_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.QuizAttempt)
        .filter(models.QuizAttempt.course_id == course_id, models.QuizAttempt.learner_id == learner_id)
        .order_by(models.QuizAttempt.attempted_at.desc())
        .all()
    )
