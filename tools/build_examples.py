#!/usr/bin/env python3
"""Dev tool: regenerates the example images used in the README (demo data, no network).

    python tools/build_examples.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bento import render, stats  # noqa: E402
from bento.config import load  # noqa: E402

OUT = os.path.join(ROOT, "examples", "img")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in ("designer", "developer", "minimal"):
        cfg = load(os.path.join(ROOT, "examples", f"{name}.yml"))
        cfg["output"] = f"{name}.svg"
        data = stats.demo("octocat")
        for path in render.build(cfg, data, OUT):
            print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
