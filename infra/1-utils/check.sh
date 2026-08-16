#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python3 infra/ci/check-projects.py && python3 infra/ci/check-python-ast.py && python3 infra/ci/check-sec-invariant.py
