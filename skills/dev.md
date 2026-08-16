# Development Patterns

## Python subprocess

- `text=True` returns strings; without it you get bytes. Common pitfall when parsing output.
- Subprocess timestamp pattern: see `ai/0-p-agent/README.md`.

## Python testing

Test isolation: mock dependencies not installed locally. Handler rename checklist — see `ai/0-p-agent/README.md`.

## Telegram Bot Pattern

Python bots use `python-telegram-bot`. Reference: `telegram/0-yahonkbot/main.py`. Startup pattern with `post_init` — see `ai/0-p-agent/README.md`.

## Terminal Progress Output

For CLI scripts processing many items: overwrite current line for OK, preserve failures on separate lines. `\r\033[K` pattern.

## Switching Tools/Frameworks

When replacing tool A with tool B: read all related files first (READMEs, Dockerfiles). Identify data format mismatches early (GGUF vs safetensors). Don't blindly copy security fields (`user:`) — verify new tool's requirements. Don't assume equivalent resource usage.

## Wrapper/Runner Scripts

Adapt the runner to the tool's expectations (CWD, paths). Don't modify working tools to make the wrapper "cleaner".

Reusable repo-root runner pattern:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/../.."  # lands at repo root
python3 infra/0-ci/some-check.py
```

## Replacing Multi-Effect Commands

When replacing a command that does multiple things, enumerate ALL effects first. Ensure each is covered. Example: `git checkout -f main` does (1) reset dirty state AND (2) ensure branch is main. Replacing with a dirty-state check without a branch check loses effect (2).

## Shell Command Formatting

When giving the user a list of files/paths to act on (rm, mv, cp), present as a single command with `\` line continuations — one path per line, order matching a logical reference (e.g. `git status` output).

## git pull in Automation

Always `git pull --ff-only` — plain `git pull` silently creates merge commits on diverged history. `--ff-only` aborts cleanly instead.

## Fetching URLs

Use `curl -s` when exact field names matter (JSON schemas, API specs) — some agent fetch tools summarize/transform content. Pipe large output through `head -200`. Cache to `./tmp/` if referencing repeatedly.
