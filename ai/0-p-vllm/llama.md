https://unsloth.ai/docs/models/qwen3.5#qwen3.5-397b-a17b
https://github.com/ggml-org/llama.cpp/tree/master/tools/server

hf download unsloth/Qwen3.5-397B-A17B-GGUF \
    --local-dir unsloth/Qwen3.5-397B-A17B-GGUF \
    --include "*mmproj-F16*" \
    --include "*UD-Q4_K_XL" # Use "*UD-Q2_K_XL*" for Dynamic 2bit

--mmproj unsloth/Qwen3.5-397B-A17B-GGUF/mmproj-F16.gguf \

su box

~/llama.cpp/build/bin/llama-server --host 0.0.0.0 --port 1337 \
    --model /ssd/huggingface.co/unsloth/Qwen3.5-397B-A17B-GGUF/UD-Q4_K_XL/Qwen3.5-397B-A17B-UD-Q4_K_XL-00001-of-00006.gguf \
    --ctx-size 16384 --threads 64 --fit on --fit-target 70000


~/llama.cpp/build/bin/llama-server --host 0.0.0.0 --port 1337 \
    --model /ssd/huggingface.co/unsloth/Qwen3.5-397B-A17B-GGUF/UD-Q4_K_XL/Qwen3.5-397B-A17B-UD-Q4_K_XL-00001-of-00006.gguf \
    --ctx-size 262144 --threads 64

What I would tune next
First experiment (high impact)
--n-parallel 2

Why:

halves KV cache
frees VRAM
lets more expert weights stay on GPU
Second experiment
--ctx-size 8192

Same logic:

less KV = more room for weights
Third experiment (important)
--no-mmap

Test:

tokens/sec
latency stability
What “good” looks like now

You want: