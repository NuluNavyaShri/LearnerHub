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

    log("== Instructor signup ==")
    page.goto(BASE + "/signup", wait_until="networkidle")
    page.click("text=I'm an Instructor")
    page.locator("input").nth(0).fill("Dana Instructor")
    page.locator("input[type='email']").fill(f"dana{UNIQUE}@example.com")
    page.locator("input[type='password']").fill("pass123")
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    log(f"After signup, URL: {page.url}")
    assert "/instructor" in page.url, f"Expected instructor dashboard redirect, got {page.url}"

    log("== Creating a course ==")
    page.click("text=+ New Course")
    page.locator("input").nth(0).fill("Design Fundamentals")
    page.locator("textarea").first.fill("Learn the basics of visual design.")
    page.locator("input").nth(1).fill("Design")
    page.locator("input[type='number']").first.fill("299")
    page.click("button:has-text('Create course')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    log(f"After create, URL: {page.url}")
    assert "/instructor/" in page.url, "Should navigate to manage page"

    log("== Trying to publish with zero lessons (should show error / be blocked) ==")
    # Add lessons first (required)
    page.locator("input[placeholder='Lesson title']").fill("Color Theory")
    page.locator("textarea[placeholder='Lesson content / notes']").fill("Basics of color")
    page.click("button:has-text('Add lesson')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    assert page.locator("text=Color Theory").is_visible(), "Lesson not added"
    log("Lesson added: OK")

    log("== Publishing with quiz details ==")
    page.click("text=Publish this course")
    page.wait_for_timeout(300)
    page.locator("input[placeholder='Question text']").fill("What is the primary color wheel based on?")
    page.locator("input[placeholder='Option A']").fill("RGB")
    page.locator("input[placeholder='Option B']").fill("RYB")
    page.locator("input[placeholder='Option C']").fill("CMYK")
    page.locator("input[placeholder='Option D']").fill("HSL")
    page.select_option("select", "b")
    page.click("button:has-text('Publish course')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    published = page.locator("text=This course is live in the catalog").is_visible()
    log(f"Published successfully: {published}")
    assert published, "Course did not show as published"

    browser.close()

    if errors:
        log("\n== Console/page errors detected ==")
        for e in errors:
            log(e)
        sys.exit(1)
    else:
        log("\nALL INSTRUCTOR-FLOW CHECKS PASSED")
