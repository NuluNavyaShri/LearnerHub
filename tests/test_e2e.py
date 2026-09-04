import sys
import time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
UNIQUE = str(int(time.time()))
errors = []

def log(msg):
    print(msg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    log("== Visiting catalog ==")
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator("text=Python Basics").first.is_visible(), "Course card not visible on catalog"
    log("Catalog shows course card: OK")

    log("== Testing search ==")
    page.fill("input[placeholder='Search by title...']", "zzzznonexistent")
    page.wait_for_timeout(600)
    assert page.locator("text=No courses match").is_visible(), "Empty search state not shown"
    log("Empty search state: OK")
    page.fill("input[placeholder='Search by title...']", "")
    page.wait_for_timeout(600)

    log("== Signing up a new learner ==")
    page.goto(BASE + "/signup", wait_until="networkidle")
    page.click("text=I'm a Learner")
    page.fill("input[type='text'], input:not([type])", "")  # noop guard
    page.fill("form input:nth-of-type(1)", "Carol Learner") if False else None
    # Use label-based selectors instead
    page.locator("input").nth(0).fill("Carol Learner")
    page.locator("input[type='email']").fill(f"carol{UNIQUE}@example.com")
    page.locator("input[type='password']").fill("pass123")
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    log(f"After signup, URL: {page.url}")
    if "/login" in page.url or "/signup" in page.url:
        err_text = page.locator("text=/.*already registered.*/i")
        log("Signup may have failed, error visible: " + str(err_text.count()))

    log("== Visiting course detail page ==")
    page.goto(BASE + "/course/1", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator("text=Python Basics").first.is_visible(), "Course title not visible"
    assert page.locator("text=Enroll").first.is_visible(), "Enroll button not visible"
    log("Course detail page renders: OK")

    log("== Enrolling ==")
    page.click("text=Enroll")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    log(f"After enroll, URL: {page.url}")
    assert "/my-learning/1" in page.url, f"Did not redirect to learning page, got {page.url}"

    log("== Ticking lessons complete (checking live progress update) ==")
    checkboxes = page.locator("input[type='checkbox']")
    count = checkboxes.count()
    log(f"Found {count} lesson checkboxes")
    checkboxes.nth(0).click(force=True)
    page.wait_for_timeout(900)
    progress_text = page.locator("text=/\\d+% complete/").first.inner_text()
    log(f"Progress after 1 lesson: {progress_text}")
    assert "25%" in progress_text, f"Expected 25%, got {progress_text}"
    assert checkboxes.nth(0).is_checked(), "Checkbox 0 should be checked after completing"

    checkboxes.nth(1).click(force=True)
    page.wait_for_timeout(900)
    progress_text = page.locator("text=/\\d+% complete/").first.inner_text()
    log(f"Progress after 2 lessons: {progress_text}")
    assert "50%" in progress_text, f"Expected 50%, got {progress_text}"

    log("== Checking rating form appears at 50% ==")
    assert page.locator("text=Rate this course").is_visible(), "Rating form not shown at 50%"
    log("Rating form visible at 50%: OK")

    log("== Checking quiz still locked (not 100% yet) ==")
    assert page.locator("text=Complete 100% of the lessons").is_visible(), "Quiz should still be locked"
    log("Quiz locked before 100%: OK")

    log("== Completing remaining lessons ==")
    checkboxes.nth(2).click(force=True)
    page.wait_for_timeout(900)
    checkboxes.nth(3).click(force=True)
    page.wait_for_timeout(900)
    progress_text = page.locator("text=/\\d+% complete/").first.inner_text()
    log(f"Progress after all lessons: {progress_text}")
    assert "100%" in progress_text, f"Expected 100%, got {progress_text}"

    log("== Checking quiz unlocked ==")
    page.wait_for_timeout(500)
    quiz_visible = page.locator("text=Submit Quiz").is_visible()
    log(f"Submit Quiz button visible: {quiz_visible}")

    log("== My Learning page shows progress bar ==")
    page.goto(BASE + "/my-learning", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator("text=Python Basics").first.is_visible(), "Course not in My Learning"
    log("My Learning shows enrolled course: OK")

    browser.close()

    if errors:
        log("\n== Console/page errors detected ==")
        for e in errors:
            log(e)
        sys.exit(1)
    else:
        log("\n== No console errors detected ==")
        log("ALL CHECKS PASSED")
