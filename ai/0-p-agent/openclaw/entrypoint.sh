#!/bin/sh
set -e
mkdir -p "$HOME/.openclaw/workspace"
if [ ! -f "$HOME/.openclaw/openclaw.json" ]; then
    cp /etc/openclaw-default.json "$HOME/.openclaw/openclaw.json"
fi
exec openclaw gateway --port 18789 --bind lan
