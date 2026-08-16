#!/usr/bin/env python3
"""Capture all slides from the home-llm Reveal.js presentation as screenshots.

Uses Playwright to control Chrome in a temporary guest profile.
Navigates through each slide using Reveal.js API and saves PNG screenshots.
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://tgr.rs/home-llm/en.html"
OUT_DIR = Path.home() / "Documents" / "llm-home" / "screenshots"
WIDTH, HEIGHT = 1920, 1080


def main():
    OUT_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # launch Chrome with a fresh temporary profile (guest-like)
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--guest", "--disable-extensions", "--no-first-run"],
        )
        context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        # wait for Reveal.js to initialize
        page.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()")
        time.sleep(1)

        total = page.evaluate("Reveal.getTotalSlides()")
        print(f"Total slides: {total}")

        for i in range(total):
            page.evaluate(f"Reveal.slide({i})")
            time.sleep(0.5)

            idx = page.evaluate("Reveal.getState()")
            h, v = idx["indexh"], idx["indexv"]
            fname = OUT_DIR / f"slide_{i+1:02d}_h{h}_v{v}.png"
            page.screenshot(path=str(fname))
            print(f"  [{i+1}/{total}] saved {fname.name}")

        browser.close()
    print(f"\nDone — {total} screenshots in {OUT_DIR}")


if __name__ == "__main__":
    main()
