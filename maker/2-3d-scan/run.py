import time
import serial
import subprocess

ser = serial.Serial('/dev/cu.usbserial-0001', 9600)

while True:
    subprocess.run(["gphoto2", "--capture-image"], stdout=subprocess.DEVNULL)
    ser.write(b"64\n")
    time.sleep(2)
