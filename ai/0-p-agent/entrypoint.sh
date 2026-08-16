#!/bin/bash
set -e

git config --global user.email "cd-bot@localhost"
git config --global user.name "cd Bot"
git config --global init.defaultBranch main

exec python3 /app/main.py
