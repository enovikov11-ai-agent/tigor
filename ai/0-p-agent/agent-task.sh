#!/usr/bin/env bash
set -euo pipefail

BRANCH="$(date +%F_%H-%M-%S)"

trap 'rm -rf "/work/$BRANCH"' ERR

git clone --depth=1 --no-progress --quiet "http://cdbot:$GIT_PASS@p-forgejo:3000/tigor/monorepo.git" "/work/$BRANCH"
cd "/work/$BRANCH"

git checkout -b "$BRANCH"

case "$COMMAND" in
  cd) cd -p "$PAYLOAD" --dangerously-skip-permissions --append-system-prompt "$(cat meta.md)" ;;
  qwen) opencode run --model p-vllm/qwen3-next-80b "$PAYLOAD" ;;
  minimax) opencode run --model p-llama/minimax-m2.5 "$PAYLOAD" ;;
  *) echo "Unknown COMMAND: $COMMAND" >&2; exit 1 ;;
esac

git add .
git commit -m "$PAYLOAD"

git push --set-upstream origin "$BRANCH"

COMMIT_HASH=$(git rev-parse HEAD)

echo "https://p-forgejo.tgr.rs/tigor/monorepo/compare/main...$BRANCH"
echo ""
echo "git cherry-pick $COMMIT_HASH"
