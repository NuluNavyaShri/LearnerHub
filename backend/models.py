import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Boolean,
    Text, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship

from database import Base


class Role(str, enum.Enum):
    instructor = "instructor"
    learner = "learner"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    courses = relationship("Course", back_populates="instructor")
    enrollments = relationship("Enrollment", back_populates="learner")
    progress = relationship("LessonProgress", back_populates="learner")
    ratings = relationship("Rating", back_populates="learner")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    category = Column(String, nullable=False, index=True)
    price = Column(Float, default=0.0)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instructor_name = Column(String, nullable=False)  # denormalized for convenience
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship("User", back_populates="courses")
    lessons = relationship(
        "Lesson", back_populates="course",
        cascade="all, delete-orphan", order_by="Lesson.order"
    )
    enrollments = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "Rating", back_populates="course", cascade="all, delete-orphan"
    )
    quiz_questions = relationship(
        "QuizQuestion", back_populates="course", cascade="all, delete-orphan"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    duration_minutes = Column(Integer, default=0)
    order = Column(Integer, default=0)

    course = relationship("Course", back_populates="lessons")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("learner_id", "course_id", name="uq_enrollment"),)

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("learner_id", "lesson_id", name="uq_progress"),)

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("User", back_populates="progress")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("learner_id", "course_id", name="uq_rating"),)

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    stars = Column(Integer, nullable=False)
    review = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("User", back_populates="ratings")
    course = relationship("Course", back_populates="ratings")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    question = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # 'a' | 'b' | 'c' | 'd'

    course = relationship("Course", back_populates="quiz_questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    score = Column(Integer, nullable=False)          # number correct
    total = Column(Integer, nullable=False)           # total questions
    passed = Column(Boolean, default=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)
