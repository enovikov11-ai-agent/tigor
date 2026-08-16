#!/usr/bin/env python3
"""Build and run the full ffmpeg command to overlay slides and demo videos onto the cropped base."""
import subprocess
import sys
from pathlib import Path

BASE = Path.home() / "Documents/llm-home/llm-home-cropped.mp4"
SCREENSHOTS = Path.home() / "Documents/llm-home/screenshots"
IMAGES = Path.home() / "Desktop/monorepo/web/tgr.rs/home-llm/images"
OUT = Path.home() / "Documents/llm-home/llm-home-final.mp4"

SCALE = "1623:914"
OX, OY = 0, 0

# (start_time_sec, slide_number, type)
# type: "img" for screenshot, "flash" for glm-flash-demo, "minimax" for minimax-demo
TIMELINE = [
    (0,    1,  "img"),
    (18,   2,  "img"),
    (50,   3,  "img"),
    (138,  4,  "img"),
    (224,  5,  "img"),
    (282,  6,  "img"),
    (344,  7,  "img"),
    (580,  8,  "img"),
    (711,  9,  "img"),
    (896,  10, "img"),
    (1021, 11, "img"),
    (1208, 12, "img"),
    (1503, 13, "img"),
    (1566, 14, "img"),
    (1708, 15, "flash"),
    (1743, 16, "minimax"),
    (1930, 17, "img"),
    (1974, 18, "img"),
    (1996, 19, "img"),
    (2050, 20, "img"),
    (2077, 21, "img"),
    (2178, 22, "img"),
    (2255, 23, "img"),
    (2285, 24, "img"),
    (2355, 25, "img"),
    (2428, 26, "img"),
    (2450, 27, "img"),
    (2520, None, None),  # end marker — no overlay
]

FLASH_PATH = IMAGES / "glm-flash-demo.mp4"
MINIMAX_PATH = IMAGES / "minimax-demo.mp4"
FLASH_DUR = 16   # seconds
MINIMAX_DUR = 20  # seconds


def slide_path(n):
    matches = list(SCREENSHOTS.glob(f"slide_{n:02d}_*.png"))
    if not matches:
        sys.exit(f"Missing screenshot for slide {n}")
    return matches[0]


def build():
    inputs = ["-i", str(BASE)]
    input_idx = 1  # 0 is the base video
    filters = []
    chain_label = "0:v"

    for i, (start, slide, typ) in enumerate(TIMELINE[:-1]):
        end = TIMELINE[i + 1][0]

        if typ == "img":
            path = slide_path(slide)
            inputs += ["-i", str(path)]
            filters.append(f"[{input_idx}:v]scale={SCALE}[s{input_idx}]")
            filters.append(
                f"[{chain_label}][s{input_idx}]overlay={OX}:{OY}"
                f":enable='between(t,{start},{end})'[t{input_idx}]"
            )
            chain_label = f"t{input_idx}"
            input_idx += 1

        elif typ == "flash":
            inputs += ["-itsoffset", str(start), "-i", str(FLASH_PATH)]
            clip_end = min(start + FLASH_DUR, end)
            filters.append(f"[{input_idx}:v]scale={SCALE}[s{input_idx}]")
            filters.append(
                f"[{chain_label}][s{input_idx}]overlay={OX}:{OY}"
                f":enable='between(t,{start},{clip_end})':eof_action=pass[t{input_idx}]"
            )
            chain_label = f"t{input_idx}"
            input_idx += 1

        elif typ == "minimax":
            inputs += ["-itsoffset", str(start), "-i", str(MINIMAX_PATH)]
            clip_end = min(start + MINIMAX_DUR, end)
            filters.append(f"[{input_idx}:v]scale={SCALE}[s{input_idx}]")
            filters.append(
                f"[{chain_label}][s{input_idx}]overlay={OX}:{OY}"
                f":enable='between(t,{start},{clip_end})':eof_action=pass[t{input_idx}]"
            )
            chain_label = f"t{input_idx}"
            input_idx += 1

    filter_complex = ";\n".join(filters)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", f"[{chain_label}]",
        "-map", "0:a",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "copy",
        str(OUT),
    ]
    return cmd


if __name__ == "__main__":
    cmd = build()
    print("Running ffmpeg with", sum(1 for x in cmd if x == "-i"), "inputs")
    print(f"Output: {OUT}\n")
    if "--dry" in sys.argv:
        print(" \\\n  ".join(cmd))
        sys.exit(0)
    subprocess.run(cmd, check=True)
    print(f"\nDone: {OUT}")
