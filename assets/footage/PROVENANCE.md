# orion_moon_fd20.mp4

The clip every tool composites in the `footage` scene. Public-domain NASA footage.

- **NASA ID:** FD 20 2
- **Title:** Flight Day 20: To the Moon
- **Date created:** 2022-12-05 (NASA Johnson Space Center)
- **Details page:** https://images.nasa.gov/details/FD%2020%202
- **Original file:** https://images-assets.nasa.gov/video/FD%2020%202/FD%2020%202~orig.mp4
  (39,593,779 bytes, sha256 `0eef27e910fdd183c38887b7d1601d2e38efc13ff5623e5ccc6c5f349f893a44`)
- **This file:** the first 20 s of the original, full frame, no audio, re-encoded to
  H.264 High (1920x1080, 30 fps, about 7.8 Mbit/s, 600 frames).
  sha256 `2281c77c0f02dd01d1d84d67c8b07cf84147e25c46ab71e86e5d8e9a85bef1cb`
  (also in `../SHA256SUMS`). The benchmark uses seconds 0 to 10.
- **NASA's description (excerpt):** "On flight day 20, Orion approached the Moon ahead of
  the return powered flyby burn that committed the spacecraft to splashdown on Sunday, Dec. 11."
- **Licence:** NASA media is generally not subject to copyright in the United States; see
  NASA's media usage guidelines: https://www.nasa.gov/nasa-brand-center/images-and-media/
  NASA does not endorse this benchmark or any of the tools in it.

To rebuild it from NASA's original, cut 0:00 to 0:20 with any FFmpeg and encode to H.264
at about 8 Mbit/s. The bytes will differ from this file; what matters is that all three
tools read the same file, so the checked-in copy is the one to use when comparing results.
