#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python3 prepare_build.py
for model in baseline optimized; do
  (cd "outputs/build/$model" && cog build -t "ee471-week7-cifar10-$model" --progress plain --use-cog-base-image=false)
  expected=$(python3 -c "import json; print(json.load(open('outputs/build/$model/model_config.json'))['sha256'])")
  actual=$(docker run --rm --network none --entrypoint python "ee471-week7-cifar10-$model" -c 'import hashlib; print(hashlib.sha256(open("/src/checkpoint.pth","rb").read()).hexdigest())')
  if [ "$expected" != "$actual" ]; then
    printf '%s\n' "$model image checkpoint SHA256 mismatch" >&2
    exit 1
  fi
  printf '%s\n' "$model IMAGE_SHA256_OK $actual"
done
docker compose --env-file /dev/null build website
