#!/usr/bin/env python3
"""Checks that the three tools rendered the same thing, and saves the evidence:

  frames/<comp>.jpg     one row per tool, the same six moments side by side
  frames/<comp>-<tool>-sheet.jpg   a 5x2 contact sheet of each tool's full output
  results/similarity.json   SSIM and PSNR of each browser tool's video against
                            ultrafast's, over all 300 frames

Usage: verify.py [--config-map tool=config,...] [--comps ...]
Uses ffmpeg/ffprobe from PATH (decode, scale, tile, ssim, psnr: any build).
"""
import argparse
import json
import os
import re
import subprocess

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BENCH, "out")
FRAMES_DIR = os.path.join(BENCH, "frames")
FONT = os.path.join(BENCH, "assets", "fonts", "GeistMono-VF.ttf")
TOOLS = ["ultrafast", "remotion", "hyperframes"]
MOMENTS = [0.5, 1.5, 3.0, 5.0, 7.0, 9.5]  # seconds
COMPS = {"title": (1080, 1920), "chart": (1920, 1080), "footage": (1080, 1920), "effects": (1920, 1080)}
# The YUV matrix each tool encodes with. HyperFrames tags its files (BT.709);
# ultrafast 0.1.1 (BT.709) and Remotion 4.0.545 (BT.601, from Chrome's sRGB frames
# through libx264) write no colour tags, and FFmpeg assumes BT.601 for untagged
# video, so the frames are decoded with the matrix each tool actually used
# (checked on a flat #fbbf24 area: see README, "Colour tags").
MATRIX = {"ultrafast": "bt709", "remotion": "bt601", "hyperframes": "bt709"}


def to_rgb(tool):
    # setparams: drop the source's colour tags so every row of a grid is encoded alike
    return (f"scale=in_color_matrix={MATRIX[tool]}:in_range=tv,format=rgb24,"
            "setparams=colorspace=unknown:color_primaries=unknown:color_trc=unknown:range=unknown")


def ff(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])
    return r


def row(video, tool, comp, path):
    w, h = COMPS[comp]
    th = 400 if h > w else 220  # tile height
    tw = round(w * th / h)
    sel = "+".join(f"eq(n\\,{int(round(t * 30))})" for t in MOMENTS)
    label_w = 230
    vf = (f"select='{sel}',{to_rgb(tool)},scale={tw}:{th}:flags=lanczos,tile={len(MOMENTS)}x1:padding=6:color=0x1a1a1a,"
          f"pad=iw+{label_w}:ih+12:{label_w}:6:color=0x1a1a1a,"
          f"drawtext=fontfile='{FONT}':text='{tool}':fontcolor=white:fontsize=30:x=20:y=(h-text_h)/2")
    ff(["-i", video, "-vf", vf, "-frames:v", "1", "-fps_mode", "passthrough", "-q:v", "3", path])


def header(comp, width, path):
    w, h = COMPS[comp]
    th = 400 if h > w else 220
    tw = round(w * th / h)
    text = "".join(f"drawtext=fontfile='{FONT}':text='{t:.1f} s':fontcolor=0xbbbbbb:fontsize=24:"
                   f"x={230 + 6 + i * (tw + 6) + tw // 2}-text_w/2:y=10," for i, t in enumerate(MOMENTS))
    ff(["-f", "lavfi", "-i", f"color=c=0x1a1a1a:s={width}x44:d=1", "-vf", text.rstrip(","),
        "-frames:v", "1", "-q:v", "3", path])


def image_width(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return int(r.stdout.strip())


def grid(comp, videos):
    os.makedirs(FRAMES_DIR, exist_ok=True)
    parts = []
    for tool, video in videos:
        p = os.path.join(FRAMES_DIR, f".{comp}-{tool}-row.jpg")
        row(video, tool, comp, p)
        parts.append(p)
    head = os.path.join(FRAMES_DIR, f".{comp}-head.jpg")
    header(comp, image_width(parts[0]), head)
    parts.insert(0, head)
    dest = os.path.join(FRAMES_DIR, f"{comp}.jpg")
    inputs = sum((["-i", p] for p in parts), [])
    ff(inputs + ["-filter_complex", f"vstack=inputs={len(parts)}", "-q:v", "3", dest])
    for p in parts:
        os.remove(p)
    return dest


def sheet(comp, tool, video):
    w, h = COMPS[comp]
    tw, th = (216, 384) if h > w else (384, 216)
    dest = os.path.join(FRAMES_DIR, f"{comp}-{tool}-sheet.jpg")
    ff(["-i", video, "-vf", f"select='not(mod(n\\,30))',{to_rgb(tool)},scale={tw}:{th},tile=5x2:padding=4", "-frames:v", "1",
        "-fps_mode", "passthrough", "-q:v", "4", dest])
    return dest


def similarity(ref, other, tool):
    """Luma SSIM and PSNR over all 300 frames: each file is decoded to RGB with its
    own matrix, then both are reduced to grey the same way."""
    a = f"{to_rgb(tool)},format=gray"
    b = f"{to_rgb('ultrafast')},format=gray"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", other, "-i", ref, "-lavfi",
                        f"[0:v]{a},split[a1][a2];[1:v]{b},split[b1][b2];[a1][b1]ssim;[a2][b2]psnr",
                        "-f", "null", "-"], capture_output=True, text=True)
    ssim = re.search(r"SSIM .*All:([\d.]+)", r.stderr)
    psnr = re.search(r"PSNR .*average:([\d.inf]+)", r.stderr)
    return {"ssim_all": float(ssim.group(1)) if ssim else None,
            "psnr_avg_db": float(psnr.group(1)) if psnr and psnr.group(1) != "inf" else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comps", default="title,chart,footage,effects")
    ap.add_argument("--config", default="ultrafast=default,remotion=default,hyperframes=default")
    a = ap.parse_args()
    cfg = dict(kv.split("=") for kv in a.config.split(","))
    sim = {}
    for comp in a.comps.split(","):
        videos = [(t, os.path.join(OUT, comp, f"{t}-{cfg[t]}.mp4")) for t in TOOLS]
        videos = [(t, v) for t, v in videos if os.path.exists(v)]
        if not videos:
            continue
        print("grid", grid(comp, videos))
        for t, v in videos:
            sheet(comp, t, v)
        ref = dict(videos).get("ultrafast")
        if ref:
            sim[comp] = {t: similarity(ref, v, t) for t, v in videos if t != "ultrafast"}
            print(comp, json.dumps(sim[comp]))
    # the fastest configuration of each browser tool (from results.json) is checked too:
    # GPU rendering or another encoder must not have changed the picture
    rj = os.path.join(BENCH, "results.json")
    if os.path.exists(rj):
        with open(rj) as f:
            headline = json.load(f).get("headline", {})
        for comp in a.comps.split(","):
            ref = os.path.join(OUT, comp, "ultrafast-default.mp4")
            for t in ("remotion", "hyperframes"):
                best = headline.get(comp, {}).get(t, {}).get("best_config")
                v = os.path.join(OUT, comp, f"{t}-{best}.mp4")
                if best and os.path.exists(ref) and os.path.exists(v):
                    sim.setdefault(comp, {})[f"{t} fastest ({best})"] = similarity(ref, v, t)
                    print(comp, t, best, json.dumps(sim[comp][f"{t} fastest ({best})"]))
    os.makedirs(os.path.join(BENCH, "results"), exist_ok=True)
    path = os.path.join(BENCH, "results", "similarity.json")
    old = {}
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)
    old.update(sim)
    with open(path, "w") as f:
        json.dump(old, f, indent=1)


if __name__ == "__main__":
    main()
