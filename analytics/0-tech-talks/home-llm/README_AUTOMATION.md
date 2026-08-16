# Presentation Review Automation

This automation script opens your HTML presentation, takes screenshots of each slide, downscales them to 1000px width, evaluates if fonts and layout look good, and suggests fixes if needed.

## Features

- ✅ Automatically navigates through all slides
- ✅ Takes high-resolution screenshots (1920x1080)
- ✅ Downscales to 1000px for review
- ✅ Uses Claude AI to evaluate slide quality
- ✅ Detects font issues, layout problems, and spacing issues
- ✅ Suggests specific CSS/HTML fixes
- ✅ Generates detailed summary report

## What Was Installed

The following packages were installed in the Docker container:

### System packages:
- `chromium` - Headless Chrome browser
- `chromium-driver` - Selenium WebDriver for Chrome
- `xvfb` - Virtual framebuffer for headless display
- `imagemagick` - Image processing tools
- `python3-pip` - Python package manager

### Python packages:
- `selenium` - Browser automation
- `pillow` - Image processing
- `anthropic` - Claude AI API client

## Files Created

1. **`review_slides.py`** - Main automation script
2. **`screenshots/`** - Directory containing all screenshots
   - `slide_XXX_original.png` - Full resolution (1920x1080)
   - `slide_XXX_downscaled.png` - Downscaled to 1000px width

## How to Use

### Basic Usage (without Claude evaluation)

```bash
cd /home/coder/presentation
python3 review_slides.py
```

This will:
1. Open ru.html in headless Chrome
2. Take screenshots of all 26 slides
3. Downscale them to 1000px width
4. Save them to `screenshots/` directory

### With Claude AI Evaluation (Recommended)

To enable automatic evaluation and fixes:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
python3 review_slides.py
```

This will additionally:
- Analyze each slide for visual issues
- Detect font rendering problems
- Check for layout issues
- Suggest specific fixes for any problems found
- Generate a detailed summary report

## What the Script Checks

The Claude AI evaluator checks for:

1. **Font rendering** - Are fonts rendering correctly? Not cut off or overlapping?
2. **Text readability** - Is text readable and properly aligned?
3. **Layout issues** - Text overflowing containers, elements overlapping?
4. **Image display** - Are images displaying properly?
5. **Spacing** - Is there adequate spacing between elements?

## Example Output

```
============================================================
🔍 Reviewing Slide 7
============================================================
📸 Taking screenshot...
   Saved original: screenshots/slide_007_original.png
📉 Downscaling to max 1000px width...
   Saved downscaled: screenshots/slide_007_downscaled.png
🤖 Evaluating slide with Claude...
⚠️  Issues found:
   - Font size too small in CPU column, text appears cramped
   - Spacing between columns is insufficient

💡 Suggestions:
   Update .column ul in CSS to font-size: 0.95em (from 0.9em)
   Increase .columns gap from 15px to 25px

➡️  Moving to next slide...
```

## Configuration

You can modify these settings in `review_slides.py`:

- `MAX_WIDTH = 1000` - Maximum width for downscaled images
- `--window-size=1920,1080` - Browser window size
- Model: `claude-3-5-sonnet-20241022` - Claude AI model used

## Notes

- The script automatically detects when it reaches the end of the presentation
- Screenshots are numbered sequentially (001, 002, 003, etc.)
- If Claude API key is not provided, the script will still take screenshots but skip evaluation
- The script has a safety limit of 100 slides to prevent infinite loops
- All screenshots are saved even if Claude evaluation is disabled

## Troubleshooting

**Issue**: "No ANTHROPIC_API_KEY found"
- **Solution**: Set the API key: `export ANTHROPIC_API_KEY="your-key"`

**Issue**: ChromeDriver not found
- **Solution**: The script uses `/usr/bin/chromedriver` which was installed automatically

**Issue**: Out of memory
- **Solution**: Process slides in batches by modifying the script to add a slide range limit

## Next Steps

After running the automation:

1. Review the screenshots in `screenshots/` directory
2. Check the summary report for slides with issues
3. Apply suggested CSS/HTML fixes to `ru.html`
4. Re-run the automation to verify fixes
5. Repeat until all slides look perfect!

## Running in Background

To run the automation in the background:

```bash
python3 review_slides.py > review_log.txt 2>&1 &
tail -f review_log.txt  # Watch progress
```

## Performance

- Full presentation (26 slides): ~2-3 minutes
- With Claude evaluation: ~3-5 minutes (depends on API latency)
- Screenshots total size: ~24MB for 26 slides

Enjoy your automated presentation review! 🚀
