#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p models
model=models/face_landmarker.task
checksum=64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff
if [ -f "$model" ] && printf '%s  %s\n' "$checksum" "$model" | sha256sum --check --status; then
    exit 0
fi
temp=$(mktemp models/.face.XXXXXX)
trap 'rm -f -- "$temp"' EXIT
curl -fLSs --retry 2 \
    'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task' \
    -o "$temp"
printf '%s  %s\n' "$checksum" "$temp" | sha256sum --check --status
mv -- "$temp" "$model"
