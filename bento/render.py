"""Config + stats -> SVG documents."""
import copy
import os

from . import layout, metrics
from .cards import CARDS, Ctx
from .svg import Canvas

# card keys that hold text the viewer reads; `style.text_case` is applied to these
TEXT_KEYS = ("title", "subtitle", "intro", "headline", "label", "caption", "eyebrow", "value", "word", "text",
             "body", "author", "unit", "updated_label", "items", "minis")


def _case(value, mode):
    if isinstance(value, str):
        return value.lower() if mode == "lower" else value.upper()
    if isinstance(value, list):
        return [_case(v, mode) for v in value]
    if isinstance(value, dict):
        return {k: (_case(v, mode) if k in ("name", "label", "value") else v) for k, v in value.items()}
    return value


def apply_case(spec, mode):
    if mode == "keep":
        return spec
    out = dict(spec)
    for k in TEXT_KEYS:
        if k in out:
            out[k] = _case(out[k], mode)
    return out


def _stats_case(stats, mode):
    if mode == "keep":
        return stats
    s = copy.deepcopy(stats)
    if s.get("now"):
        s["now"] = {k: _case(v, mode) for k, v in s["now"].items()}
    s["languages"] = [[_case(n, mode), p] for n, p in s.get("languages", [])]
    s["top_repos"] = [dict(r, name=_case(r.get("name", ""), mode)) for r in s.get("top_repos", [])]
    return s


def render_svg(cfg, stats, theme):
    style = cfg["style"]
    metrics.set_font(style["font"])
    geo = layout.geometry(style["padding"], style["gap"])
    cv = Canvas(theme, style, cfg["gradients"])
    spots, total = layout.place([(c["cols"], c["units"]) for c in cfg["cards"]])
    width, height = layout.CANVAS_W, layout.canvas_height(geo, total)
    cv.background(width, height, cfg["palettes"])
    data = _stats_case(stats, style["text_case"])
    for i, (card, (col, unit)) in enumerate(zip(cfg["cards"], spots)):
        rect = layout.rect(geo, col, unit, card["cols"], card["units"])
        spec = apply_case(card["spec"], style["text_case"])
        CARDS[spec["type"]].fn(Ctx(cv, theme, data, cfg["palettes"], i, spec), spec, *rect)
    cv.finish(width, height)
    hero = next((c["spec"] for c in cfg["cards"] if c["spec"]["type"] == "hero"), {})
    title = " · ".join(p for p in (hero.get("title") or cfg["user"], hero.get("subtitle")) if p) or "bento"
    return cv.document(width, height, title, cfg["alt"])


def outputs(cfg):
    """[(suffix, theme, relative path)]. A dark/light pair writes `-dark` and `-light` files."""
    out = cfg["output"]
    if len(cfg["variants"]) == 1:
        return [("", cfg["variants"][0][1], out)]
    stem, ext = os.path.splitext(out)
    return [(name, theme, f"{stem}-{name}{ext}") for name, theme in cfg["variants"]]


def build(cfg, stats, base_dir="."):
    written = []
    for _, theme, rel in outputs(cfg):
        path = os.path.join(base_dir, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_svg(cfg, stats, theme))
        written.append(path)
    return written


def readme_snippet(cfg):
    alt = cfg["alt"].replace('"', "&quot;")
    outs = outputs(cfg)
    if len(outs) == 1:
        return f'<img src="./{outs[0][2]}" alt="{alt}" width="100%">'
    dark, light = outs[0][2], outs[1][2]
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="./{dark}">\n'
        f'  <img src="./{light}" alt="{alt}" width="100%">\n'
        "</picture>"
    )
