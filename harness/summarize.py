#!/usr/bin/env python3
"""Turns results/runs.jsonl into results.json (every run, plus medians and ratios)
and results/tables.md (the tables in README.md)."""
import json
import os
import re
import statistics

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPS = ["title", "chart", "footage", "effects"]
TOOLS = ["ultrafast", "remotion", "hyperframes"]
LABEL = {
    "default": "default command",
    "c32": "--concurrency 32 (max)",
    "w24": "--workers 24 (max)",
    "gpu": "--gpu (NVENC encode)",
}


def label(tool, cfg):
    if cfg in LABEL:
        return LABEL[cfg]
    if cfg.startswith("bundled-vulkan-nvenc-c"):
        return f"prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency {cfg[22:]}"
    if cfg.startswith("bundled-vulkan-c"):
        return f"prebuilt bundle, --gl=vulkan, --concurrency {cfg[16:]}"
    if cfg.startswith("bundled-angle-egl-c"):
        return f"prebuilt bundle, --gl=angle-egl, --concurrency {cfg[19:]}"
    if cfg.startswith("bundled-c"):
        return f"prebuilt bundle, --concurrency {cfg[9:]}"
    if cfg.startswith("angle-egl-c"):
        return f"--gl=angle-egl --concurrency {cfg[11:]}"
    if cfg.startswith("gpu-w"):
        return f"--gpu --workers {cfg[5:]}"
    if cfg.startswith("c"):
        return f"--concurrency {cfg[1:]}"
    if cfg.startswith("w"):
        return f"--workers {cfg[1:]}"
    return cfg


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def good(r):
    # "invalid": a run set aside after the fact, with the reason (see README, "A quiet machine")
    return r.get("ok") and not r.get("contaminated") and not r.get("invalid")


def stats(vals):
    vals = sorted(vals)
    return {"n": len(vals), "median": round(statistics.median(vals), 3), "min": round(vals[0], 3),
            "max": round(vals[-1], 3),
            "stdev": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0}


def summarize_config(runs):
    warm = [r for r in runs if r["kind"] == "warm" and good(r)]
    cold = [r for r in runs if r["kind"] == "cold" and good(r)]
    if not warm:
        return None
    out = {
        "warm_s": stats([r["wall_s"] for r in warm]),
        "warm_runs_s": [r["wall_s"] for r in warm],
        "cold_s": cold[-1]["wall_s"] if cold else None,
        "cpu_threads_avg": round(statistics.median(r["avg_cpu_threads"] for r in warm), 2),
        "cpu_s": round(statistics.median(r["cpu_s"] for r in warm), 2),
        "peak_ram_mib": round(statistics.median(r["peak_ram_mib"] for r in warm)),
        "peak_ram_mib_max": round(max(r["peak_ram_mib"] for r in warm)),
        "gpu_util_mean": round(statistics.median((r["gpu"] or {}).get("util_mean", 0) for r in warm), 1),
        "gpu_encoder_util_mean": round(statistics.median((r["gpu"] or {}).get("encoder_util_mean", 0) for r in warm), 1),
        "gpu_mem_delta_mib": round(statistics.median((r["gpu"] or {}).get("mem_used_peak_delta_mib", 0) for r in warm)),
        "other_load_threads_avg": round(statistics.mean(r["foreign_cpu_threads"] for r in warm), 2),
        "output": {k: warm[-1]["output"].get(k) for k in ("frames", "duration_s", "width", "height", "codec",
                                                          "profile", "pix_fmt", "size_bytes", "bitrate", "color")},
        "all_outputs_ok": all(r["output"].get("ok") for r in warm),
        "notes": warm[-1].get("notes", {}),
        "command": " ".join(warm[-1]["argv"]),
    }
    return out


def main():
    runs = load(os.path.join(BENCH, "results", "runs.jsonl"))
    env = {}
    p = os.path.join(BENCH, "results", "environment.json")
    if os.path.exists(p):
        with open(p) as f:
            env = json.load(f)
    sim = {}
    p = os.path.join(BENCH, "results", "similarity.json")
    if os.path.exists(p):
        with open(p) as f:
            sim = json.load(f)

    measured, sweep, preview, bundle = {}, {}, {}, {}
    for comp in COMPS:
        measured[comp] = {}
        for tool in TOOLS:
            cfgs = sorted({r["config"] for r in runs if r["phase"] == "measure" and r["comp"] == comp
                           and r["tool"] == tool})
            for cfg in cfgs:
                s = summarize_config([r for r in runs if r["phase"] == "measure" and r["comp"] == comp
                                      and r["tool"] == tool and r["config"] == cfg])
                if s:
                    s["label"] = label(tool, cfg)
                    measured[comp].setdefault(tool, {})[cfg] = s
        sweep[comp] = {}
        for tool in ("remotion", "hyperframes"):
            by = {}
            for r in runs:
                if r["phase"] == "sweep" and r["comp"] == comp and r["tool"] == tool and r["kind"] == "warm" and good(r):
                    by.setdefault(r["config"], []).append(r["wall_s"])
            sweep[comp][tool] = {c: round(statistics.median(v), 3) for c, v in
                                 sorted(by.items(), key=lambda kv: (len(kv[0].split("-")), int(re.sub(r"\D", "", kv[0]))))}
        preview[comp] = {}
        for tool in TOOLS:
            v = [r["wall_s"] for r in runs if r["phase"] == "preview" and r["comp"] == comp and r["tool"] == tool
                 and r["kind"] == "warm" and good(r)]
            if v:
                preview[comp][tool] = stats(v)
        b = [r["wall_s"] for r in runs if r["kind"] == "bundle" and r["comp"] == comp and good(r)]
        if b:
            bundle[comp] = round(statistics.median(b), 3)

    headline = {}
    for comp in COMPS:
        m = measured[comp]
        if "ultrafast" not in m or "default" not in m["ultrafast"]:
            continue
        uf = m["ultrafast"]["default"]["warm_s"]["median"]
        row = {"ultrafast_s": uf, "ultrafast_cold_s": m["ultrafast"]["default"]["cold_s"]}
        for tool in ("remotion", "hyperframes"):
            if tool not in m:
                continue
            d = m[tool].get("default")
            best_cfg = min(m[tool], key=lambda c: m[tool][c]["warm_s"]["median"])
            best = m[tool][best_cfg]
            row[tool] = {
                "default_s": d["warm_s"]["median"] if d else None,
                "default_cold_s": d["cold_s"] if d else None,
                "best_s": best["warm_s"]["median"], "best_config": best_cfg,
                "best_label": label(tool, best_cfg),
                "speedup_vs_default": round(d["warm_s"]["median"] / uf, 1) if d else None,
                "speedup_vs_best": round(best["warm_s"]["median"] / uf, 1),
            }
        headline[comp] = row

    counted = [r for r in runs if good(r)]
    def pct(vals, q):
        vals = sorted(vals)
        return round(vals[min(len(vals) - 1, int(q * len(vals)))], 2) if vals else None
    before = [r["quiet_before"].get("busy_threads_before") for r in counted if r.get("quiet_before")]
    before = [b for b in before if b is not None]
    la = [r["quiet_before"]["loadavg_before"][0] for r in counted
          if r.get("quiet_before") and r["quiet_before"].get("loadavg_before")]
    during = [r["foreign_cpu_threads"] for r in counted]
    quiet = {
        "runs_counted": len(counted),
        "runs_discarded_for_other_load": sum(1 for r in runs if r.get("contaminated")),
        "runs_set_aside_invalid": sum(1 for r in runs if r.get("invalid") and not r.get("contaminated")),
        "runs_failed": sum(1 for r in runs if not r.get("ok")),
        "busy_threads_before_median": pct(before, 0.5), "busy_threads_before_max": pct(before, 1.0),
        "loadavg1_before_median": pct(la, 0.5), "loadavg1_before_max": pct(la, 1.0),
        "other_cpu_threads_during_median": pct(during, 0.5), "other_cpu_threads_during_max": pct(during, 1.0),
        "note": "busy threads: CPU use of the whole machine over 3 s just before a run (nothing of the "
                "benchmark's running); load average also counts the benchmark's own previous run, so it "
                "is recorded but not used to gate runs; other CPU during a run: machine CPU minus the "
                "run's own cgroup. Runs with more than 1.5 threads of other load, or with another "
                "renderer working, were discarded and repeated.",
    }

    result = {
        "about": f"Render-speed benchmark: {(env.get('ultrafast') or {}).get('version') or 'ultrafast'} vs Remotion vs "
                 "HyperFrames on one machine. "
                 "Times are wall-clock seconds for the whole CLI command (start to finished MP4); "
                 "see README.md for the method.",
        "environment": env,
        "frames_per_video": 300,
        "crf": 18,
        "headline": headline,
        "machine_quiet": quiet,
        "measured": measured,
        "concurrency_sweep_s": sweep,
        "remotion_bundle_s": bundle,
        "still_frame_s": preview,
        "similarity_to_ultrafast": sim,
        "runs": runs,
    }
    with open(os.path.join(BENCH, "results.json"), "w") as f:
        json.dump(result, f, indent=1)
    write_tables(result)


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def write_tables(res):
    L = []
    L.append("### Headline: warm median seconds (300 frames, 10 s video, H.264 CRF 18)\n")
    L.append("| Composition | ultrafast | Remotion default | Remotion fastest | HyperFrames default | HyperFrames fastest |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for comp, h in res["headline"].items():
        rm, hf = h.get("remotion", {}), h.get("hyperframes", {})
        L.append(f"| {comp} | **{fmt(h['ultrafast_s'])}** | {fmt(rm.get('default_s'))} ({rm.get('speedup_vs_default')}×) | "
                 f"{fmt(rm.get('best_s'))} ({rm.get('speedup_vs_best')}×) | {fmt(hf.get('default_s'))} "
                 f"({hf.get('speedup_vs_default')}×) | {fmt(hf.get('best_s'))} ({hf.get('speedup_vs_best')}×) |")
    L.append("\n(×) = that time divided by ultrafast's: how many times longer the tool took.\n")
    L.append("Fastest configuration found for each browser tool:\n")
    for comp, h in res["headline"].items():
        L.append(f"- {comp}: Remotion `{h['remotion']['best_label']}`, HyperFrames `{h['hyperframes']['best_label']}`")
    L.append("\n### Cold first run (tool caches cleared), seconds\n")
    L.append("| Composition | ultrafast | Remotion | HyperFrames |")
    L.append("|---|---:|---:|---:|")
    for comp, h in res["headline"].items():
        L.append(f"| {comp} | {fmt(h['ultrafast_cold_s'])} | {fmt(h['remotion']['default_cold_s'])} | "
                 f"{fmt(h['hyperframes']['default_cold_s'])} |")
    q = res.get("machine_quiet", {})
    if q:
        L.append("\n### Was the machine quiet?\n")
        aside = q.get("runs_set_aside_invalid")
        L.append(f"- runs counted: {q['runs_counted']}; discarded because other work overlapped them: "
                 f"{q['runs_discarded_for_other_load']}; "
                 + (f"set aside as invalid (`invalid` in runs.jsonl gives why): {aside}; " if aside else "")
                 + f"failed: {q['runs_failed']}")
        L.append(f"- CPU busy just before a run (whole machine, threads of 32): median "
                 f"{q['busy_threads_before_median']}, max {q['busy_threads_before_max']}")
        L.append(f"- 1-minute load average at the start of a run: median {q['loadavg1_before_median']}, "
                 f"max {q['loadavg1_before_max']} (includes the benchmark's own previous run)")
        L.append(f"- other processes' CPU during a run: median {q['other_cpu_threads_during_median']} "
                 f"threads, max {q['other_cpu_threads_during_max']}")
    L.append("\n### Every measured configuration\n")
    L.append("| Composition | Tool | Configuration | Warm median s (min–max, n) | Cold s | CPU threads avg | Peak RAM MiB | GPU util % (mean) | GPU mem MiB | Output MB |")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for comp, tools in res["measured"].items():
        for tool, cfgs in tools.items():
            for cfg, s in sorted(cfgs.items(), key=lambda kv: kv[1]["warm_s"]["median"]):
                w = s["warm_s"]
                L.append(f"| {comp} | {tool} | {s['label']} | {fmt(w['median'])} ({fmt(w['min'])}–{fmt(w['max'])}, {w['n']}) | "
                         f"{fmt(s['cold_s'])} | {fmt(s['cpu_threads_avg'], 1)} | {s['peak_ram_mib']} | "
                         f"{fmt(s['gpu_util_mean'], 0)} | {s['gpu_mem_delta_mib']} | {fmt(s['output']['size_bytes'] / 1e6, 1)} |")
    L.append("\n### Concurrency sweep (median of 2 warm runs, seconds)\n")
    for comp, tools in res["concurrency_sweep_s"].items():
        for tool, vals in tools.items():
            if vals:
                plain = {k: v for k, v in vals.items() if re.match(r"^[cw]\d+$", k)}
                vk = {k: v for k, v in vals.items() if k.startswith("bundled-vulkan-c")}
                L.append(f"- {comp}, {tool}: " + ", ".join(f"{k[1:]} → {v:.2f}" for k, v in plain.items()))
                if vk:
                    L.append(f"- {comp}, remotion, prebuilt bundle + `--gl=vulkan`: "
                             + ", ".join(f"{k[16:]} → {v:.2f}" for k, v in vk.items()))
    L.append("\n### One still frame (t = 5 s) from the CLI, warm median seconds\n")
    L.append("| Composition | ultrafast `render --at 5` | Remotion `still --frame=150` | HyperFrames `snapshot --at 5` |")
    L.append("|---|---:|---:|---:|")
    for comp, p in res["still_frame_s"].items():
        L.append(f"| {comp} | {fmt(p.get('ultrafast', {}).get('median'))} | {fmt(p.get('remotion', {}).get('median'))} | "
                 f"{fmt(p.get('hyperframes', {}).get('median'))} |")
    if res["similarity_to_ultrafast"]:
        L.append("\n### Same picture? Luma SSIM / PSNR against ultrafast's video, all 300 frames\n")
        L.append("| Composition | Output compared with ultrafast's | SSIM | PSNR dB |")
        L.append("|---|---|---:|---:|")
        for comp, s in res["similarity_to_ultrafast"].items():
            for name, v in s.items():
                shown = name if " " in name else f"{name} default"
                L.append(f"| {comp} | {shown} | {fmt(v.get('ssim_all'), 3)} | {fmt(v.get('psnr_avg_db'), 1)} |")
    with open(os.path.join(BENCH, "results", "tables.md"), "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
