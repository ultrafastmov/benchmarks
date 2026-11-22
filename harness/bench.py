#!/usr/bin/env python3
"""Runs the benchmark matrix and appends one JSON line per run to results/runs.jsonl.

Every run:
  1. waits until the machine is quiet (CPU, GPU, no other renderer running);
  2. runs the tool's documented command in its own cgroup (runner.py), timing the
     whole command and sampling memory; nvidia-smi samples the GPU meanwhile;
  3. checks the output (frame count, duration, size, codec) with ffprobe;
  4. is thrown away and repeated if other work on the machine took more than
     QUIET_CORES of CPU on average while it ran (it is still logged, flagged).

Phases (see run.sh): sweep (find each browser tool's fastest concurrency on this
machine), measure (cold + warm runs per configuration), preview (one still frame).
Stdlib only; needs systemd-run (cgroup v2), nvidia-smi and ffprobe.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import uuid

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BENCH, "results")
OUT = os.path.join(BENCH, "out")
LOGS = os.path.join(BENCH, "logs")
RUNNER = os.path.join(BENCH, "harness", "runner.py")
FFMPEG_DIR = os.path.join(BENCH, "tools", "ffmpeg", "ffmpeg-n9.0.2-61-gd59078794d-linux64-gpl-9.0", "bin")

COMPS = {"title": (1080, 1920), "chart": (1920, 1080), "footage": (1080, 1920), "effects": (1920, 1080)}
FRAMES = 300
CRF = "18"
PREVIEW_T = 5.0  # the still-frame (preview) measurement renders frame 150

QUIET_CORES = 1.5      # other work allowed on the machine, in busy CPU threads
                       # (this desktop idles at about 0.2 to 1.0)
QUIET_GPU_UTIL = 15.0  # % GPU utilisation allowed before a run starts
# Another renderer on the machine means "not quiet". Matched on what a process
# runs (its executable, or the CLI a node process runs), not on the text of shell
# scripts, which can mention these names without running them.
RENDERER_EXES = re.compile(r"^(chrome-headless-shell|chrome|chromium|ffmpeg|ultrafast|uf|blender|steam|"
                           r"gamescope|wineserver|wine64-preloader|.*\.exe)$")
NODE_CLI = re.compile(r"(remotion|hyperframes)\S*\s+(render|still|benchmark|snapshot)\b")


def log(msg):
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------
def uf_binary():
    uf = os.environ.get("UF") or shutil.which("ultrafast")
    if not uf:
        sys.exit("set UF=/path/to/ultrafast (the release binary to measure)")
    return uf


def tool_env(tool):
    env = dict(os.environ)
    env["XDG_CACHE_HOME"] = os.path.join(BENCH, ".cache", f"xdg-{tool}")
    os.makedirs(env["XDG_CACHE_HOME"], exist_ok=True)
    if tool == "hyperframes":
        # HyperFrames' MP4 path needs an FFmpeg with libx264 (its docs: apt/brew ffmpeg);
        # Fedora's ffmpeg-free has none, so point it at a standard static build.
        env["HYPERFRAMES_FFMPEG_PATH"] = os.path.join(FFMPEG_DIR, "ffmpeg")
        env["HYPERFRAMES_FFPROBE_PATH"] = os.path.join(FFMPEG_DIR, "ffprobe")
        env["PATH"] = FFMPEG_DIR + os.pathsep + env["PATH"]
    return env


def command(tool, config, comp, out):
    """(argv, cwd) for one configuration: default; Remotion cN (--concurrency N),
    bundled-cN (prebuilt bundle), angle-egl; HyperFrames wN (--workers N), gpu, gpu-wN."""
    if tool == "ultrafast":
        return [uf_binary(), "export", f"{comp}.json", out, "--crf", CRF], os.path.join(BENCH, "ultrafast")
    if tool == "remotion":
        # bundled: render from a bundle made once by `npx remotion bundle` (skips webpack)
        entry = "build" if config.startswith("bundled") else "src/index.ts"
        argv = ["npx", "remotion", "render", entry, comp, out, "--crf", CRF]
        m = re.search(r"(?:^|-)c(\d+)$", config)
        if m:
            argv += ["--concurrency", m.group(1)]
        if "angle-egl" in config:
            argv += ["--gl=angle-egl"]
        if "vulkan" in config:
            argv += ["--gl=vulkan"]
        if "nvenc" in config:
            # Remotion uses NVENC on Linux with --hardware-acceleration, but not together
            # with --crf (it would fall back to libx264), so this one runs at NVENC's default quality
            argv.remove("--crf")
            argv.remove(CRF)
            argv += ["--hardware-acceleration", "if-possible"]
        return argv, os.path.join(BENCH, "remotion")
    if tool == "hyperframes":
        argv = ["npx", "hyperframes", "render", "-o", out, "--crf", CRF]
        m = re.search(r"(?:^|-)w(\d+)$", config)
        if m:
            argv += ["--workers", m.group(1)]
        if "gpu" in config:
            argv += ["--gpu"]
        return argv, os.path.join(BENCH, "hyperframes", comp)
    raise ValueError(tool)


def preview_command(tool, comp, out_png):
    t = PREVIEW_T
    if tool == "ultrafast":
        return [uf_binary(), "render", f"{comp}.json", "--at", str(t), "--out", out_png], os.path.join(BENCH, "ultrafast")
    if tool == "remotion":
        return (["npx", "remotion", "still", "src/index.ts", comp, out_png, f"--frame={int(round(t * 30))}"],
                os.path.join(BENCH, "remotion"))
    if tool == "hyperframes":
        return (["npx", "hyperframes", "snapshot", "--at", str(t), "--no-end", "-o", out_png],
                os.path.join(BENCH, "hyperframes", comp))
    raise ValueError(tool)


def reset_caches(tool):
    """What 'cold' means: the tool's own on-disk caches are gone (compiled kernels,
    bundles, extracted video frames). The OS page cache is not dropped (needs root)."""
    shutil.rmtree(os.path.join(BENCH, ".cache", f"xdg-{tool}"), ignore_errors=True)
    if tool == "remotion":
        shutil.rmtree(os.path.join(BENCH, "remotion", "node_modules", ".cache"), ignore_errors=True)
    if tool == "hyperframes":
        extract = os.environ.get("HYPERFRAMES_EXTRACT_CACHE_DIR", os.path.join(BENCH, ".cache", "hyperframes-extract"))
        shutil.rmtree(extract, ignore_errors=True)
        os.makedirs(extract, exist_ok=True)
        hf = os.environ.get("HYPERFRAMES_CACHE_DIR", os.path.join(BENCH, ".cache", "hyperframes"))
        for name in os.listdir(hf) if os.path.isdir(hf) else []:
            if name not in ("chrome", "locks"):  # keep the downloaded browser
                p = os.path.join(hf, name)
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
        for comp in COMPS:
            shutil.rmtree(os.path.join(BENCH, "hyperframes", comp, ".hyperframes"), ignore_errors=True)


# ---------------------------------------------------------------------------
# quiet machine
# ---------------------------------------------------------------------------
def busy_jiffies():
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    return sum(v[:8]) - v[3] - v[4], sum(v[:8])


def cpu_busy_cores(seconds=2.0):
    b0, _ = busy_jiffies()
    time.sleep(seconds)
    b1, _ = busy_jiffies()
    return (b1 - b0) / os.sysconf("SC_CLK_TCK") / seconds


def proc_ticks():
    out = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                head, rest = f.read().rsplit(")", 1)
            fields = rest.split()
            out[int(pid)] = (head.split("(", 1)[1], int(fields[11]) + int(fields[12]))
        except (OSError, IndexError, ValueError):
            pass
    return out


PF_KTHREAD = 0x00200000


def user_proc_ticks():
    """CPU ticks of every user-space process (kernel threads left out): {pid: (name, ticks)}."""
    out = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                head, rest = f.read().rsplit(")", 1)
            fields = rest.split()
            if int(fields[6]) & PF_KTHREAD:
                continue
            out[int(pid)] = (head.split("(", 1)[1], int(fields[11]) + int(fields[12]))
        except (OSError, IndexError, ValueError):
            pass
    return out


def machine_load(seconds=3.0):
    """CPU use of everything on the machine over a few seconds, the load average, and
    the processes using the most CPU meanwhile (recorded with every run)."""
    hz = os.sysconf("SC_CLK_TCK")
    p0 = proc_ticks()
    b0, _ = busy_jiffies()
    time.sleep(seconds)
    b1, _ = busy_jiffies()
    p1 = proc_ticks()
    top = sorted(((t1 - p0[pid][1], name) for pid, (name, t1) in p1.items() if pid in p0),
                 reverse=True)[:3]
    with open("/proc/loadavg") as f:
        la = [float(x) for x in f.read().split()[:3]]
    return {
        "busy_threads": round((b1 - b0) / hz / seconds, 2),
        "loadavg_1_5_15": la,
        "top_processes": [{"name": n, "threads": round(d / hz / seconds, 2)} for d, n in top if d > 0],
    }


def gpu_util(samples=4):
    vals = []
    for _ in range(samples):
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True)
        try:
            vals.append(float(r.stdout.strip().splitlines()[0]))
        except (ValueError, IndexError):
            pass
        time.sleep(0.4)
    return statistics.mean(vals) if vals else 0.0


def in_bench_scope(pid):
    try:
        with open(f"/proc/{pid}/cgroup") as f:
            return "ufbench-" in f.read()
    except OSError:
        return False


def renderer_procs():
    """Other renderers on the machine: {pid: (description, cpu ticks)}."""
    me = os.getpid()
    found = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me or in_bench_scope(pid):
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argv = [a.decode(errors="replace") for a in f.read().split(b"\0") if a]
            if not argv:
                continue
            exe = os.path.basename(argv[0])
            if not (RENDERER_EXES.match(exe) or (exe == "node" and NODE_CLI.search(" ".join(argv[1:4])))):
                continue
            with open(f"/proc/{pid}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
            ticks = int(fields[11]) + int(fields[12])  # utime + stime
        except (OSError, IndexError, ValueError):
            continue
        found[int(pid)] = (f"{pid}: {' '.join(argv)[:160]}", ticks)
    return found


def active_renderers(before, after, min_ticks):
    """Renderers that started, or used more than min_ticks of CPU, between two snapshots.
    An idle browser someone left open does not count; one that is rendering does."""
    out = []
    for pid, (desc, ticks) in after.items():
        if pid not in before or ticks - before[pid][1] > min_ticks:
            out.append(desc)
    return out


def foreign_renderers():
    """Kept for a quick look: every other renderer process, active or not."""
    return [d for d, _t in renderer_procs().values()]


def wait_quiet(max_wait_s=4 * 3600):
    t0 = time.time()
    waited = 0
    while True:
        snap = renderer_procs()
        load = machine_load()
        cores = load["busy_threads"]
        others = active_renderers(snap, renderer_procs(), min_ticks=10)
        gpu = gpu_util()
        if not others and cores <= QUIET_CORES and gpu <= QUIET_GPU_UTIL:
            return {"waited_s": round(time.time() - t0, 1), "busy_threads_before": cores,
                    "loadavg_before": load["loadavg_1_5_15"], "top_processes_before": load["top_processes"],
                    "gpu_util_before": round(gpu, 1)}
        if waited % 4 == 0:
            why = []
            if others:
                why.append(f"{len(others)} other render process(es), e.g. {others[0]}")
            if cores > QUIET_CORES:
                why.append(f"CPU busy {cores:.1f} threads")
            if gpu > QUIET_GPU_UTIL:
                why.append(f"GPU {gpu:.0f}% busy")
            log("  waiting for a quiet machine: " + "; ".join(why))
        waited += 1
        if time.time() - t0 > max_wait_s:
            raise SystemExit("machine never became quiet; giving up")
        time.sleep(15)


class ForeignWatcher:
    """Looks for other renderers (another benchmark, a game) that start, or do work,
    while a run is in progress: they would share the GPU or CPU with it."""

    def __init__(self):
        self.start = renderer_procs()
        self.seen = []
        self.stop_ev = threading.Event()
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def _loop(self):
        while not self.stop_ev.is_set():
            for d in active_renderers(self.start, renderer_procs(), min_ticks=20):
                if d not in self.seen:
                    self.seen.append(d)
            self.stop_ev.wait(0.5)

    def stop(self):
        self.stop_ev.set()
        self.th.join()


# ---------------------------------------------------------------------------
# GPU sampling
# ---------------------------------------------------------------------------
class GpuSampler:
    def __init__(self):
        self.samples = []
        self.proc = subprocess.Popen(
            ["nvidia-smi", "--query-gpu=utilization.gpu,utilization.encoder,utilization.decoder,memory.used",
             "--format=csv,noheader,nounits", "-lms", "100"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.th = threading.Thread(target=self._read, daemon=True)
        self.th.start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                g, e, d, m = [float(x) for x in line.split(",")]
            except ValueError:
                continue
            self.samples.append((time.time(), g, e, d, m))

    def stop(self):
        self.proc.terminate()
        self.proc.wait()
        self.th.join(timeout=2)

    def summary(self, start, end):
        before = [s for s in self.samples if s[0] < start]
        during = [s for s in self.samples if start <= s[0] <= end + 0.05]
        if not during:
            return None
        base_mem = before[-1][4] if before else during[0][4]
        return {
            "util_mean": round(statistics.mean(s[1] for s in during), 1),
            "util_max": max(s[1] for s in during),
            "encoder_util_mean": round(statistics.mean(s[2] for s in during), 1),
            "decoder_util_mean": round(statistics.mean(s[3] for s in during), 1),
            "mem_used_peak_delta_mib": max(s[4] for s in during) - base_mem,
            "samples": len(during),
        }


# ---------------------------------------------------------------------------
# output check
# ---------------------------------------------------------------------------
def probe(path, comp):
    if not os.path.exists(path):
        return {"ok": False, "error": "no output"}
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_read_frames,color_space,color_primaries,color_transfer",
                        "-show_entries", "format=duration,size,bit_rate", "-of", "json", path],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        s, f = j["streams"][0], j["format"]
    except (ValueError, KeyError, IndexError):
        return {"ok": False, "error": "ffprobe failed: " + r.stderr[-300:]}
    w, h = COMPS[comp]
    info = {
        "codec": s.get("codec_name"), "profile": s.get("profile"), "width": s.get("width"),
        "height": s.get("height"), "pix_fmt": s.get("pix_fmt"), "fps": s.get("r_frame_rate"),
        "frames": int(s.get("nb_read_frames", 0)), "duration_s": float(f.get("duration", 0)),
        "size_bytes": int(f.get("size", 0)), "bitrate": int(f.get("bit_rate", 0)),
        "color": [s.get("color_space"), s.get("color_primaries"), s.get("color_transfer")],
    }
    problems = []
    if info["codec"] != "h264":
        problems.append(f"codec {info['codec']}")
    if (info["width"], info["height"]) != (w, h):
        problems.append(f"size {info['width']}x{info['height']}")
    if info["frames"] != FRAMES:
        problems.append(f"{info['frames']} frames")
    if abs(info["duration_s"] - 10.0) > 0.05:
        problems.append(f"duration {info['duration_s']}")
    if info["fps"] != "30/1":
        problems.append(f"fps {info['fps']}")
    info["ok"] = not problems
    info["problems"] = problems
    return info


def tool_notes(tool, log_text):
    """What the tool reported about itself (worker count, capture path, encoder)."""
    notes = {}
    if tool == "hyperframes":
        m = re.findall(r'"workerCount":(\d+)', log_text)
        if m:
            notes["workers"] = int(m[-1])
        m = re.search(r'"captureMode":"(\w+)"', log_text)
        if m:
            notes["capture"] = m.group(1)
        m = re.search(r"rendered in ([\d.]+)s", log_text)
        if m:
            notes["self_reported_s"] = float(m.group(1))
        m = re.search(r"(beginframe|screenshot)[^\n]*capture · ([^·\n]+)·", log_text)
        if m:
            notes["browser_gpu"] = m.group(2).strip()
    if tool == "ultrafast":
        m = re.search(r"in ([\d.]+) s = ([\d.]+) fps", log_text)
        if m:
            notes["self_reported_s"] = float(m.group(1))
        m = re.search(r"pipelines: (\d+) from cache, (\d+) compiled", log_text)
        if m:
            notes["pipelines_cached"], notes["pipelines_compiled"] = int(m.group(1)), int(m.group(2))
    if tool == "remotion":
        m = re.search(r"concurrency[^\d]*(\d+)", log_text, re.I)
        if m:
            notes["concurrency_reported"] = int(m.group(1))
    if re.search(r"falling back|fallback", log_text, re.I):
        notes["fallback_warning"] = True
    return notes


# ---------------------------------------------------------------------------
# one run
# ---------------------------------------------------------------------------
def run_once(phase, tool, config, comp, kind, index, argv, cwd, out, check_video=True):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.isdir(out):
        shutil.rmtree(out)
    elif os.path.exists(out):
        os.remove(out)
    for attempt in range(1, 6):
        quiet = wait_quiet()
        rid = uuid.uuid4().hex[:10]
        res_path = os.path.join(LOGS, f"{rid}.result.json")
        log_path = os.path.join(LOGS, f"{comp}-{tool}-{config}-{kind}{index}-{rid}.log")
        sampler = GpuSampler()
        time.sleep(0.3)  # a GPU baseline before the run starts
        watcher = ForeignWatcher()
        others0 = user_proc_ticks()
        scope = ["systemd-run", "--user", "--scope", "-q", "--collect", f"--unit=ufbench-{rid}",
                 sys.executable, "-I", RUNNER, res_path, log_path, cwd, "--"] + argv
        subprocess.run(scope, env=tool_env(tool))
        others1 = user_proc_ticks()
        time.sleep(0.15)
        sampler.stop()
        watcher.stop()
        with open(res_path) as f:
            r = json.load(f)
        os.remove(res_path)
        with open(log_path, errors="replace") as f:
            log_text = f.read()
        # Other load during the run: CPU used by user-space processes that are not part of
        # the run (nor this harness). Kernel and driver threads are left out: much of their
        # work during a run is caused by the run itself (GPU interrupts, I/O), and it lies
        # outside the run's cgroup. The whole-machine figure is kept too, for reference.
        hz = os.sysconf("SC_CLK_TCK")
        me = os.getpid()
        deltas = []
        for pid, (name, t1) in others1.items():
            if pid in (me, sampler.proc.pid) or pid not in others0:
                continue  # new processes are the watcher's job; the run's own are gone by now
            d = t1 - others0[pid][1]
            if d > 0:
                deltas.append((d, name))
        deltas.sort(reverse=True)
        foreign = sum(d for d, _ in deltas) / hz / r["wall_s"]
        host_other = max(0.0, r["host_busy_s"] - r["cpu_s"]) / r["wall_s"]
        rec = {
            "phase": phase, "comp": comp, "tool": tool, "config": config, "kind": kind, "index": index,
            "attempt": attempt, "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "argv": public_argv(argv), "cwd": os.path.relpath(cwd, BENCH),
            "returncode": r["returncode"], "wall_s": round(r["wall_s"], 4), "cpu_s": round(r["cpu_s"], 3),
            "avg_cpu_threads": round(r["cpu_s"] / r["wall_s"], 2),
            "peak_ram_mib": round(r["peak_ram_bytes"] / 2**20, 1),
            "cgroup_memory_peak_mib": round(r["memory_peak_bytes"] / 2**20, 1),
            "gpu": sampler.summary(r["start_unix"], r["end_unix"]),
            "foreign_cpu_threads": round(foreign, 2),
            "foreign_top_processes": [{"name": n, "threads": round(d / hz / r["wall_s"], 2)} for d, n in deltas[:3]],
            "host_other_cpu_threads": round(host_other, 2), "quiet_before": quiet,
            "foreign_renderers_during": watcher.seen[:5],
            "leftover_processes": r["leftover_processes"],
            "log": os.path.relpath(log_path, BENCH), "notes": tool_notes(tool, log_text),
        }
        if check_video:
            rec["output"] = probe(out, comp)
            rec["ok"] = r["returncode"] == 0 and rec["output"]["ok"]
        else:
            rec["output"] = {"exists": os.path.exists(out)}
            rec["ok"] = r["returncode"] == 0 and os.path.exists(out)
        rec["contaminated"] = foreign > QUIET_CORES or bool(watcher.seen)
        append(rec)
        status = "ok" if rec["ok"] else "FAILED"
        log(f"  {phase:7s} {comp:8s} {tool:11s} {config:9s} {kind}{index}: {rec['wall_s']:.2f} s "
            f"({status}, cpu {rec['avg_cpu_threads']} thr, ram {rec['peak_ram_mib']:.0f} MiB, other load {foreign:.1f} thr)")
        if rec["contaminated"]:
            why = watcher.seen[0] if watcher.seen else f"{foreign:.1f} threads of other CPU load"
            log(f"  ^ other work on the machine during this run ({why[:120]}); discarding it and running again")
            continue
        return rec
    log("  gave up after 5 contaminated attempts")
    return rec


def public_argv(argv):
    """The command as recorded: the ultrafast binary by name, paths relative to this folder."""
    out = []
    for i, a in enumerate(argv):
        if i == 0 and os.path.isabs(a) and os.path.basename(a) in ("ultrafast", "uf"):
            out.append(os.path.basename(a))
        elif os.path.isabs(a) and a.startswith(BENCH + os.sep):
            out.append(os.path.relpath(a, BENCH))
        else:
            out.append(a)
    return out


def append(rec):
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "runs.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def load_runs():
    path = os.path.join(RESULTS, "runs.jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def out_path(comp, tool, config):
    return os.path.join(OUT, comp, f"{tool}-{config}.mp4")


# ---------------------------------------------------------------------------
# phases
# ---------------------------------------------------------------------------
REMOTION_SWEEP = [2, 4, 8, 12, 16, 24, 32]   # 32 = every CPU thread, Remotion's maximum here
HYPERFRAMES_SWEEP = [2, 4, 8, 12, 16, 24]    # 24 = HyperFrames' maximum
SWEEP_RUNS = 2


def phase_sweep(comps):
    for comp in comps:
        for tool, values, prefix in (("remotion", REMOTION_SWEEP, "c"), ("hyperframes", HYPERFRAMES_SWEEP, "w")):
            log(f"sweep {comp} {tool}")
            first = f"{prefix}{values[0]}"
            argv, cwd = command(tool, first, comp, out_path(comp, tool, first))
            run_once("sweep", tool, first, comp, "warmup", 0, argv, cwd, out_path(comp, tool, first))
            for v in values:
                cfg = f"{prefix}{v}"
                for i in range(SWEEP_RUNS):
                    argv, cwd = command(tool, cfg, comp, out_path(comp, tool, cfg))
                    run_once("sweep", tool, cfg, comp, "warm", i + 1, argv, cwd, out_path(comp, tool, cfg))


def best_sweep(comp, tool, pattern=None):
    """The fastest configuration the sweep found, among configs matching `pattern`
    (default: plain concurrency, cN for Remotion and wN for HyperFrames)."""
    pattern = pattern or (r"^c\d+$" if tool == "remotion" else r"^w\d+$")
    runs = [r for r in load_runs() if r["phase"] == "sweep" and r["comp"] == comp and r["tool"] == tool
            and r["kind"] == "warm" and r["ok"] and not r["contaminated"] and re.match(pattern, r["config"])]
    by = {}
    for r in runs:
        by.setdefault(r["config"], []).append(r["wall_s"])
    if not by:
        return None
    return min(by, key=lambda c: statistics.median(by[c]))


def configs_for(comp):
    """The configurations measured in full for one composition: each tool's default,
    its maximum concurrency, the fastest concurrency the sweep found, and the best
    case each browser tool offers (Remotion from a prebuilt bundle; HyperFrames with
    NVENC encoding)."""
    rm_best = best_sweep(comp, "remotion") or "c8"
    hf_best = best_sweep(comp, "hyperframes") or "w4"
    cfgs = [("ultrafast", "default"),
            ("remotion", "default"), ("remotion", rm_best), ("remotion", "c32"),
            ("remotion", f"bundled-{rm_best}"),
            ("hyperframes", "default"), ("hyperframes", hf_best), ("hyperframes", "w24"),
            ("hyperframes", "gpu"), ("hyperframes", f"gpu-{hf_best}")]
    # Remotion's documented way to give Chrome the GPU on Linux (its docs recommend it
    # for WebGL and GPU-heavy CSS; for other content they say the default is best)
    cfgs.append(("remotion", f"angle-egl-{rm_best}"))
    cfgs.append(("remotion", f"bundled-angle-egl-{rm_best}"))  # both of Remotion's speed-ups at once
    # --gl=vulkan: on this machine (an NVIDIA card plus an AMD iGPU) angle-egl does not
    # reach the NVIDIA GPU while vulkan does, so Remotion also gets its fastest Vulkan setting
    vk = best_sweep(comp, "remotion", r"^bundled-vulkan-c\d+$")
    if vk:
        cfgs.append(("remotion", vk))
        cfgs.append(("remotion", vk.replace("bundled-vulkan-", "bundled-vulkan-nvenc-")))
    seen, out = set(), []
    for c in cfgs:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def measured_counts():
    n = {}
    for r in load_runs():
        if r["phase"] == "measure" and r["kind"] in ("warm", "cold") and r["ok"] and not r["contaminated"]:
            key = (r["comp"], r["tool"], r["config"], r["kind"])
            n[key] = n.get(key, 0) + 1
    return n


VULKAN_SWEEP = [8, 12, 16, 24, 32]


def phase_sweep_vulkan(comps):
    """Remotion with --gl=vulkan from a prebuilt bundle, at several concurrencies."""
    bundle_argv = ["npx", "remotion", "bundle", "src/index.ts", "--out-dir", "build"]
    for comp in comps:
        log(f"sweep {comp} remotion --gl=vulkan")
        run_once("sweep", "remotion", "bundle", comp, "bundle", 1, bundle_argv,
                 os.path.join(BENCH, "remotion"), os.path.join(BENCH, "remotion", "build"), check_video=False)
        first = f"bundled-vulkan-c{VULKAN_SWEEP[0]}"
        argv, cwd = command("remotion", first, comp, out_path(comp, "remotion", first))
        run_once("sweep", "remotion", first, comp, "warmup", 0, argv, cwd, out_path(comp, "remotion", first))
        for v in VULKAN_SWEEP:
            cfg = f"bundled-vulkan-c{v}"
            for i in range(SWEEP_RUNS):
                argv, cwd = command("remotion", cfg, comp, out_path(comp, "remotion", cfg))
                run_once("sweep", "remotion", cfg, comp, "warm", i + 1, argv, cwd, out_path(comp, "remotion", cfg))


def phase_measure(comps, warm_runs):
    """Resumable: configurations that already have their warm runs are skipped."""
    for comp in comps:
        done = measured_counts()
        cfgs = [(t, c) for t, c in configs_for(comp) if done.get((comp, t, c, "warm"), 0) < warm_runs]
        if not cfgs:
            continue
        log(f"measure {comp}: " + ", ".join(f"{t}/{c}" for t, c in cfgs))
        cold_done = {t for t in ("ultrafast", "remotion", "hyperframes") if done.get((comp, t, "default", "cold"))}
        # the bundle the "bundled" configurations render from (made once per source change)
        bundle_argv = ["npx", "remotion", "bundle", "src/index.ts", "--out-dir", "build"]
        run_once("measure", "remotion", "bundle", comp, "bundle", 1, bundle_argv,
                 os.path.join(BENCH, "remotion"), os.path.join(BENCH, "remotion", "build"), check_video=False)
        for tool, cfg in cfgs:
            out = out_path(comp, tool, cfg)
            argv, cwd = command(tool, cfg, comp, out)
            if tool not in cold_done and cfg == "default":
                reset_caches(tool)
                run_once("measure", tool, cfg, comp, "cold", 1, argv, cwd, out)
                cold_done.add(tool)
            else:  # one unrecorded-in-the-median warm-up so every config starts warm
                run_once("measure", tool, cfg, comp, "warmup", 0, argv, cwd, out)
            for i in range(warm_runs):
                run_once("measure", tool, cfg, comp, "warm", i + 1, argv, cwd, out)


def phase_preview(comps, runs):
    for comp in comps:
        for tool in ("ultrafast", "remotion", "hyperframes"):
            ext = "" if tool == "hyperframes" else ".png"  # hyperframes snapshot writes a folder
            out = os.path.join(OUT, comp, f"{tool}-preview{ext}")
            argv, cwd = preview_command(tool, comp, out)
            run_once("preview", tool, "default", comp, "warmup", 0, argv, cwd, out, check_video=False)
            for i in range(runs):
                run_once("preview", tool, "default", comp, "warm", i + 1, argv, cwd, out, check_video=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["sweep", "sweep-vulkan", "measure", "preview", "all", "quiet"])
    ap.add_argument("--comps", default="title,chart,footage,effects")
    ap.add_argument("--warm", type=int, default=5)
    ap.add_argument("--preview-runs", type=int, default=3)
    a = ap.parse_args()
    comps = [c for c in a.comps.split(",") if c]
    os.makedirs(LOGS, exist_ok=True)
    if a.phase == "quiet":
        print(json.dumps(wait_quiet()))
        return
    if a.phase in ("sweep", "all"):
        phase_sweep(comps)
    if a.phase in ("sweep-vulkan", "all"):
        phase_sweep_vulkan(comps)
    if a.phase in ("measure", "all"):
        phase_measure(comps, a.warm)
    if a.phase in ("preview", "all"):
        phase_preview(comps, a.preview_runs)


if __name__ == "__main__":
    main()
