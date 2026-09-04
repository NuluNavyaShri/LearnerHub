from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, EmailStr, field_validator


# ---------- Auth ----------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["instructor", "learner"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


# ---------- Lessons ----------
class LessonCreate(BaseModel):
    title: str
    content: str = ""
    duration_minutes: int = 0
    order: Optional[int] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: Optional[int] = None


class LessonOut(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    duration_minutes: int
    order: int

    class Config:
        from_attributes = True


class LessonOutWithProgress(LessonOut):
    completed: bool = False


# ---------- Quiz ----------
class QuizQuestionCreate(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: Literal["a", "b", "c", "d"]


class QuizQuestionOut(BaseModel):
    id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class QuizQuestionOutWithAnswer(QuizQuestionOut):
    correct_option: str


class QuizSubmitRequest(BaseModel):
    learner_id: int
    answers: dict  # {question_id(str): "a"/"b"/"c"/"d"}


class QuizAttemptOut(BaseModel):
    id: int
    score: int
    total: int
    passed: bool
    attempted_at: datetime

    class Config:
        from_attributes = True


# ---------- Courses ----------
class CourseCreate(BaseModel):
    title: str
    description: str = ""
    category: str
    price: float = 0.0
    instructor_id: int


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None


class PublishRequest(BaseModel):
    """Details required to publish a course, per instructor."""
    quiz_questions: List[QuizQuestionCreate] = []


class CourseCardOut(BaseModel):
    id: int
    title: str
    category: str
    price: float
    instructor_name: str
    avg_rating: float
    rating_count: int
    lesson_count: int
    published: bool

    class Config:
        from_attributes = True


class CourseDetailOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    price: float
    instructor_id: int
    instructor_name: str
    published: bool
    avg_rating: float
    rating_count: int
    total_duration_minutes: int
    quiz_question_count: int
    lessons: List[LessonOut]

    class Config:
        from_attributes = True


# ---------- Enrollment ----------
class EnrollRequest(BaseModel):
    learner_id: int


class EnrollmentOut(BaseModel):
    course_id: int
    title: str
    category: str
    instructor_name: str
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    enrolled_at: datetime

    class Config:
        from_attributes = True


# ---------- Progress ----------
class CompleteLessonRequest(BaseModel):
    learner_id: int


class ProgressOut(BaseModel):
    course_id: int
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    completed_lesson_ids: List[int]
    eligible_for_rating: bool
    eligible_for_quiz: bool


# ---------- Ratings ----------
class RatingCreate(BaseModel):
    learner_id: int
    stars: int
    review: str = ""

    @field_validator("stars")
    @classmethod
    def validate_stars(cls, v):
        if v < 1 or v > 5:
            raise ValueError("stars must be between 1 and 5")
        return v


class RatingOut(BaseModel):
    id: int
    learner_id: int
    learner_name: str
    stars: int
    review: str
    created_at: datetime

    class Config:
        from_attributes = True
