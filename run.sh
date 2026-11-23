#!/usr/bin/env bash
# Reproduces the whole benchmark: environment, concurrency sweep, measured runs,
# still-frame (preview) runs, output checks, frame grids and results.json.
#
#   ./setup.sh            # once: installs the pinned packages and browsers here
#   UF=/path/to/ultrafast ./run.sh [--fresh]
#
# --fresh starts results/runs.jsonl over; without it, new runs are appended.
# Every run waits for a quiet machine (no other render, little CPU or GPU load).
set -euo pipefail
cd "$(dirname "$0")"
BENCH=$PWD
source harness/env.sh
if [ -z "${UF:-}" ] || [ ! -x "$UF" ]; then
  echo "put the ultrafast 0.2.0 release on PATH, or set UF=/path/to/ultrafast" >&2
  exit 1
fi
mkdir -p results logs out frames
if [ "${1:-}" = "--fresh" ]; then
  rm -f results/runs.jsonl results/similarity.json
fi
python3 ultrafast/build.py
python3 -I harness/env_info.py > results/environment.json
python3 -I harness/bench.py sweep
python3 -I harness/bench.py sweep-vulkan
python3 -I harness/bench.py measure --warm 5
python3 -I harness/bench.py preview --preview-runs 3
python3 -I harness/verify.py
python3 -I harness/summarize.py
echo "done: results.json, frames/, README tables in results/tables.md"
