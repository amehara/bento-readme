"""Config + stats -> SVG documents."""
import os

from . import layout
from .cards import CARDS, Ctx
from .palettes import THEMES
from .svg import Canvas


def render_svg(cfg, stats, theme_name):
    theme = THEMES[theme_name]
    cv = Canvas(theme)
    sizes = [(c["cols"], c["units"]) for c in cfg["cards"]]
    spots, total = layout.place(sizes)
    for i, (card, (col, unit)) in enumerate(zip(cfg["cards"], spots)):
        rect = layout.rect(col, unit, card["cols"], card["units"])
        ctx = Ctx(cv, theme, stats, cfg["palettes"], i)
        CARDS[card["spec"]["type"]].fn(ctx, card["spec"], *rect)
    hero = next((c["spec"] for c in cfg["cards"] if c["spec"]["type"] == "hero"), {})
    title = " · ".join(p for p in (hero.get("title") or cfg["user"], hero.get("subtitle")) if p) or "bento"
    return cv.document(layout.CANVAS_W, layout.canvas_height(total), title, cfg["alt"])


def outputs(cfg):
    """[(theme, relative path)] for this config. `auto` writes a dark and a light file."""
    out = cfg["output"]
    if cfg["theme"] != "auto":
        return [(cfg["theme"], out)]
    stem, ext = os.path.splitext(out)
    return [("dark", f"{stem}-dark{ext}"), ("light", f"{stem}-light{ext}")]


def build(cfg, stats, base_dir="."):
    written = []
    for theme_name, rel in outputs(cfg):
        path = os.path.join(base_dir, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_svg(cfg, stats, theme_name))
        written.append(path)
    return written


def readme_snippet(cfg):
    alt = cfg["alt"].replace('"', "&quot;")
    outs = outputs(cfg)
    if cfg["theme"] != "auto":
        return f'<img src="./{outs[0][1]}" alt="{alt}" width="100%">'
    dark, light = outs[0][1], outs[1][1]
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="./{dark}">\n'
        f'  <img src="./{light}" alt="{alt}" width="100%">\n'
        "</picture>"
    )
