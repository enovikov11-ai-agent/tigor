#!/usr/bin/env python3
import re
import subprocess

LIMITS = {
    "CPU0_TEMP": 75,
    "DIMMG0_TEMP": 75,
    "DIMMG1_TEMP": 75,
    "GPU_CORE_TEMP": 83,
    "M2_G0_AMB_TEMP": 60,
    "MB_TEMP1": 65,
    "MB_TEMP2": 60,
    "VR_DIMMG0_TEMP": 80,
    "VR_DIMMG1_TEMP": 80,
    "VR_P0_TEMP": 85,
}

def run(cmd):
    return subprocess.check_output(cmd, text=True)

temps = {}

gpu_out = run([
    "nvidia-smi",
    "--query-gpu=temperature.gpu,fan.speed",
    "--format=csv,noheader,nounits",
]).strip()

gpu_temp, gpu_fan = [int(x.strip()) for x in gpu_out.split(",", 1)]
temps["GPU_CORE_TEMP"] = gpu_temp

ipmi_out = run(["ipmitool", "sdr", "elist"])

for line in ipmi_out.splitlines():
    if "degrees C" not in line or "CPU0_DTS" in line:
        continue

    key = line.split("|", 1)[0].strip()
    m = re.search(r"(-?\d+)\s+degrees C", line)

    if key in LIMITS and m:
        temps[key] = int(m.group(1))

print(f"GPU_FAN_SPEED {gpu_fan}%")

items = []

for key, limit in LIMITS.items():
    if key not in temps:
        continue

    margin = limit - temps[key]
    items.append((margin, key))

for margin, key in sorted(items):
    print(f"{key} margin {margin:+d}C")
