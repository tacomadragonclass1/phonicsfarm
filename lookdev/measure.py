#!/usr/bin/env python3
"""Measure a look-dev plate's grade against the Cycles control.

    python3 lookdev/measure.py /tmp/lookdev-*.png

⭐ The point of this file is that "it still looks too green" is not a number
and cannot be chased. Sampled across the whole frame, the published build sits
at mean saturation 0.707 against the control's 0.304. That is the acid green
said in a way that can be aimed at and checked.

⛔ Sky and void are dropped (low saturation AND high value) or they drag the
mean toward nothing. Compare like-for-like framings only.
"""

import colorsys
import sys

from PIL import Image

TARGET_SAT = 0.304     # the Cycles control, measured
TARGET_VAL = 0.546


def stats(path, step=4):
    image = Image.open(path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    sats, vals = [], []
    for y in range(0, height, step):
        for x in range(0, width, step):
            r, g, b = pixels[x, y]
            _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < 0.08 and v > 0.60:
                continue
            sats.append(s)
            vals.append(v)
    count = len(sats)
    return sum(sats) / count, sum(vals) / count, count


if __name__ == "__main__":
    print("%-26s %8s %8s   %s" % ("plate", "sat", "val", "vs control"))
    for path in sys.argv[1:]:
        sat, val, _ = stats(path)
        name = path.rsplit("/", 1)[-1]
        print("%-26s %8.3f %8.3f   sat %+.0f%%  val %+.0f%%"
              % (name, sat, val,
                 (sat / TARGET_SAT - 1) * 100, (val / TARGET_VAL - 1) * 100))
