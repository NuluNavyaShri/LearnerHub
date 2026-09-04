from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # noqa: F401  (ensures models are registered on Base before create_all)

from routers import auth, courses, lessons, enrollments, progress, ratings, quiz, instructor

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LearnHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(lessons.router)
app.include_router(enrollments.router)
app.include_router(progress.router)
app.include_router(ratings.router)
app.include_router(quiz.router)
app.include_router(instructor.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "LearnHub API"}
