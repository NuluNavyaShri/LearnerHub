from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from helpers import compute_progress, is_enrolled

router = APIRouter(tags=["ratings"])


@router.post("/courses/{course_id}/ratings", response_model=schemas.RatingOut)
def rate_course(course_id: int, payload: schemas.RatingCreate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    learner = db.query(models.User).filter(models.User.id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    if not is_enrolled(db, payload.learner_id, course_id):
        raise HTTPException(status_code=403, detail="You must be enrolled to rate this course")

    # Server-side enforcement of the 50% completion rule - never trust the client
    total, completed, percent, _ = compute_progress(db, payload.learner_id, course)
    if total == 0 or percent < 50.0:
        raise HTTPException(
            status_code=403,
            detail="You must complete at least 50% of the course lessons before rating",
        )

    existing = (
        db.query(models.Rating)
        .filter(models.Rating.learner_id == payload.learner_id, models.Rating.course_id == course_id)
        .first()
    )
    if existing:
        # one rating per learner per course -> update instead of duplicating
        existing.stars = payload.stars
        existing.review = payload.review
        db.commit()
        db.refresh(existing)
        rating = existing
    else:
        rating = models.Rating(
            learner_id=payload.learner_id,
            course_id=course_id,
            stars=payload.stars,
            review=payload.review,
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)

    return schemas.RatingOut(
        id=rating.id,
        learner_id=rating.learner_id,
        learner_name=learner.name,
        stars=rating.stars,
        review=rating.review,
        created_at=rating.created_at,
    )


@router.get("/courses/{course_id}/ratings", response_model=List[schemas.RatingOut])
def list_ratings(course_id: int, db: Session = Depends(get_db)):
    ratings = db.query(models.Rating).filter(models.Rating.course_id == course_id).all()
    out = []
    for r in ratings:
        learner = db.query(models.User).filter(models.User.id == r.learner_id).first()
        out.append(
            schemas.RatingOut(
                id=r.id,
                learner_id=r.learner_id,
                learner_name=learner.name if learner else "Unknown",
                stars=r.stars,
                review=r.review,
                created_at=r.created_at,
            )
        )
    return out
