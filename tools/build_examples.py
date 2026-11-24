#!/usr/bin/env python3
"""Dev tool: regenerates the example images used in the README (demo data, no network).

    python tools/build_examples.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bento import render, stats  # noqa: E402
from bento.config import DEFAULT_PATH, load  # noqa: E402

OUT = os.path.join(ROOT, "examples", "img")


def main():
    os.makedirs(OUT, exist_ok=True)
    cfg = load(DEFAULT_PATH)  # the built-in bento used when a repo has no bento.yml
    cfg["output"] = "zero-config.svg"
    for path in render.build(cfg, stats.demo("octocat"), OUT):
        print("wrote", os.path.relpath(path, ROOT))
    names = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "examples")) if f.endswith(".yml"))
    for name in names:
        cfg = load(os.path.join(ROOT, "examples", f"{name}.yml"))
        cfg["output"] = f"{name}.svg"
        data = stats.demo("octocat")
        for path in render.build(cfg, data, OUT):
            print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
