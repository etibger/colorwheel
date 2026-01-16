#!/usr/bin/env bash
# Exit on errors, undefined vars, and failed pipes
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Generating image with data source..."
# Run the main script to produce the output PNG
if command -v uv >/dev/null 2>&1; then
  uv run -m apps.main --use-data --data-file data/golden.ods
else
  PYTHON="${PYTHON:-}"
  if [[ -z "$PYTHON" ]]; then
    if [[ -x ".venv/bin/python3" ]]; then
      PYTHON=".venv/bin/python3"
    elif [[ -x ".venv/bin/python" ]]; then
      PYTHON=".venv/bin/python"
    else
      PYTHON="python3"
    fi
  fi
  "$PYTHON" -m apps.main --use-data --data-file data/golden.ods
fi

echo "Comparing generated image to golden..."
# Compare outputs quietly, exit non-zero if they differ
if ! cmp -s "color_wheel_with_legend.png" "data/golden.png"; then
  echo "ERROR: Generated image does not match data/golden.png" >&2
  exit 1
fi

echo "Image matches golden reference."
