#!/bin/sh
set -e

cd /hdd/monorepo
git config core.fileMode false

BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "ABORT: on branch '$BRANCH', expected 'main'" >&2
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "ABORT: repo has uncommitted changes — something modified the working tree" >&2
    git status --short >&2
    exit 1
fi

git pull --ff-only

if ! git verify-commit HEAD; then
    echo "ABORT: HEAD commit is not signed with a trusted GPG key" >&2
    exit 1
fi

./infra/0-ci/check-sec-invariant.py
./infra/0-ci/check-python-ast.py

chmod -R 777 .

docker compose build
if [ "$1" != "--no-pull" ]; then
    docker compose pull
fi
docker compose up -d --remove-orphans
