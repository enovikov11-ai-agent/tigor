nvidia-smi --lock-gpu-clocks=300,2400
nvidia-smi -pl 450

55°C -> 30%
70°C -> 50%
77°C -> 100%

# Monitor

watch -n 2 'ipmitool sdr elist | grep -E "degrees" | grep -v "CPU0_DTS"'

nvidia-smi --query-gpu=timestamp,power.draw,power.limit,temperature.gpu,clocks.sm,clocks.mem,clocks.gr,clocks_throttle_reasons.active,utilization.gpu,utilization.memory,fan.speed -lms 1000

# Burn (started 22:30)

nvidia-smi -pl 600
kubectl scale deployment p-vllm --replicas=0
podman run --rm -it --device nvidia.com/gpu=all gpu_burn ./gpu_burn 1000000
nix-shell -p stress-ng --run 'stress-ng --cpu 128 --cpu-method matrixprod --vm 16 --vm-bytes 90% --vm-method all --vm-keep --vm-populate --page-in --aggressive --metrics-brief --timeout 1000000s'

# Manual GPU fans

nvidia-settings -a "[fan:0]/GPUTargetFanSpeed=100" --display :0
nvidia-settings -a "[gpu:0]/GPUFanControlState=0" --display :0

# Prepare

git clone https://github.com/wilicc/gpu-burn
cd gpu-burn
docker build -t gpu_burn .

# BMC fan config

Fans controlled by BMC, only 1 active policy, cannot use CPU0_DTS; GPU 450W

30% - quiet
50% - can be heard but kinda ok
60% - loud

GPU
85C - do not exceed, will last <3 years
75C - best for 3–5 years lifespan
70C - 5–7 years

## Power budget

| Component                        | idle (W) | normal (W) | peak (W) |
| -------------------------------- | -------: | ---------: | -------: |
| 1x RTX PRO 6000 Blackwell        |       25 |        250 |      600 |
| 1x AMD EPYC 7702P                |       35 |        120 |      280 |
| 16x Kingston 32GB DDR4 ECC RDIMM |       48 |         80 |      128 |
| 4x Seagate IronWolf Pro 18TB HDD |       21 |         32 |      100 |
| Chassis                          |        9 |         27 |       54 |
| 1x Gigabyte MZ32-AR0             |       25 |         40 |       60 |
| 4x Kingston NV3 2TB NVMe         |        2 |         12 |       24 |
| Total                            |      165 |        561 |     1246 |

# GPU test (not works)

mkdir -p gpu-test
podman run --rm -it \
  --name gpu-test \
  --privileged \
  --pid=host \
  --ipc=host \
  --device nvidia.com/gpu=all \
  -v "$PWD/gpu-test-no-oc:/out" \
  --entrypoint bash \
  nvcr.io/nvidia/cloud-native/dcgm:4.5.2-1-ubuntu22.04 \
  -lc 'nv-hostengine -f /var/log/nv-hostengine.log & sleep 3; cd /out; bash'

NIXPKGS_ALLOW_UNFREE=1 nix-shell --impure \
  -p cudaPackages.cuda_nvcc \
  -p cudaPackages.cuda_cudart \
  -p cudaPackages.libcublas \
  -p gcc \
  --run 'nvcc -O3 -arch=sm_120 shake.cu -lcublas -o gpu-shaker'
