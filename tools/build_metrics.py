#!/usr/bin/env python3
"""Dev tool: regenerates bento/data/metrics.json (glyph advance widths).

The generator needs to know how wide a piece of text will be so it can fit it
inside a card. Instead of shipping fontTools to every user, we measure the
bundled Sora font once and store the advances (in em units) as JSON.

    pip install fonttools brotli
    python tools/build_metrics.py
"""
import json
import os

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "bento", "data", "fonts")
WEIGHTS = [200, 400, 500, 600, 700, 800]


def advances(font):
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    return {chr(cp): round(hmtx[name][0] / upm, 4) for cp, name in cmap.items()}


def main():
    out = {"sora": {}, "outline": {}}
    for w in WEIGHTS:
        f = TTFont(os.path.join(FONTS, "sora-subset.woff2"))
        inst = instancer.instantiateVariableFont(f, {"wght": w})
        out["sora"][str(w)] = advances(inst)
    out["outline"]["200"] = advances(TTFont(os.path.join(FONTS, "sora-outline-digits.woff2")))
    path = os.path.join(ROOT, "bento", "data", "metrics.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    chars = "".join(sorted(out["sora"]["800"]))
    print("wrote", path, "-", len(chars), "glyphs")
    for c in "…—→·é":
        print(hex(ord(c)), c in out["sora"]["800"])


if __name__ == "__main__":
    main()
