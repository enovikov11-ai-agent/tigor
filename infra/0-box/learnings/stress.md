apt install stress-ng git build-essential nvidia-cuda-toolkit

git clone https://github.com/wilicc/gpu-burn.git
cd gpu-burn
make -j128

stress-ng --matrix 128 --timeout 30h --metrics-brief

/home/box/gpu-burn/gpu_burn 300000

CPU only: 1776.74 ops/s
GPU only: 26333 Gflop/s
CPU+GPU: 1773.89 ops/s + 26175 Gflop/s

https://p-zigbee.tgr.rs/
