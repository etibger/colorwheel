#!/usr/bin/env bash
# Exit on errors, undefined vars, and failed pipes
set -euo pipefail

echo "Generating image with data source..."
# Run the main script to produce the output PNG
uv run main.py --use-data --data-file data/golden.ods

echo "Comparing generated image to golden..."
# Compare outputs quietly, exit non-zero if they differ
if ! cmp -s "color_wheel_with_legend.png" "data/golden.png"; then
  echo "ERROR: Generated image does not match data/golden.png" >&2
  exit 1
fi

echo "Image matches golden reference."
