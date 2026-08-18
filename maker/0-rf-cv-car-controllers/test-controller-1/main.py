import sys
import time

while True:
    sys.stdin.write('w') # forward
    time.sleep(0.5)
    sys.stdin.write('s') # backward
    time.sleep(0.5)
    sys.stdin.write('q') # forward-left
    time.sleep(0.5)
    sys.stdin.write('c') # backward-right
    time.sleep(0.5)
