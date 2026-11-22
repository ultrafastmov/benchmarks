#!/usr/bin/env python3
"""Build results.json from timings.jsonl (run.sh) and tokens.json (tokens.py); print the tables.

python3 -I summarize.py
"""
import json
import statistics
import subprocess
from pathlib import Path

B = Path(__file__).resolve().parent
FRAMES = 300  # 10 s at 30 fps


def sh(*cmd, cwd=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd).stdout.strip()
    except OSError:
        return ""


runs = [json.loads(l) for l in (B / "timings.jsonl").read_text().splitlines() if l.strip()]

# Another agent started its own timed benchmark on this machine at 05:25 IST (2026-11-22). A run whose
# log was created (= the run started) at or after that is kept out of the medians and listed separately.
import datetime
CUTOFF = datetime.datetime(2026, 11, 22, 5, 25, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
for r in runs:
    log = B / "out/logs" / f"{r['config'].replace('/', '_')}.{r['phase']}{r['round']}.log"
    born = int(sh("stat", "-c", "%W", str(log)) or 0)
    r["started"] = datetime.datetime.fromtimestamp(born, CUTOFF.tzinfo).isoformat(timespec="seconds")
    r["after_cutoff"] = born >= CUTOFF.timestamp()
late = [r for r in runs if r["after_cutoff"]]
runs = [r for r in runs if not r["after_cutoff"]]
tokens = json.loads((B / "tokens.json").read_text())
disc = B / "out/discarded.jsonl"
discarded = [json.loads(l) for l in disc.read_text().splitlines() if l.strip()] if disc.exists() else []

configs = {}
for r in runs:
    c = configs.setdefault(r["config"], dict(config=r["config"], cmd=r["cmd"], warmup_s=None, runs_s=[], busy_cores_before=[],
                                             gpu_util_before=[], foreign_cores_during=[], frames=[], bytes=None, rc=[]))
    if r["phase"] == "warmup":
        c["warmup_s"] = r["wall_s"]
    else:
        c["runs_s"].append(r["wall_s"])
        c["busy_cores_before"].append(r["before"]["busy_cores"])
        c["gpu_util_before"].append(r["before"]["gpu_util"])
        c["foreign_cores_during"].append(r["foreign_cores"])
        c["frames"].append(r["frames"])
        c["rc"].append(r["rc"])
        c["bytes"] = r["bytes"]
for c in configs.values():
    if c["runs_s"]:
        med = statistics.median(c["runs_s"])
        c["median_s"] = med
        c["min_s"], c["max_s"] = min(c["runs_s"]), max(c["runs_s"])
        c["render_fps"] = round(FRAMES / med, 1)
        c["realtime_x"] = round(10 / med, 2)
        c["mbit_per_s"] = round(c["bytes"] * 8 / 10 / 1e6, 1) if c["bytes"] else None
        c["all_frames_ok"] = all(f == FRAMES for f in c["frames"]) and all(rc == 0 for rc in c["rc"])

result = {
    "date": "2026-11-22",
    "job": "10 s vertical short, 1080x1920, 30 fps, H.264 MP4: NASA footage background (cover), a title that animates in, "
           "three detail lines, word-timed captions (15 words, 3.0-9.6 s), colour grade (exposure -0.2, contrast up, "
           "saturation down) and film grain (matched: added noise std ~2.45/255 in a flat 360x360 crop at 4.8 s)",
    "footage": {"file": "iss_earth_limb.mp4 (copied into each project)", "source": "NASA, jsc2021m000138 4K Earth Views "
                "(public domain), cut in ~/ultrafast-site/footage", "format": "H.264 1920x1080 30 fps 20 s",
                "sha256": sh("sha256sum", str(B / "ultrafast/footage.mp4")).split(" ")[0]},
    "machine": {
        "cpu": "AMD Ryzen 9 9950X3D2 (16 cores, 32 threads)", "gpu": "NVIDIA GeForce RTX 5090",
        "driver": sh("nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"),
        "os": sh("cat", "/etc/fedora-release") + ", kernel " + sh("uname", "-r"),
        "node": sh("node", "--version"), "ffmpeg": sh("sh", "-c", "ffmpeg -version | head -1"),
        "note": "shared machine: other agents ran light browser work; run.sh waits for 1-min load < 4 and GPU < 15% "
                "before each timed run and logs both",
    },
    "versions": {
        "ultrafast": {"version": sh(str(B / "bin/ultrafast"), "--version"), "binary_sha256": sh("sha256sum", str(B / "bin/ultrafast")).split(" ")[0],
                      "source": "copy of ~/ultrafast/target/release/ultrafast (built 2026-11-22 01:54 IST, checkout 9e59a55)",
                      "backend": "Vulkan"},
        "remotion": {"remotion": "4.0.545", "packages": "@remotion/cli, media, effects, captions, google-fonts, layout-utils 4.0.545",
                     "browser": (B / "remotion/node_modules/.remotion/chrome-headless-shell/VERSION").read_text().strip(),
                     "scaffold": "npx create-video@4.0.545 --yes --blank --skills remotion"},
        "hyperframes": {"hyperframes": "0.9.79", "browser": "chrome-headless-shell 158.0.8127.36", "gsap": "3.15.0",
                        "scaffold": "npx hyperframes@0.9.79 init hyperframes --example blank --resolution portrait --non-interactive"},
    },
    "timing_method": "wall clock of the render command (timeit.py), 1 warm-up then 3 timed runs per config, rounds "
                     "interleaved across tools; each run starts when the machine is quiet (quiet.py) and is discarded and "
                     "repeated if other processes used > 1.5 cores during it",
    "discarded_runs": len(discarded),
    "excluded_after_0525": {
        "why": "another agent began a timed benchmark at 05:25 IST; runs that started then or later may be contaminated "
               "(GPU load is not seen by the CPU check), so they are not in any median",
        "runs": [{k: r[k] for k in ("config", "phase", "round", "started", "wall_s", "foreign_cores", "frames")} for r in late],
    },
    "single_clean_runs_not_in_medians": {
        "note": "Remotion with --gl=vulkan (WebGL on the RTX 5090), timed once each before 05:25 IST: a concurrency sweep "
                "with timeit.py and the harness warm-ups. Its three timed rounds started after 05:25 and are excluded.",
        "remotion --gl=vulkan --concurrency=4": 7.077, "remotion --gl=vulkan (concurrency 8, default)": 7.037,
        "remotion --gl=vulkan --concurrency=12 (other processes used 1.41 cores)": 9.106,
        "remotion --gl=vulkan --concurrency=16": 10.447,
        "remotion/gl-vulkan warm-up (05:24:32)": 7.287, "remotion/gl-vulkan-nvenc warm-up (05:24:46)": 6.742,
        "remotion/4k-gl-vulkan warm-up (05:24:57)": 12.02,
    },
    "timings": configs,
    "token_method": "tiktoken o200k_base. 'edits' (headline): what the agent types after the tool's own scaffold step "
                    "(ultrafast new vertical / create-video --blank / hyperframes init): new files in full, added or changed "
                    "lines of scaffold files (unified diff '+' lines), and commands that carry content. 'whole': full text of "
                    "every file the agent creates or edits. Code written by the tools' CLIs (Remotion Element source, "
                    "HyperFrames' expanded grading attribute, scaffolds) is listed under generated_not_counted. Excluded: "
                    "lockfiles, node_modules, package.json changes made by CLIs, render commands.",
    "tokens": tokens,
    "shotstack": json.loads((B / "shotstack/facts.json").read_text()),
}
# Render timings are reported by the shared benchmark, not here: the local runs are kept only for reference.
LOCAL = ("timing_method", "discarded_runs", "excluded_after_0525", "single_clean_runs_not_in_medians", "timings")
local = {k: result.pop(k) for k in LOCAL}
local["status"] = "NOT FOR PUBLICATION: render timings come from the shared benchmark; these local runs are reference only"
(B / "out/local-timings-not-published.json").write_text(json.dumps(local, indent=2) + "\n")
result["render_timings"] = "not reported here (they come from the shared benchmark); local runs: out/local-timings-not-published.json"
(B / "results.json").write_text(json.dumps(result, indent=2) + "\n")

print("| config | median s | runs s | fps | warm-up s | MB | Mbit/s | frames ok |")
print("|---|---|---|---|---|---|---|---|")
for c in configs.values():
    if not c["runs_s"]:
        continue
    print(f"| {c['config']} | {c['median_s']:.2f} | {', '.join(f'{x:.2f}' for x in c['runs_s'])} | {c['render_fps']} | "
          f"{c['warmup_s']:.2f} | {c['bytes'] / 1e6:.1f} | {c['mbit_per_s']} | {c['all_frames_ok']} |")
print()
for t, v in tokens["tools"].items():
    print(t, "edits", v["edits"], "whole", v["whole"], [(f["file"], f["edits"], f["whole"]) for f in v["files"]])
