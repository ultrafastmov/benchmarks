#!/usr/bin/env bash
# Installs the pinned Remotion and HyperFrames packages into this folder, the
# browsers they render with, and copies the shared assets (fonts, the NASA clip,
# GSAP) into each project. Nothing is installed outside this folder.
set -euo pipefail
cd "$(dirname "$0")"
BENCH=$PWD
source harness/env.sh

echo "== checking the shared assets"
(cd assets && sha256sum -c SHA256SUMS)

echo "== FFmpeg for HyperFrames (a static GPL build with libx264, pinned by checksum)"
# HyperFrames encodes MP4 with libx264 from the FFmpeg it finds; some distributions'
# FFmpeg (Fedora's ffmpeg-free) has no libx264, and HyperFrames then falls back to the
# GPU encoder. This build is what an apt or brew FFmpeg gives it.
FF_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-11-21-12-37/ffmpeg-n9.0.2-61-gd59078794d-linux64-gpl-9.0.tar.xz
FF_SHA=010499a8a9855e477b1a0ebfa9602832526ec80eb306b58213a2b6cda7149607
if [ ! -x tools/ffmpeg/ffmpeg-n9.0.2-61-gd59078794d-linux64-gpl-9.0/bin/ffmpeg ]; then
  mkdir -p tools/ffmpeg
  curl -fsSL -o tools/ffmpeg/ffmpeg.tar.xz "$FF_URL"
  echo "$FF_SHA  tools/ffmpeg/ffmpeg.tar.xz" | sha256sum -c
  tar -xJf tools/ffmpeg/ffmpeg.tar.xz -C tools/ffmpeg
fi

echo "== Remotion (exact versions from remotion/package-lock.json)"
(cd remotion && npm ci --no-audit --no-fund)
mkdir -p remotion/public/fonts remotion/public/footage
cp assets/fonts/*.ttf remotion/public/fonts/
cp assets/footage/orion_moon_fd20.mp4 remotion/public/footage/
# downloads Remotion's pinned chrome-headless-shell into remotion/node_modules/.remotion
(cd remotion && npx remotion browser ensure)

echo "== HyperFrames (exact versions from hyperframes/package-lock.json)"
(cd hyperframes && npm ci --no-audit --no-fund)
for c in title chart footage effects; do
  mkdir -p "hyperframes/$c/assets/fonts" "hyperframes/$c/assets/footage"
  cp assets/fonts/*.ttf "hyperframes/$c/assets/fonts/"
  cp hyperframes/node_modules/gsap/dist/gsap.min.js "hyperframes/$c/assets/"
done
cp assets/footage/orion_moon_fd20.mp4 hyperframes/footage/assets/footage/
# downloads HyperFrames' pinned chrome-headless-shell into $HYPERFRAMES_CACHE_DIR
(cd hyperframes && npx hyperframes browser ensure)

echo "== ultrafast documents"
python3 ultrafast/build.py
echo "setup done"
