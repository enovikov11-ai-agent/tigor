# hackrf_sweep -f 10:5990 -w 1000000 -l 16 -g 24 -N 600 -r sweep.csv

import json

maxval = {}

with open("sweep.csv", "r") as file:
    for line in file:
        _date, _time, _start, _end, _width, _n, _v1, _v2, _v3, _v4, _v5 = line.rstrip('\n').split(", ")

        end, start, width = int(_end), int(_start), int(float(_width))
        v1, v2, v3, v4, v5 = float(_v1), float(_v2), float(_v3), float(_v4), float(_v5)

        if end - start != width * 5:
            raise Exception("Bad data")
        
        strenghts = [(v1, start), (v2, start + width), (v3, start + 2 * width), (v4, start + 3 * width), (v5, start + 4 * width)]

        for value, frequency in strenghts:
            f_mhz = int(frequency / 1_000_000)

            if f_mhz not in maxval:
                maxval[f_mhz] = value
            
            maxval[f_mhz] = max(maxval[f_mhz], value)

with open("stat.json", "w") as file:
    json.dump(maxval, file)