# libcamera-vid -t 0 --codec yuv420 --width 1920 --height 1080 --framerate 30 --inline --output - 2>/dev/null | ffmpeg -f rawvideo -pix_fmt yuv420p -s 1920x1080 -i - -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='%{gmtime\\:%Y-%m-%d %H-%M-%S UTC+0}':x=30:y=30:fontsize=60:fontcolor=white:borderw=5:bordercolor=black" -c:v h264_v4l2m2m -g 10 -b:v 4M -f mpegts - 2>/dev/null | python /root/server.py

import time
import sys
import os
from datetime import datetime

CHUNK = 7 * 188
ROTATE_SEC = 10
ROOT = "/var/www/html"

eof_reached = False

while not eof_reached:
    unixtime = time.time() // ROTATE_SEC * ROTATE_SEC
    date_str = time.strftime("%Y-%m-%d", time.gmtime(unixtime))
    datetime_str = time.strftime("%Y-%m-%d_%H-%M-%S.ts", time.gmtime(unixtime))

    dirname = os.path.join(ROOT, date_str)
    filename = os.path.join(dirname, datetime_str)

    print(f"Opening {filename} for write")
    
    os.makedirs(dirname, exist_ok=True)
    file = open(filename, "wb")

    while time.time() < unixtime + ROTATE_SEC:
        buf = sys.stdin.buffer.read(CHUNK)

        if not buf:
            eof_reached = True
            break

        file.write(buf)
    
    file.close()
