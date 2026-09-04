from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from helpers import get_avg_rating, get_total_duration, get_lesson_count

router = APIRouter(prefix="/courses", tags=["courses"])


def _to_card(db: Session, course: models.Course) -> schemas.CourseCardOut:
    avg, count = get_avg_rating(db, course.id)
    return schemas.CourseCardOut(
        id=course.id,
        title=course.title,
        category=course.category,
        price=course.price,
        instructor_name=course.instructor_name,
        avg_rating=avg,
        rating_count=count,
        lesson_count=get_lesson_count(course),
        published=course.published,
    )


@router.post("", response_model=schemas.CourseDetailOut)
def create_course(payload: schemas.CourseCreate, db: Session = Depends(get_db)):
    instructor = db.query(models.User).filter(models.User.id == payload.instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    if instructor.role != models.Role.instructor:
        raise HTTPException(status_code=403, detail="Only instructors can create courses")

    course = models.Course(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        instructor_id=instructor.id,
        instructor_name=instructor.name,
        published=False,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return _to_detail(db, course)


def _to_detail(db: Session, course: models.Course) -> schemas.CourseDetailOut:
    avg, count = get_avg_rating(db, course.id)
    quiz_count = (
        db.query(models.QuizQuestion).filter(models.QuizQuestion.course_id == course.id).count()
    )
    return schemas.CourseDetailOut(
        id=course.id,
        title=course.title,
        description=course.description,
        category=course.category,
        price=course.price,
        instructor_id=course.instructor_id,
        instructor_name=course.instructor_name,
        published=course.published,
        avg_rating=avg,
        rating_count=count,
        total_duration_minutes=get_total_duration(course),
        quiz_question_count=quiz_count,
        lessons=[schemas.LessonOut.model_validate(l) for l in course.lessons],
    )


@router.get("", response_model=List[schemas.CourseCardOut])
def catalog(
    search: Optional[str] = Query(None, description="search by title"),
    category: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, description="rating | price | -price | -rating"),
    include_unpublished: bool = Query(False),
    db: Session = Depends(get_db),
):
    q = db.query(models.Course)
    if not include_unpublished:
        q = q.filter(models.Course.published == True)  # noqa: E712
    if search:
        q = q.filter(models.Course.title.ilike(f"%{search}%"))
    if category:
        q = q.filter(models.Course.category == category)

    courses = q.all()
    cards = [_to_card(db, c) for c in courses]

    if sort == "price":
        cards.sort(key=lambda c: c.price)
    elif sort == "-price":
        cards.sort(key=lambda c: c.price, reverse=True)
    elif sort == "rating":
        cards.sort(key=lambda c: c.avg_rating)
    elif sort == "-rating":
        cards.sort(key=lambda c: c.avg_rating, reverse=True)

    return cards


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(models.Course.category).distinct().all()
    return sorted({r[0] for r in rows})


@router.get("/{course_id}", response_model=schemas.CourseDetailOut)
def course_detail(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _to_detail(db, course)


@router.put("/{course_id}", response_model=schemas.CourseDetailOut)
def update_course(course_id: int, payload: schemas.CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return _to_detail(db, course)


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"detail": "Course deleted"}


@router.post("/{course_id}/publish", response_model=schemas.CourseDetailOut)
def publish_course(course_id: int, payload: schemas.PublishRequest, db: Session = Depends(get_db)):
    """Publishing a course requires the instructor to supply quiz details
    (at least one question) so learners have a quiz to take at 100% completion."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if get_lesson_count(course) == 0:
        raise HTTPException(status_code=400, detail="Add at least one lesson before publishing")

    # Require quiz questions either already existing or provided now
    existing_quiz_count = (
        db.query(models.QuizQuestion).filter(models.QuizQuestion.course_id == course_id).count()
    )
    if existing_quiz_count == 0 and not payload.quiz_questions:
        raise HTTPException(
            status_code=400,
            detail="At least one quiz question is required to publish a course",
        )

    for q in payload.quiz_questions:
        db.add(models.QuizQuestion(course_id=course_id, **q.model_dump()))

    course.published = True
    db.commit()
    db.refresh(course)
    return _to_detail(db, course)
