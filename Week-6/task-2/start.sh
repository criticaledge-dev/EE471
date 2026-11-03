#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! docker image inspect ee471-week6-classifier:latest >/dev/null 2>&1; then
  printf '%s\n' 'Missing local classifier image. No registry pull was attempted.' \
    'First run inside task-2/classifier:' \
    'cog build -t ee471-week6-classifier --progress plain --use-cog-base-image=false' >&2
  exit 1
fi
docker compose build website
docker compose up -d --no-build --pull never --wait --wait-timeout 120
