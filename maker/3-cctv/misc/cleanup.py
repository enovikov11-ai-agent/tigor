import os
import time
import json

dir = "/var/www/html/"
keep_files = 1000
each_sec = 10

while True:
    try:
        files = sorted(f for f in os.listdir(dir) if f.startswith("video_"))
        remove = files[0:-keep_files]
        keep = files[-keep_files:]

        try:
            with open("index_videos.json", "w") as file:
                json.dump(keep, file)
        except Exception as e:
            print(e)

        for file in remove:
            try:
                os.remove(dir + file)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    
    time.sleep(each_sec)