# HuggingFace Models to Download

Downloaded to VM via VPS+SSHFS pipeline. VM has no direct internet.

**Target:** `/ssd/vm/hermes/huggingface.co/` on VM (10.67.69.2)

## Already on VM (read-write) — All Complete ✅

| # | HF Repo | Path on VM | Size |
|---|---|---|---|
| 1 | `Qwen/Qwen3.8-27B` | `/ssd/vm/hermes/huggingface.co/Qwen/Qwen3.8-27B/` | 52G (BF16) |
| 2 | `Qwen/Qwen3.8-27B-FP8` | `/ssd/vm/hermes/huggingface.co/Qwen/Qwen3.8-27B-FP8/` | 29G (FP8) |
| 3 | `google/gemma-4-31B-it` | `/ssd/vm/hermes/huggingface.co/google/gemma-4-31B-it/` | 58G |
| 4 | `heretic-org/Qwen3.8-27B-heretic-ara` | `/ssd/vm/hermes/huggingface.co/heretic-org/Qwen3.8-27B-heretic-ara/` | 52G |
| 5 | `wangzhang/Qwen3.8-27B-abliterated` | `/ssd/vm/hermes/huggingface.co/wangzhang/Qwen3.8-27B-abliterated/` | 51G |
| 6 | `trohrbaugh/gemma-4-31b-it-heretic-ara` | `/ssd/vm/hermes/huggingface.co/trohrbaugh/gemma-4-31b-it-heretic-ara/` | 58G |
| 7 | `wangzhang/gemma-4-31B-it-abliterated` | `/ssd/vm/hermes/huggingface.co/wangzhang/gemma-4-31B-it-abliterated/` | 58G |
| 8 | `MiniMaxAI/MiniMax-H3` | `/ssd/vm/hermes/huggingface.co/MiniMaxAI/MiniMax-H3/` | 19M ⚠️ partial |

**Total on VM: ~358G + HF cache 120G in /ssd/vm/hermes/.hf_cache/**

## Notes

- gemma-4-31B-it is gated — requires HF auth token
- All abliterated/derivative repos are based on Qwen3.8-27B or gemma-4-31B-it
- Download script: `~/.hermes/scripts/hf_download/phase12.py` (VPS, uses SSHFS cache)
