#!/usr/bin/env bash
set -euo pipefail

cd /out

# expected time: <1m, should capture ir: no, likely to trip braker: no
nvidia-smi -pl 600

# expected time: <1m, should capture ir: no, likely to trip braker: no
nvidia-smi | tee 00-nvidia-smi.txt

# expected time: <1m, should capture ir: no, likely to trip braker: no
nvidia-smi -q -d ECC,PAGE_RETIREMENT,ROW_REMAPPER | tee 00-health-before.txt

# expected time: <1m, should capture ir: no, likely to trip braker: no
dcgmi discovery -l | tee 01-discovery.txt

# expected time: 1-3m, should capture ir: no, likely to trip braker: no
dcgmi diag -r 2 -p "memory.is_allowed=true;pcie.is_allowed=true" -j | tee 02-r2.json

# expected time: 10-20m, should capture ir: maybe, likely to trip braker: yes
dcgmi diag -r pulse_test -p "pulse_test.is_allowed=true;pulse_test.test_duration=600" -j | tee 03-pulse-cold-10m.json

# expected time: 20-25m, should capture ir: yes, likely to trip braker: no
dcgmi diag -r targeted_power -p "targeted_power.is_allowed=true;targeted_power.test_duration=1200.0" -j | tee 04-power-20m.json

# expected time: 10-20m, should capture ir: yes, likely to trip braker: yes
dcgmi diag -r pulse_test -p "pulse_test.is_allowed=true;pulse_test.test_duration=600" -j | tee 05-pulse-warm-10m.json

# expected time: 2-10m, should capture ir: maybe, likely to trip braker: no
dcgmi diag -r memory_bandwidth -p "memory_bandwidth.is_allowed=true" -j | tee 06-memory-bandwidth.json

# expected time: 5-10m, should capture ir: maybe, likely to trip braker: no
dcgmi diag -r 3 -p "memory.is_allowed=true;pcie.is_allowed=true;diagnostic.is_allowed=true;targeted_stress.is_allowed=true;targeted_power.is_allowed=true" -j | tee 07-r3.json

# expected time: 15-45m, should capture ir: maybe, likely to trip braker: no
dcgmi diag -r 4 -p "memory.is_allowed=true;pcie.is_allowed=true;diagnostic.is_allowed=true;targeted_stress.is_allowed=true;targeted_power.is_allowed=true;memory_bandwidth.is_allowed=true;pulse_test.is_allowed=true" -j | tee 08-r4.json

# expected time: 1-3h, should capture ir: maybe, likely to trip braker: no
dcgmi diag -r 4 -p "memory.is_allowed=true;pcie.is_allowed=true;diagnostic.is_allowed=true;targeted_stress.is_allowed=true;targeted_power.is_allowed=true;memory_bandwidth.is_allowed=true;pulse_test.is_allowed=true;memtest.test0=true;memtest.test1=true;memtest.test2=true;memtest.test3=true;memtest.test4=true;memtest.test5=true;memtest.test6=true;memtest.test7=true;memtest.test8=true;memtest.test9=true;memtest.test10=true;memtest.test_duration=600" -j | tee 09-memtest-full.json

while true; do
  # expected time: 30-35m, should capture ir: yes, likely to trip braker: no
  dcgmi diag -r targeted_power -p "targeted_power.is_allowed=true;targeted_power.test_duration=1800.0" -j | tee "10-loop-power-$(date +%s).json"

  # expected time: 5-15m, should capture ir: yes, likely to trip braker: yes
  dcgmi diag -r pulse_test -p "pulse_test.is_allowed=true;pulse_test.test_duration=300" -j | tee "11-loop-pulse-$(date +%s).json"

  # expected time: 2-10m, should capture ir: maybe, likely to trip braker: no
  dcgmi diag -r memory_bandwidth -p "memory_bandwidth.is_allowed=true" -j | tee "12-loop-membw-$(date +%s).json"

  # expected time: <1m, should capture ir: no, likely to trip braker: no
  nvidia-smi -q -d ECC,PAGE_RETIREMENT,ROW_REMAPPER | tee "13-loop-health-$(date +%s).txt"
done