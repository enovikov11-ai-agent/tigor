#!/usr/bin/env bash
# HF model integrity audit
#
# Discover (stdin: model names, or args):
#   find /ssd/internet/huggingface.co/ -mindepth 2 -maxdepth 2 -type d | sed 's|.*/huggingface.co/||' | sort
#
# Local hashes:
#   find /ssd/internet/huggingface.co/ -mindepth 3 -type f ! -name crc32.txt ! -name .gitkeep -exec sha256sum {} + \
#     | sed 's| .*/huggingface.co/||' | awk '{split($1,a,"/"); printf "%s/%s\t%s\t%s\n", a[1], a[2], $2, $1}'
#
# Remote hashes (this script) — input: models on stdin or args, output: model\tfname\tsha256\tsize
#
# Compare:
#   sort remote.tsv | diff - <(sort local.tsv)

set -euo pipefail

fetch() {
  local repo="$1"
  curl -sf -H "User-Agent: hf-audit/1.0" \
    "https://huggingface.co/api/models/${repo}/tree/main" | jq -r --arg r "$repo" '
    select(.lfs) |
    ((.lfs.oid // .lfs.sha256 // "") | sub("^0000000000000000"; "")) as $h |
    select($h != "") |
    [$r, .path, $h, (.size | tostring)] | @tsv'
}

if [ $# -gt 0 ]; then
  for r in "$@"; do fetch "$r"; done
else
  while IFS= read -r r; do [ -n "$r" ] && fetch "$r"; done
fi