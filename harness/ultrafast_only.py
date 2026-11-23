"""Measures ultrafast's rows again with the same harness (quiet-machine waits, cgroup
timing, output checks), leaving Remotion's and HyperFrames' rows as they are. Per scene:
a cold export (ultrafast's caches cleared) and five warm ones, as `bench.py measure`
does (the cold run is the warm-up); then a warm-up and three warm still frames, as
`bench.py preview` does. ultrafast 0.2.0's rows were measured this way.

    UF=/path/to/ultrafast python3 -I harness/ultrafast_only.py [title,chart,footage,effects]

Move ultrafast's earlier records out of results/runs.jsonl first (summarize.py counts
every record in it), then run verify.py and summarize.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench  # noqa: E402

comps = sys.argv[1].split(",") if len(sys.argv) > 1 else ["title", "chart", "footage", "effects"]
for comp in comps:
    out = bench.out_path(comp, "ultrafast", "default")
    argv, cwd = bench.command("ultrafast", "default", comp, out)
    bench.reset_caches("ultrafast")
    bench.run_once("measure", "ultrafast", "default", comp, "cold", 1, argv, cwd, out)
    for i in range(5):
        bench.run_once("measure", "ultrafast", "default", comp, "warm", i + 1, argv, cwd, out)
for comp in comps:
    out = os.path.join(bench.OUT, comp, "ultrafast-preview.png")
    argv, cwd = bench.preview_command("ultrafast", comp, out)
    bench.run_once("preview", "ultrafast", "default", comp, "warmup", 0, argv, cwd, out, check_video=False)
    for i in range(3):
        bench.run_once("preview", "ultrafast", "default", comp, "warm", i + 1, argv, cwd, out, check_video=False)
print("done")
