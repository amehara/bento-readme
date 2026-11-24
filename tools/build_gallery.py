#!/usr/bin/env python3
"""Dev tool: renders every built-in theme and every palette into docs/img/ (demo data, no network).

    python tools/build_gallery.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bento import palettes, render, stats, themes  # noqa: E402
from bento.config import load  # noqa: E402

OUT = os.path.join(ROOT, "docs", "img")

THEME_CARDS = """
cards:
  - {type: hero, size: 2x2, title: your name, subtitle: THEME, intro: ["a theme to make", "your profile yours."], headline: [hello, world.]}
  - {type: number, source: contributions, label: [contributions, this year], color: ocean}
  - {type: streak}
  - {type: stack, items: [python, rust, docker, git]}
  - {type: status, word: "on", caption: available, color: meadow}
"""


def build(text, out_name, folder):
    path = os.path.join(folder, "bento.yml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    cfg = load(path)
    cfg["output"] = out_name
    return render.build(cfg, stats.demo("octocat"), OUT)


def main():
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name in themes.THEMES:
            cards = THEME_CARDS.replace("THEME", name)
            build(f"theme: {name}\nstyle: {{padding: 16, gap: 12, background: theme}}\n{cards}", f"theme-{name}.svg", tmp)
            print("wrote theme", name)
        # one image with every palette
        items = "\n".join(f"  - {{type: number, value: \"{n}\", color: {n}, label: [palette]}}" for n in palettes.PALETTES)
        build("theme: dark\nstyle: {text_case: lower, background: theme, padding: 24}\ncards:\n" + items + "\n", "palettes.svg", tmp)
        print("wrote palettes")


if __name__ == "__main__":
    main()
