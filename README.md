# LearnHub — Mini Udemy-Style Course Platform

A working end-to-end course platform: instructors publish courses with lessons and
a quiz, learners enroll, track progress, rate courses, and take the quiz on completion.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (`backend/`)
- **Frontend:** Next.js (App Router, JS, Tailwind) (`frontend/`)
- They talk over plain HTTP/JSON. No auth tokens — login returns a `User` object
  the frontend keeps in `localStorage` and sends explicit `learner_id` /
  `instructor_id` fields with each request. Simple by design, but every rule
  that matters (enrollment, 50% rating gate, 100% quiz gate, no duplicates) is
  re-verified server-side — the frontend never enforces a rule the backend doesn't.

## Running it

### 1. Backend (port 8000)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

SQLite schema is created automatically on first boot (`learnhub.db`, gitignored).
Visit `http://localhost:8000/docs` for interactive API docs.

### 2. Frontend (port 3000)

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env.local` already points `NEXT_PUBLIC_API_URL` at `http://localhost:8000`.

Visit `http://localhost:3000`.

## Demo script

1. **Sign up an instructor** → dashboard → **+ New Course** → fill title/category/price.
2. Add 3–4 lessons.
3. Click **Publish this course** — this form *requires* at least one quiz question
   (the "publish requires quiz details" rule); it's rejected server-side if you
   have zero lessons or zero quiz questions.
4. **Sign up a learner** (separate account/login) → browse catalog → search/filter/sort
   → open the course → **Enroll**.
5. In **My Learning**, open the course, tick lessons off one by one — progress bar
   updates live (no page reload, it's a client-side state update after each API call).
6. At **50%** completion the rating form appears — rate & review.
7. At **100%** completion the quiz unlocks — answer and submit, see the score.
8. Try re-enrolling in the same course (button becomes "Go to My Learning", and the
   backend rejects a duplicate enroll with 400 if hit directly).

## Data model (`backend/models.py`)

- `User` — `role` is `instructor` or `learner`; same table, discriminated by role.
- `Course` — belongs to an instructor, has `published` flag.
- `Lesson` — belongs to a course, has `order` and `duration_minutes`.
- `Enrollment` — unique `(learner_id, course_id)`.
- `LessonProgress` — unique `(learner_id, lesson_id)`; completing twice is a no-op, not an error.
- `Rating` — unique `(learner_id, course_id)`; re-rating updates in place rather than duplicating.
- `QuizQuestion` / `QuizAttempt` — one quiz per course, attached at publish time.

## Server-enforced rules (see `backend/helpers.py` + routers)

- Can't mark a lesson complete unless enrolled (`403`).
- Marking the same lesson complete twice is idempotent (not an error, no duplicate row).
- Can't enroll twice in the same course (`400`).
- Can't rate before completing ≥50% of lessons — **computed from `LessonProgress`
  rows server-side**, never trusted from the client (`403` if violated).
- Quiz only fetchable/attemptable at 100% completion, checked again at submission
  time (`403` if violated even if the frontend UI is bypassed).
- Average rating and total course duration are always computed server-side
  (`helpers.get_avg_rating`, `helpers.get_total_duration`), never sent by the client.
- Courses with zero lessons: progress is defined as 0% (explicit guard against
  divide-by-zero in `helpers.compute_progress`), and they simply can't be published
  in the first place.
- Empty catalog / empty search results render a friendly empty state, not a crash.

## API surface

See `backend/main.py` for the full router list, or run the server and open
`/docs`. Routers: `auth`, `courses`, `lessons`, `enrollments`, `progress`,
`ratings`, `quiz`, `instructor`.

## Testing performed

- `backend/` — manually exercised every endpoint and edge case via `curl`
  (duplicate signup/enroll, wrong password, publish without lessons/quiz,
  complete-without-enroll, double-complete, rate-before-50%, quiz-before-100%,
  zero-lesson course progress, catalog search/filter/sort/empty-results).
- `frontend/` — `npm run build` passes cleanly; end-to-end flows were driven
  with Playwright in a real headless Chromium browser (see `test_e2e.py`,
  `test_instructor_flow.py`, `test_quiz_flow.py` at the repo root) covering:
  catalog browse/search/empty-state, learner signup → enroll → tick lessons →
  live progress → rating gate at 50% → quiz gate at 100% → quiz submission and
  scoring, instructor signup → create course → add lesson → publish with quiz,
  and duplicate-enroll UI guarding. All passed with zero console errors.

## Known simplifications (by design, given scope)

- Auth is intentionally minimal: SHA-256 password hashing, no JWT/session
  cookies — fine for a local demo, not production-grade auth.
- No lesson reordering UI (the API supports it — `PUT /courses/{id}/lessons/reorder`
  — but the instructor page doesn't expose drag-and-drop).
- No "un-complete a lesson" action in the UI (backend doesn't forbid it, just wasn't wired up).
- Quiz pass threshold is a flat 60%, chosen arbitrarily since the spec didn't specify one.
