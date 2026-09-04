from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.courses import _to_detail

router = APIRouter(prefix="/instructors", tags=["instructor"])


@router.get("/{instructor_id}/courses", response_model=List[schemas.CourseDetailOut])
def instructor_courses(instructor_id: int, db: Session = Depends(get_db)):
    instructor = db.query(models.User).filter(models.User.id == instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    courses = db.query(models.Course).filter(models.Course.instructor_id == instructor_id).all()
    return [_to_detail(db, c) for c in courses]
