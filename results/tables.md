### Headline: warm median seconds (300 frames, 10 s video, H.264 CRF 18)

| Composition | ultrafast | Remotion default | Remotion fastest | HyperFrames default | HyperFrames fastest |
|---|---:|---:|---:|---:|---:|
| title | **0.66** | 4.73 (7.2×) | 2.32 (3.5×) | 3.92 (5.9×) | 3.53 (5.3×) |
| chart | **0.72** | 4.45 (6.2×) | 2.25 (3.1×) | 3.71 (5.2×) | 3.31 (4.6×) |
| footage | **0.78** | 8.53 (10.9×) | 6.69 (8.6×) | 5.05 (6.5×) | 4.46 (5.7×) |
| effects | **0.74** | 5.95 (8.1×) | 2.98 (4.0×) | 6.42 (8.7×) | 5.23 (7.1×) |

(×) = that time divided by ultrafast's: how many times longer the tool took.

Fastest configuration found for each browser tool:

- title: Remotion `prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 24`, HyperFrames `--workers 8`
- chart: Remotion `prebuilt bundle, --gl=angle-egl, --concurrency 16`, HyperFrames `--workers 4`
- footage: Remotion `prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 8`, HyperFrames `--workers 8`
- effects: Remotion `prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 12`, HyperFrames `--workers 12`

### Cold first run (tool caches cleared), seconds

| Composition | ultrafast | Remotion | HyperFrames |
|---|---:|---:|---:|
| title | 1.77 | 8.46 | 3.93 |
| chart | 2.09 | 8.41 | 3.66 |
| footage | 1.99 | 12.56 | 5.55 |
| effects | 2.01 | 9.69 | 6.43 |

### Was the machine quiet?

- runs counted: 560; discarded because other work overlapped them: 3; set aside as invalid (`invalid` in runs.jsonl gives why): 1; failed: 0
- CPU busy just before a run (whole machine, threads of 32): median 0.19, max 1.45
- 1-minute load average at the start of a run: median 2.62, max 18.51 (includes the benchmark's own previous run)
- other processes' CPU during a run: median 0.2 threads, max 1.11

### Every measured configuration

| Composition | Tool | Configuration | Warm median s (min–max, n) | Cold s | CPU threads avg | Peak RAM MiB | GPU util % (mean) | GPU mem MiB | Output MB |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| title | ultrafast | default command | 0.66 (0.65–0.71, 5) | 1.77 | 0.9 | 73 | 14 | 1079 | 1.1 |
| title | remotion | prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 24 | 2.32 (2.31–2.60, 5) | – | 5.1 | 1668 | 8 | 1730 | 1.5 |
| title | remotion | prebuilt bundle, --gl=vulkan, --concurrency 24 | 2.42 (2.28–2.47, 5) | – | 8.2 | 3027 | 5 | 1087 | 0.7 |
| title | remotion | prebuilt bundle, --gl=angle-egl, --concurrency 12 | 2.63 (2.62–2.66, 5) | – | 6.5 | 2525 | 0 | 0 | 0.6 |
| title | remotion | prebuilt bundle, --concurrency 12 | 3.19 (3.18–3.22, 5) | – | 5.3 | 2668 | 0 | 0 | 0.6 |
| title | remotion | --gl=angle-egl --concurrency 12 | 4.04 (3.99–4.08, 5) | – | 4.8 | 3121 | 0 | 0 | 0.6 |
| title | remotion | --concurrency 12 | 4.54 (4.53–4.59, 5) | – | 4.2 | 3239 | 0 | 0 | 0.6 |
| title | remotion | --concurrency 32 (max) | 4.67 (4.67–4.72, 5) | – | 5.3 | 4849 | 0 | 0 | 0.6 |
| title | remotion | default command | 4.73 (4.65–4.78, 5) | 8.46 | 3.8 | 2911 | 0 | 0 | 0.6 |
| title | hyperframes | --workers 8 | 3.53 (3.50–3.57, 5) | – | 4.8 | 2548 | 6 | 776 | 1.1 |
| title | hyperframes | default command | 3.92 (3.91–3.96, 5) | 3.93 | 4.2 | 2268 | 4 | 582 | 1.1 |
| title | hyperframes | --gpu --workers 8 | 3.93 (3.82–3.96, 5) | – | 2.9 | 1532 | 6 | 1344 | 2.2 |
| title | hyperframes | --gpu (NVENC encode) | 4.33 (4.27–4.36, 5) | – | 2.6 | 1253 | 5 | 1150 | 2.2 |
| title | hyperframes | --workers 24 (max) | 4.40 (4.34–4.48, 5) | – | 6.0 | 4901 | 7 | 2318 | 1.1 |
| chart | ultrafast | default command | 0.72 (0.68–0.76, 5) | 2.09 | 1.0 | 125 | 16 | 1287 | 0.4 |
| chart | remotion | prebuilt bundle, --gl=angle-egl, --concurrency 16 | 2.25 (2.24–2.31, 5) | – | 6.1 | 2492 | 0 | 0 | 0.2 |
| chart | remotion | prebuilt bundle, --gl=vulkan, --concurrency 24 | 2.27 (2.24–2.32, 5) | – | 6.8 | 2811 | 5 | 1133 | 0.3 |
| chart | remotion | prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 24 | 2.31 (2.30–2.47, 5) | – | 5.0 | 1698 | 7 | 1753 | 0.6 |
| chart | remotion | prebuilt bundle, --concurrency 16 | 2.90 (2.86–2.91, 5) | – | 4.8 | 2667 | 0 | 0 | 0.2 |
| chart | remotion | --gl=angle-egl --concurrency 16 | 3.65 (3.64–3.72, 5) | – | 4.3 | 3075 | 0 | 0 | 0.2 |
| chart | remotion | --concurrency 16 | 4.25 (4.22–4.34, 5) | – | 3.8 | 3232 | 0 | 0 | 0.2 |
| chart | remotion | --concurrency 32 (max) | 4.42 (4.32–4.46, 5) | – | 4.7 | 4441 | 0 | 0 | 0.2 |
| chart | remotion | default command | 4.45 (4.40–4.51, 5) | 8.41 | 3.1 | 2633 | 0 | 0 | 0.2 |
| chart | hyperframes | --workers 4 | 3.31 (3.29–3.34, 5) | – | 3.5 | 1976 | 2 | 421 | 0.3 |
| chart | hyperframes | default command | 3.71 (3.63–3.72, 5) | 3.66 | 3.7 | 2286 | 3 | 629 | 0.3 |
| chart | hyperframes | --gpu --workers 4 | 3.74 (3.70–3.77, 5) | – | 2.2 | 937 | 4 | 980 | 0.4 |
| chart | hyperframes | --gpu (NVENC encode) | 4.11 (4.08–4.17, 5) | – | 2.4 | 1233 | 4 | 1189 | 0.4 |
| chart | hyperframes | --workers 24 (max) | 4.17 (4.15–4.19, 5) | – | 6.1 | 4972 | 6 | 2479 | 0.3 |
| footage | ultrafast | default command | 0.78 (0.75–0.88, 5) | 1.99 | 1.0 | 132 | 12 | 1316 | 2.9 |
| footage | remotion | prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 8 | 6.69 (6.58–6.83, 5) | – | 4.1 | 3962 | 5 | 1724 | 3.1 |
| footage | remotion | prebuilt bundle, --gl=vulkan, --concurrency 8 | 6.75 (6.65–6.84, 5) | – | 5.2 | 5095 | 9 | 1061 | 2.4 |
| footage | remotion | prebuilt bundle, --gl=angle-egl, --concurrency 8 | 6.75 (6.69–6.81, 5) | – | 5.2 | 5016 | 0 | 0 | 2.4 |
| footage | remotion | prebuilt bundle, --concurrency 8 | 7.22 (7.12–7.42, 5) | – | 5.7 | 5698 | 0 | 0 | 2.5 |
| footage | remotion | --gl=angle-egl --concurrency 8 | 8.15 (8.00–8.34, 5) | – | 4.6 | 5747 | 0 | 0 | 2.4 |
| footage | remotion | default command | 8.53 (8.32–8.59, 5) | 12.56 | 5.1 | 6212 | 0 | 0 | 2.5 |
| footage | remotion | --concurrency 8 | 8.63 (8.57–8.68, 5) | – | 5.1 | 6474 | 0 | 0 | 2.5 |
| footage | remotion | --concurrency 32 (max) | 21.66 (21.30–21.98, 5) | – | 7.6 | 17853 | 0 | 0 | 2.5 |
| footage | hyperframes | --workers 8 | 4.46 (4.42–4.49, 5) | – | 5.5 | 2789 | 5 | 2213 | 4.7 |
| footage | hyperframes | --gpu --workers 8 | 4.81 (4.71–4.83, 5) | – | 3.1 | 1773 | 6 | 2788 | 10.9 |
| footage | hyperframes | default command | 5.05 (5.03–5.10, 5) | 5.55 | 4.5 | 2464 | 4 | 2053 | 4.7 |
| footage | hyperframes | --workers 24 (max) | 5.19 (5.17–5.36, 5) | – | 6.9 | 5264 | 7 | 3615 | 4.7 |
| footage | hyperframes | --gpu (NVENC encode) | 5.39 (5.38–5.43, 5) | – | 2.6 | 1468 | 5 | 2608 | 10.9 |
| effects | ultrafast | default command | 0.74 (0.72–0.79, 5) | 2.01 | 0.9 | 116 | 30 | 1279 | 1.6 |
| effects | remotion | prebuilt bundle, --gl=vulkan, NVENC (--hardware-acceleration, no CRF), --concurrency 12 | 2.98 (2.95–2.98, 5) | – | 3.1 | 1059 | 15 | 1347 | 2.7 |
| effects | remotion | prebuilt bundle, --gl=vulkan, --concurrency 12 | 3.20 (3.18–3.21, 5) | – | 13.6 | 2180 | 12 | 728 | 16.0 |
| effects | remotion | prebuilt bundle, --gl=angle-egl, --concurrency 12 | 4.13 (4.09–4.15, 5) | – | 20.2 | 3390 | 0 | 0 | 16.2 |
| effects | remotion | prebuilt bundle, --concurrency 12 | 4.51 (4.49–4.54, 5) | – | 17.4 | 3601 | 0 | 0 | 16.2 |
| effects | remotion | --gl=angle-egl --concurrency 12 | 5.48 (5.46–5.50, 5) | – | 15.6 | 3978 | 0 | 0 | 16.2 |
| effects | remotion | --concurrency 12 | 5.86 (5.84–5.88, 5) | – | 13.8 | 4137 | 0 | 0 | 16.2 |
| effects | remotion | default command | 5.95 (5.82–6.04, 5) | 9.69 | 12.6 | 3471 | 0 | 0 | 16.2 |
| effects | remotion | --concurrency 32 (max) | 6.42 (6.35–6.49, 5) | – | 15.5 | 7398 | 0 | 0 | 16.2 |
| effects | hyperframes | --workers 12 | 5.23 (5.21–5.25, 5) | – | 10.5 | 3175 | 31 | 4555 | 18.1 |
| effects | hyperframes | --gpu --workers 12 | 5.30 (5.25–5.32, 5) | – | 4.5 | 2450 | 30 | 5121 | 17.2 |
| effects | hyperframes | default command | 6.42 (6.38–6.44, 5) | 6.43 | 7.0 | 2281 | 21 | 2325 | 18.0 |
| effects | hyperframes | --gpu (NVENC encode) | 6.56 (6.55–6.63, 5) | – | 2.7 | 1386 | 22 | 2886 | 17.2 |
| effects | hyperframes | --workers 24 (max) | 7.87 (7.84–7.89, 5) | – | 8.0 | 4752 | 22 | 8128 | 18.1 |

### Concurrency sweep (median of 2 warm runs, seconds)

- title, remotion: 2 → 9.19, 4 → 6.13, 8 → 4.60, 12 → 4.50, 16 → 4.52, 24 → 4.57, 32 → 4.67
- title, remotion, prebuilt bundle + `--gl=vulkan`: 8 → 3.51, 12 → 2.77, 16 → 2.40, 24 → 2.29, 32 → 2.41
- title, hyperframes: 2 → 4.41, 4 → 3.69, 8 → 3.50, 12 → 3.73, 16 → 3.98, 24 → 4.38
- chart, remotion: 2 → 9.01, 4 → 5.77, 8 → 4.42, 12 → 4.19, 16 → 4.18, 24 → 4.19, 32 → 4.34
- chart, remotion, prebuilt bundle + `--gl=vulkan`: 8 → 2.82, 12 → 2.72, 16 → 2.37, 24 → 2.28, 32 → 2.32
- chart, hyperframes: 2 → 3.55, 4 → 3.26, 8 → 3.31, 12 → 3.49, 16 → 3.69, 24 → 4.21
- footage, remotion: 2 → 12.55, 4 → 8.45, 8 → 8.32, 12 → 10.01, 16 → 11.80, 24 → 16.41, 32 → 21.51
- footage, remotion, prebuilt bundle + `--gl=vulkan`: 8 → 6.71, 12 → 8.36, 16 → 10.03, 24 → 13.72, 32 → 16.82
- footage, hyperframes: 2 → 6.31, 4 → 4.92, 8 → 4.46, 12 → 4.49, 16 → 4.72, 24 → 5.21
- effects, remotion: 2 → 12.06, 4 → 7.67, 8 → 5.91, 12 → 5.86, 16 → 5.95, 24 → 6.15, 32 → 6.43
- effects, remotion, prebuilt bundle + `--gl=vulkan`: 8 → 3.83, 12 → 3.17, 16 → 3.21, 24 → 3.28, 32 → 3.39
- effects, hyperframes: 2 → 11.75, 4 → 7.38, 8 → 5.35, 12 → 5.19, 16 → 5.59, 24 → 7.92

### One still frame (t = 5 s) from the CLI, warm median seconds

| Composition | ultrafast `render --at 5` | Remotion `still --frame=150` | HyperFrames `snapshot --at 5` |
|---|---:|---:|---:|
| title | 0.22 | 2.19 | 1.52 |
| chart | 0.20 | 2.16 | 1.52 |
| footage | 0.70 | 2.29 | 2.10 |
| effects | 0.46 | 2.35 | 1.96 |

### Same picture? Luma SSIM / PSNR against ultrafast's video, all 300 frames

| Composition | Output compared with ultrafast's | SSIM | PSNR dB |
|---|---|---:|---:|
| title | remotion default | 0.989 | 29.9 |
| title | hyperframes default | 0.985 | 29.0 |
| title | remotion fastest (bundled-vulkan-nvenc-c24) | 0.989 | 30.0 |
| title | hyperframes fastest (w8) | 0.985 | 29.0 |
| chart | remotion default | 0.993 | 34.6 |
| chart | hyperframes default | 0.991 | 34.0 |
| chart | remotion fastest (bundled-angle-egl-c16) | 0.993 | 34.6 |
| chart | hyperframes fastest (w4) | 0.991 | 34.0 |
| footage | remotion default | 0.948 | 27.5 |
| footage | hyperframes default | 0.936 | 25.8 |
| footage | remotion fastest (bundled-vulkan-nvenc-c8) | 0.948 | 27.6 |
| footage | hyperframes fastest (w8) | 0.936 | 25.8 |
| effects | remotion default | 0.628 | 25.2 |
| effects | hyperframes default | 0.628 | 25.5 |
| effects | remotion fastest (bundled-vulkan-nvenc-c12) | 0.643 | 25.4 |
| effects | hyperframes fastest (w12) | 0.628 | 25.5 |
