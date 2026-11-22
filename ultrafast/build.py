#!/usr/bin/env python3
"""Writes the benchmark compositions as ultrafast documents (title.json, chart.json,
footage.json, effects.json). The same scenes are written by hand for Remotion
(../remotion/src) and HyperFrames (../hyperframes/*/index.html); SPEC.md is the
shared description all three follow.

Run: python3 build.py   (stdlib only; output is deterministic)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "../assets/fonts/Geist-VF.ttf"
MONO = "../assets/fonts/GeistMono-VF.ttf"
CLIP = "../assets/footage/orion_moon_fd20.mp4"


def keys(*ks):
    """keys((t, v, ease), ...): ease is the ease into the next key."""
    out = []
    for k in ks:
        d = {"t": k[0], "v": k[1]}
        if len(k) > 2 and k[2]:
            d["ease"] = k[2]
        out.append(d)
    return {"keys": out}


class Doc:
    def __init__(self, w, h, fps=30, duration=10.0, motion_blur=None):
        self.format = {"width": w, "height": h, "fps": fps, "duration": duration}
        if motion_blur:
            self.format["motion_blur"] = motion_blur
        self.nodes = {}
        self.n = 0

    def add(self, nid, op, params=None, inputs=None, timing=None):
        node = {"op": op}
        if params:
            node["params"] = params
        if inputs:
            node["inputs"] = inputs
        if timing:
            node["timing"] = timing
        self.nodes[nid] = node
        return nid

    def over(self, layers, prefix):
        """Composite layers bottom to top with `over`; returns the top node id."""
        acc = layers[0]
        for i, fg in enumerate(layers[1:]):
            acc = self.add(f"{prefix}_{i}", "over", inputs={"fg": fg, "bg": acc})
        return acc

    def write(self, name, output):
        doc = {"version": 1, "format": self.format, "output": output, "nodes": self.nodes}
        with open(os.path.join(HERE, name), "w") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")


# ---------------------------------------------------------------------------
# (a) title: 1080x1920 social title card
# ---------------------------------------------------------------------------
def title():
    d = Doc(1080, 1920)
    E = "out_cubic"
    bg = d.add("bg", "gradient", {"kind": "linear", "a": "#1e1b4b", "b": "#be185d",
                                  "start": [0, 0], "end": [0, 1920], "space": "srgb"})
    sun = d.add("sun", "shape", {
        "kind": "circle", "color": "#fbbf24", "size": [640, 640],
        "center": keys((0, [760, 560]), (10, [700, 640])),
        "scale": keys((0, 0, E), (0.9, 1))})
    tile = d.add("tile", "shape", {
        "kind": "rect", "color": "#22d3ee", "size": [520, 520], "radius": 72,
        "center": keys((0, [-360, 1700]), (0.3, [-360, 1700], E), (1.2, [250, 1700])),
        "rotation": keys((0, 8), (10, 20))})
    ring = d.add("ring", "shape", {
        "kind": "circle", "color": "#ffffff", "size": [220, 220], "stroke": 10,
        "center": [250, 560],
        "opacity": keys((0, 0), (1.4, 0, E), (2.0, 0.9)),
        "scale": keys((0, 0.6), (1.4, 0.6, E), (2.0, 1))})

    # Copy block: enters element by element, leaves together (8.8 s to 9.6 s).
    def enter(t0, t1, dy):
        return keys((0, 0), (t0, 0, E), (t1, 1)), (t0, t1, dy)

    def pos(x, y, t0, t1, dy):
        return keys((0, [x, y + dy]), (t0, [x, y + dy], E), (t1, [x, y]))

    bar = d.add("bar", "shape", {
        "kind": "rect", "color": "#ffffff", "radius": 7,
        "size": keys((0, [0, 14]), (1.0, [0, 14], E), (1.5, [160, 14])),
        "center": keys((0, [120, 1000]), (1.0, [120, 1000], E), (1.5, [200, 1000]))})
    kicker = d.add("kicker", "text", {
        "text": "NEW DROP · 2026", "font": MONO, "weight": 500, "size": 40,
        "tracking": 6, "color": "#ffffffcc",
        "opacity": keys((0, 0), (0.8, 0, E), (1.3, 1)),
        "position": pos(120, 1030, 0.8, 1.3, 30)})
    line1 = d.add("line1", "text", {
        "text": "Make it", "font": FONT, "weight": 800, "size": 190, "color": "#ffffff",
        "opacity": keys((0, 0), (1.0, 0, E), (1.7, 1)),
        "position": pos(120, 1090, 1.0, 1.7, 80)})
    line2 = d.add("line2", "text", {
        "text": "move.", "font": FONT, "weight": 800, "size": 190, "color": "#fbbf24",
        "opacity": keys((0, 0), (1.15, 0, E), (1.85, 1)),
        "position": pos(120, 1280, 1.15, 1.85, 80)})
    sub = d.add("sub", "text", {
        "text": "Ten seconds. One render.", "font": FONT, "weight": 500, "size": 52,
        "color": "#ffffffd9",
        "opacity": keys((0, 0), (2.0, 0, E), (2.6, 1)),
        "position": pos(120, 1500, 2.0, 2.6, 20)})
    copy = d.over([bar, kicker, line1, line2, sub], "copy")
    copy_fade = d.add("copy_fade", "opacity", {
        "opacity": keys((0, 1), (8.8, 1, "in_cubic"), (9.6, 0))}, {"source": copy})
    copy_move = d.add("copy_move", "transform", {
        "anchor": [540, 960],
        "position": keys((0, [540, 960]), (8.8, [540, 960], "in_cubic"), (9.6, [540, 900]))},
        {"source": copy_fade})
    out = d.over([bg, sun, tile, ring, copy_move], "frame")
    d.write("title.json", out)


# ---------------------------------------------------------------------------
# (b) chart: 1920x1080 animated bar + line chart with labels
# ---------------------------------------------------------------------------
VALUES = [12, 18, 23, 31, 36, 44, 52, 57, 63, 71, 80, 92]
TARGETS = [15, 20, 26, 30, 38, 42, 50, 58, 66, 72, 78, 88]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
X0, X1, BASE, PXU = 160, 1800, 900, 6.0  # plot left/right, baseline y, px per unit


def chart():
    d = Doc(1920, 1080)
    E = "out_cubic"
    layers = [d.add("bg", "solid", {"color": "#0b1020"})]
    layers.append(d.add("title", "text", {
        "text": "Monthly active users, 2026", "font": FONT, "weight": 700, "size": 60,
        "color": "#ffffff",
        "opacity": keys((0, 0, E), (0.6, 1)),
        "position": keys((0, [120, 100], E), (0.6, [120, 80]))}))
    layers.append(d.add("subtitle", "text", {
        "text": "Millions, January to December", "font": FONT, "weight": 400, "size": 30,
        "color": "#94a3b8",
        "opacity": keys((0, 0), (0.15, 0, E), (0.75, 1)),
        "position": keys((0, [120, 178]), (0.15, [120, 178], E), (0.75, [120, 158]))}))
    # gridlines (25, 50, 75, 100) and their labels; they draw on from the left
    for v in (25, 50, 75, 100):
        y = BASE - v * PXU
        w = X1 - X0
        layers.append(d.add(f"grid{v}", "shape", {
            "kind": "rect", "color": "#1e293b",
            "size": keys((0, [0, 2]), (0.3, [0, 2], E), (1.0, [w, 2])),
            "center": keys((0, [X0, y]), (0.3, [X0, y], E), (1.0, [X0 + w / 2, y]))}))
        layers.append(d.add(f"gridlabel{v}", "text", {
            "text": str(v), "font": MONO, "weight": 400, "size": 22, "color": "#64748b",
            "align": "right", "valign": "middle", "position": [140, y],
            "opacity": keys((0, 0), (0.3, 0, E), (1.0, 1))}))
    layers.append(d.add("baseline", "shape", {
        "kind": "rect", "color": "#475569",
        "size": keys((0, [0, 3]), (0.3, [0, 3], E), (1.0, [X1 - X0, 3])),
        "center": keys((0, [X0, BASE]), (0.3, [X0, BASE], E), (1.0, [(X0 + X1) / 2, BASE]))}))
    slot = (X1 - X0) / len(VALUES)
    for i, (v, m) in enumerate(zip(VALUES, MONTHS)):
        cx = X0 + slot * (i + 0.5)
        t0, t1 = 0.8 + 0.12 * i, 0.8 + 0.12 * i + 0.8
        h = v * PXU
        color = "#f472b6" if i == len(VALUES) - 1 else "#38bdf8"
        layers.append(d.add(f"bar{i}", "shape", {
            "kind": "rect", "color": color, "radius": 6,
            "size": keys((0, [84, 0]), (t0, [84, 0], E), (t1, [84, h])),
            "center": keys((0, [cx, BASE]), (t0, [cx, BASE], E), (t1, [cx, BASE - h / 2]))}))
        layers.append(d.add(f"value{i}", "text", {
            "text": str(v), "font": MONO, "weight": 600, "size": 26, "color": "#ffffff",
            "align": "center", "valign": "bottom",
            "number": keys((0, 0), (t0, 0, E), (t1, v)), "decimals": 0,
            "opacity": keys((0, 0), (t0, 0), (t0 + 0.2, 1)),
            "position": keys((0, [cx, BASE - 12]), (t0, [cx, BASE - 12], E), (t1, [cx, BASE - h - 12]))}))
        layers.append(d.add(f"month{i}", "text", {
            "text": m, "font": FONT, "weight": 500, "size": 26, "color": "#94a3b8",
            "align": "center", "valign": "top", "position": [cx, 920],
            "opacity": keys((0, 0), (0.3, 0, E), (1.0, 1))}))
    pts = []
    for i, v in enumerate(TARGETS):
        pts += [round(X0 + slot * (i + 0.5), 2), BASE - v * PXU]
    layers.append(d.add("target", "path", {
        "kind": "polyline", "points": pts, "stroke": 5, "join": "round", "cap": "round",
        "color": "#fbbf24",
        "trim_end": keys((0, 0), (3.0, 0, "in_out_cubic"), (5.0, 1))}))
    for i in range(len(TARGETS)):
        layers.append(d.add(f"dot{i}", "shape", {
            "kind": "circle", "color": "#fbbf24", "size": [16, 16],
            "center": [pts[2 * i], pts[2 * i + 1]],
            "scale": keys((0, 0), (5.0, 0, E), (5.4, 1))}))
    # legend
    leg = keys((0, 0), (3.0, 0, E), (3.5, 1))
    layers.append(d.add("leg_bar", "shape", {
        "kind": "rect", "color": "#38bdf8", "radius": 3, "size": [22, 22],
        "center": [1471, 110], "opacity": leg}))
    layers.append(d.add("leg_bar_text", "text", {
        "text": "Actual", "font": FONT, "weight": 500, "size": 26, "color": "#cbd5e1",
        "valign": "middle", "position": [1494, 110], "opacity": leg}))
    layers.append(d.add("leg_line", "shape", {
        "kind": "rect", "color": "#fbbf24", "radius": 2.5, "size": [36, 5],
        "center": [1638, 110], "opacity": leg}))
    layers.append(d.add("leg_line_text", "text", {
        "text": "Target", "font": FONT, "weight": 500, "size": 26, "color": "#cbd5e1",
        "valign": "middle", "position": [1668, 110], "opacity": leg}))
    out = d.over(layers, "frame")
    d.write("chart.json", out)


# ---------------------------------------------------------------------------
# (c) footage: 1080x1920 composite over a NASA clip, with word-timed captions
# ---------------------------------------------------------------------------
PAGES = [  # one caption page per phrase; (start, end, word); a page's last word
    # lasts until the next page starts, so "which word is lit" never depends on
    # how a tool treats the gaps between words
    [(0.40, 0.70, "Day"), (0.70, 1.10, "twenty"), (1.10, 1.30, "of"), (1.30, 1.90, "Artemis"),
     (1.90, 2.80, "I.")],
    [(2.80, 3.30, "Orion"), (3.30, 3.75, "closes"), (3.75, 3.95, "in"), (3.95, 4.15, "on"),
     (4.15, 4.35, "the"), (4.35, 5.40, "Moon")],
    [(5.40, 5.75, "ahead"), (5.75, 5.90, "of"), (5.90, 6.10, "its"), (6.10, 6.55, "return"),
     (6.55, 7.05, "flyby"), (7.05, 7.90, "burn.")],
    [(7.90, 8.60, "Splashdown"), (8.60, 8.80, "is"), (8.80, 9.30, "December"), (9.30, 10.00, "11.")],
]


def footage():
    d = Doc(1080, 1920)
    # cover: the 1920x1080 clip scaled to 1920 px tall (3413.33 wide), centered,
    # pushed in from 1.00 to 1.08 about the frame center over the 10 s
    def cover(s):
        w, h = 1920 * 1920 / 1080 * s, 1920 * s
        return [round(540 - w / 2, 3), round(960 - h / 2, 3), round(w, 3), round(h, 3)]
    clip = d.add("clip", "video", {"src": CLIP, "start": 0, "fit": "fill",
                                   "rect": keys((0, cover(1.0)), (10, cover(1.08)))})
    shade = d.add("shade", "gradient", {"kind": "linear", "stops": "0:#00000000, 1:#000000cc",
                                        "start": [0, 1100], "end": [0, 1920], "space": "srgb"})
    label = d.add("label", "text", {
        "text": "NASA · ARTEMIS I · FLIGHT DAY 20", "font": MONO, "weight": 500,
        "size": 30, "tracking": 4, "color": "#ffffffd9", "align": "center",
        "position": [540, 140], "opacity": keys((0, 0), (0.2, 0, "out_cubic"), (0.8, 1))})
    layers = [clip, shade, label]
    for p, words in enumerate(PAGES):
        start = words[0][0]
        end = PAGES[p + 1][0][0] if p + 1 < len(PAGES) else 10.0
        layers.append(d.add(f"caption{p}", "captions", {
            "words": "\n".join(f"{a:.2f} {b:.2f} {w}" for a, b, w in words),
            "style": "karaoke", "font": FONT, "weight": 800, "size": 72,
            "color": "#ffffff", "highlight": "#ffd23f", "width": 880, "max_lines": 2,
            "line_height": 1.18, "position": [540, 1450], "safe": "none", "linger": 5},
            timing={"in": start, "out": end}))
    out = d.over(layers, "frame")
    d.write("footage.json", out)


# ---------------------------------------------------------------------------
# (d) effects: 1920x1080 blurred colour fields, glowing title, motion-blurred whip,
# grain and vignette (the case that favours a GPU engine; see README)
# ---------------------------------------------------------------------------
BLOBS = [("#7c3aed", [600, 420], [1000, 640]),
         ("#06b6d4", [1340, 380], [980, 560]),
         ("#f43f5e", [900, 800], [720, 520])]


def effects():
    d = Doc(1920, 1080, motion_blur={"samples": 8, "shutter": 0.5, "max_samples": 32})
    E = "out_cubic"
    layers = [d.add("bg", "solid", {"color": "#07060d"})]
    for i, (color, a, b) in enumerate(BLOBS):
        blob = d.add(f"blob{i}", "shape", {
            "kind": "circle", "color": color, "size": [560, 560],
            "center": keys((0, a, "in_out_sine"), (5, b, "in_out_sine"), (10, a))})
        layers.append(d.add(f"blob{i}_blur", "blur", {"radius": 80}, {"source": blob}))
    title_text = d.add("title_text", "text", {
        "text": "GLOW", "font": FONT, "weight": 900, "size": 260, "color": "#ffffff",
        "align": "center", "valign": "middle", "position": [960, 540],
        "opacity": keys((0, 0), (0.5, 0, E), (1.5, 1)),
        "scale": keys((0, 0.9), (0.5, 0.9, E), (1.5, 1))})
    layers.append(d.add("title_glow", "glow", {"intensity": 1.0, "radius": 24},
                        {"source": title_text}))
    layers.append(d.add("subtitle", "text", {
        "text": "GPU EFFECTS TEST", "font": MONO, "weight": 500, "size": 32, "tracking": 8,
        "color": "#c4b5fd", "align": "center", "position": [960, 720],
        "opacity": keys((0, 0), (1.2, 0, E), (1.8, 1))}))
    for i, (t0, x0, x1) in enumerate([(1.0, -300, 2220), (6.0, 2220, -300)]):
        layers.append(d.add(f"whip{i}", "shape", {
            "kind": "rect", "color": "#ffffff", "size": [360, 28], "radius": 14,
            "center": keys((t0, [x0, 860], "in_out_cubic"), (t0 + 0.6, [x1, 860]))},
            timing={"in": t0, "out": t0 + 0.6}))
    scene = d.over(layers, "frame")
    vig = d.add("vignette", "vignette", {}, {"source": scene})
    out = d.add("grain", "grain", {"amount": 0.07}, {"source": vig})
    d.write("effects.json", out)


if __name__ == "__main__":
    title()
    chart()
    footage()
    effects()
