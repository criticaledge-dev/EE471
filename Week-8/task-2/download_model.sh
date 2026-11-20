#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p models
model=models/pose_landmarker_lite.task
checksum=59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a
if [ -f "$model" ] && printf '%s  %s\n' "$checksum" "$model" | sha256sum --check --status; then
    exit 0
fi
temp=$(mktemp models/.pose.XXXXXX)
trap 'rm -f -- "$temp"' EXIT
curl -fLSs --retry 2 \
    'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task' \
    -o "$temp"
printf '%s  %s\n' "$checksum" "$temp" | sha256sum --check --status
mv -- "$temp" "$model"
