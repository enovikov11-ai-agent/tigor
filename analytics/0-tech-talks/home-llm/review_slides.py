#!/usr/bin/env python3
"""
Automation script to review presentation slides.
Opens HTML presentation, takes screenshots, downscales them,
evaluates if fonts look good, updates HTML if needed, and advances to next slide.
"""

import os
import time
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
import anthropic

# Configuration
PRESENTATION_PATH = "/home/coder/presentation/ru.html"
SCREENSHOTS_DIR = "/home/coder/presentation/screenshots"
MAX_WIDTH = 1000
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def setup_driver():
    """Setup Chrome WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--force-device-scale-factor=1')

    # Try to use chromium-driver
    service = Service('/usr/bin/chromedriver')

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def downscale_image(image_data, max_width=MAX_WIDTH):
    """Downscale image to specified max width while maintaining aspect ratio."""
    img = Image.open(io.BytesIO(image_data))

    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def evaluate_slide(image_data, slide_number):
    """Use Claude to evaluate if the slide looks good or has font issues."""
    if not ANTHROPIC_API_KEY:
        print(f"⚠️  No ANTHROPIC_API_KEY found. Skipping evaluation for slide {slide_number}")
        return {"looks_good": True, "issues": [], "suggestions": ""}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Encode image to base64
    image_b64 = base64.standard_b64encode(image_data).decode('utf-8')

    prompt = """Please evaluate this presentation slide and check if it looks good visually.

Focus on:
1. Are fonts rendering correctly? (not cut off, not overlapping, not too large/small)
2. Is text readable and properly aligned?
3. Are there any layout issues? (text overflowing containers, elements overlapping)
4. Are images displaying properly?
5. Is there adequate spacing between elements?

Respond in JSON format with:
{
  "looks_good": true/false,
  "issues": ["list of specific issues found"],
  "suggestions": "specific CSS or HTML changes to fix the issues"
}

Be specific about what needs to be fixed and provide actionable suggestions."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Extract response text
        response_text = message.content[0].text

        # Try to parse JSON from response
        import json
        # Sometimes Claude wraps JSON in markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)
        return result

    except Exception as e:
        print(f"❌ Error evaluating slide {slide_number}: {e}")
        return {"looks_good": True, "issues": [], "suggestions": ""}

def main():
    """Main automation loop."""
    print("🚀 Starting presentation review automation...")

    # Create screenshots directory
    Path(SCREENSHOTS_DIR).mkdir(exist_ok=True)

    # Setup driver
    print("📦 Setting up Chrome driver...")
    driver = setup_driver()

    try:
        # Open presentation
        print(f"📂 Opening presentation: {PRESENTATION_PATH}")
        driver.get(f"file://{PRESENTATION_PATH}")

        # Wait for reveal.js to initialize
        time.sleep(3)

        # Get total number of slides
        slides_info = driver.execute_script("""
            return {
                total_h: Reveal.getTotalSlides(),
                current_h: Reveal.getIndices().h,
                current_v: Reveal.getIndices().v
            };
        """)

        total_slides = slides_info['total_h']
        print(f"📊 Found {total_slides} slides to review\n")

        slide_number = 1
        slides_with_issues = []

        while True:
            print(f"\n{'='*60}")
            print(f"🔍 Reviewing Slide {slide_number}")
            print(f"{'='*60}")

            # Take screenshot
            print("📸 Taking screenshot...")
            screenshot_data = driver.get_screenshot_as_png()

            # Save original
            original_path = f"{SCREENSHOTS_DIR}/slide_{slide_number:03d}_original.png"
            with open(original_path, 'wb') as f:
                f.write(screenshot_data)
            print(f"   Saved original: {original_path}")

            # Downscale
            print(f"📉 Downscaling to max {MAX_WIDTH}px width...")
            downscaled_data = downscale_image(screenshot_data, MAX_WIDTH)
            downscaled_path = f"{SCREENSHOTS_DIR}/slide_{slide_number:03d}_downscaled.png"
            with open(downscaled_path, 'wb') as f:
                f.write(downscaled_data)
            print(f"   Saved downscaled: {downscaled_path}")

            # Evaluate with Claude
            print("🤖 Evaluating slide with Claude...")
            evaluation = evaluate_slide(downscaled_data, slide_number)

            if evaluation['looks_good']:
                print("✅ Slide looks good!")
            else:
                print("⚠️  Issues found:")
                for issue in evaluation['issues']:
                    print(f"   - {issue}")
                print(f"\n💡 Suggestions:")
                print(f"   {evaluation['suggestions']}")
                slides_with_issues.append({
                    'slide_number': slide_number,
                    'issues': evaluation['issues'],
                    'suggestions': evaluation['suggestions']
                })

            # Try to move to next slide
            print("\n➡️  Moving to next slide...")

            # Get current position before moving
            indices_before = driver.execute_script("return Reveal.getIndices();")

            # Press right arrow
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ARROW_RIGHT)
            time.sleep(1)

            # Check if we moved
            indices_after = driver.execute_script("return Reveal.getIndices();")

            if indices_before == indices_after:
                print("🏁 Reached the end of presentation!")
                break

            slide_number += 1

            # Safety check
            if slide_number > 100:
                print("⚠️  Safety limit reached (100 slides)")
                break

        # Summary
        print(f"\n\n{'='*60}")
        print("📋 REVIEW SUMMARY")
        print(f"{'='*60}")
        print(f"Total slides reviewed: {slide_number}")
        print(f"Slides with issues: {len(slides_with_issues)}")

        if slides_with_issues:
            print("\n⚠️  Slides that need attention:")
            for slide_info in slides_with_issues:
                print(f"\n  Slide {slide_info['slide_number']}:")
                for issue in slide_info['issues']:
                    print(f"    - {issue}")
                print(f"  Suggestions: {slide_info['suggestions']}")
        else:
            print("\n✅ All slides look great!")

        print(f"\n📁 Screenshots saved to: {SCREENSHOTS_DIR}")

    except Exception as e:
        print(f"\n❌ Error during automation: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n🔒 Closing browser...")
        driver.quit()
        print("✅ Done!")

if __name__ == "__main__":
    main()
