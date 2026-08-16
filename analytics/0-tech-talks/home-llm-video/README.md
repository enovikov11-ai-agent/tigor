# home-llm-video

Production video for the "How to Safely and Privately Run LLMs on Your Own Hardware" talk.

## Slide timeline

0:00 - slide 1
0:18 - 2
0:50 - 3
2:18 - 4
3:44 - 5
4:42 - 6
5:44 - 7
9:40 - 8
11:51 - 9
14:56 - 10
17:01 - 11
20:08 - 12
25:03 - 13
26:06 - 14
28:28 - 15 video (glm-flash-demo.mp4, 16s)
29:03 - 16 video (minimax-demo.mp4, 20s)
32:10 - 17
32:54 - 18
33:16 - 19
34:10 - 20
34:37 - 21
36:18 - 22
37:35 - 23
38:05 - 24
39:15 - 25
40:28 - 26
40:50 - 27
42:00 - no overlay

## Chosen parameters

From crop-tool.html, adjusted to x=0:

```
Crop:    672x378 at (0, 442) from 720x1280 source
Upscale: 672x378 → 2560x1440 (2K, lanczos)
Overlay: 1623x914 at (0, 0) in the upscaled frame
```

## Source material

| Asset | Location | Format |
|---|---|---|
| Presentation source | `../../web/tgr.rs/home-llm/` (Reveal.js) | en.html, ru.html |
| Live URL | https://tgr.rs/home-llm/en.html | — |
| Video recording (vertical) | `~/Documents/llm-home/llm-home-cut.mp4` | 720x1280 (9:16), ~71 min, h264 |
| Full uncut recording | `~/Documents/llm-home/llm-home-full.mp4` | same |
| glm-flash demo clip | `../../web/tgr.rs/home-llm/images/glm-flash-demo.mp4` | 2276x1344, 16s |
| minimax demo clip | `../../web/tgr.rs/home-llm/images/minimax-demo.mp4` | 2276x1344, 20s |
| Slide screenshots | `~/Documents/llm-home/screenshots/` | 1920x1080 PNG x27 |
| Previous automation | `../home-llm/` | Python scripts |

## Pipeline

### Step 1: Capture slide screenshots

```
pip3 install --break-system-packages playwright
```

```
python3 capture_slides.py
```

Opens the Reveal.js presentation in Chrome via Playwright, saves all 27 slides as 1920x1080 PNGs to `~/Documents/llm-home/screenshots/`.

### Step 2: Plan crop and overlay layout

Open `crop-tool.html` in browser, load the source video. Draw two rectangles (A=crop, B=slide overlay). Click-drag to draw, A/B buttons to switch. Ratios configurable. Positions saved to URL querystring.

### Step 3: Crop and upscale to 2K

```
ffmpeg -i ~/Documents/llm-home/llm-home-cut.mp4 \
  -vf "crop=672:378:0:442,scale=2560:1440:flags=lanczos" \
  -c:v libx264 -crf 18 -preset medium \
  -c:a copy \
  ~/Documents/llm-home/llm-home-cropped.mp4
```

### Step 4: Render final video with overlays

```
python3 render.py
```

`render.py` builds a single ffmpeg command with 29 inputs (base video + 25 slide PNGs + 2 demo video clips). All 27 overlays are chained in one `filter_complex` — single encode pass. Video clips use `-itsoffset` for timing and play once (no loop).

Output: `~/Documents/llm-home/llm-home-final.mp4`

### Step 5: Normalize audio

```
ffmpeg -i ~/Documents/llm-home/llm-home-final.mp4 \
  -af loudnorm \
  -c:v copy \
  ~/Documents/llm-home/llm-home-final-normalized.mp4
```

### Step 6: Review and iterate

Adjust timestamps in the slide timeline above, update `render.py` TIMELINE, re-run.

## Files

| File | Purpose |
|---|---|
| `capture_slides.py` | Captures slide screenshots via Playwright + Chrome |
| `crop-tool.html` | Interactive tool for planning crop and overlay positions |
| `render.py` | Builds and runs the full ffmpeg overlay command |
| `README.md` | This file |
