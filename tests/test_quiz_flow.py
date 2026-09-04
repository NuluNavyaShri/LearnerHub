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

    log("== Signup learner for quiz test ==")
    page.goto(BASE + "/signup", wait_until="networkidle")
    page.click("text=I'm a Learner")
    page.locator("input").nth(0).fill("Eve Learner")
    page.locator("input[type='email']").fill(f"eve{UNIQUE}@example.com")
    page.locator("input[type='password']").fill("pass123")
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    log("== Enroll in course 1 (Python Basics) ==")
    page.goto(BASE + "/course/1", wait_until="networkidle")
    page.click("text=Enroll")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    assert "/my-learning/1" in page.url

    log("== Re-visiting course detail page shows 'Go to My Learning' (no duplicate enroll) ==")
    page.goto(BASE + "/course/1", wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator("text=Go to My Learning").is_visible(), "Should show Go to My Learning, not Enroll again"
    assert page.locator("text=Enroll").count() == 0 or not page.locator("button:has-text('Enroll')").is_visible()
    log("Duplicate-enroll UI guarded: OK")

    log("== Completing all lessons to unlock quiz ==")
    page.goto(BASE + "/my-learning/1", wait_until="networkidle")
    checkboxes = page.locator("input[type='checkbox']")
    page.wait_for_timeout(500)
    n = checkboxes.count()
    for i in range(n):
        checkboxes.nth(i).click(force=True)
        page.wait_for_timeout(700)

    progress_text = page.locator("text=/\\d+% complete/").first.inner_text()
    log(f"Final progress: {progress_text}")
    assert "100%" in progress_text

    log("== Taking the quiz ==")
    page.wait_for_timeout(500)
    assert page.locator("text=Submit Quiz").is_visible(), "Quiz form not visible at 100%"
    radios = page.locator("input[type='radio']")
    count = radios.count()
    log(f"Found {count} radio options")
    # answer question 1 (correct = b) and question 2 (correct = a) per seed data
    page.locator("input[type='radio'][value='b']").first.check()
    page.locator("input[type='radio'][value='a']").nth(1).check() if count > 4 else None
    page.click("button:has-text('Submit Quiz')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    result_visible = page.locator("text=/You scored/").is_visible()
    log(f"Quiz result shown: {result_visible}")
    assert result_visible, "Quiz result not shown after submission"
    result_text = page.locator("text=/You scored/").inner_text()
    log(f"Result: {result_text}")

    browser.close()

    if errors:
        log("\n== Console/page errors detected ==")
        for e in errors:
            log(e)
        sys.exit(1)
    else:
        log("\nALL QUIZ-FLOW CHECKS PASSED")
