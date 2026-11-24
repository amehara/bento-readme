"""Card renderers. Each card type declares its keys, default size and allowed sizes."""
from . import metrics
from .layout import UNIT_H
from .palettes import FALLBACK_DOT, TECH_COLORS
from .svg import clean

SOURCES = ("contributions", "streak", "repos", "stars", "followers", "lines")
SOURCE_LABELS = {
    "contributions": "contributions",
    "streak": "streak",
    "repos": "repos",
    "stars": "stars",
    "followers": "followers",
    "lines": "lines of code",
}


class Ctx:
    """Everything a card needs besides its own config."""

    def __init__(self, canvas, theme, stats, palettes, index):
        self.cv = canvas
        self.t = theme
        self.stats = stats
        self.palettes = palettes
        self.index = index

    def palette(self, name, default):
        name = name or default
        if name not in self.palettes:
            raise ValueError(f"unknown color {name!r}; choose one of: {', '.join(sorted(self.palettes))}")
        return self.palettes[name]


def as_lines(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def compact(n):
    n = int(n)
    if n < 1000:
        return str(n)
    if n < 100_000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    if n < 1_000_000:
        return f"{round(n / 1000)}k"
    return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "m"


def value_of(spec, stats):
    if spec.get("source"):
        return compact(stats.get(spec["source"], 0))
    return str(spec.get("value", ""))


# --------------------------------------------------------------------------- hero
def hero(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    cv.card(x, y, w, h, 44, strong=True)
    pad = 36
    inner = w - pad * 2
    cv.fitted(x + pad, y + 70, inner, 34, spec.get("title", ""), t["text"], 800, -0.03)
    if spec.get("subtitle"):
        cv.fitted(x + pad, y + 102, inner, 17, spec["subtitle"], t["muted"], 600, 0)
    intro = as_lines(spec.get("intro"))[:2]
    headline = as_lines(spec.get("headline"))[:2]
    full = h >= 330 and headline
    for i, ln in enumerate(intro):
        cv.fitted(x + pad, y + 148 + i * 28, inner, 21, ln, t["text_soft"], 500, -0.01)
    if full:
        accent = cv.gradient(spec.get("accent", "pink"))
        cap = h * 0.34
        bottom = y + h - 30
        for i, ln in enumerate(reversed(headline)):
            size = metrics.fill(ln, w - 64, 800, -0.05, max_size=cap)
            cv.text(x + 32, bottom, ln, size, accent if i == 0 else t["text"], 800, -0.05)
            bottom -= size * 0.865


# ------------------------------------------------------------------------- number
def number(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    style = spec.get("style", "mesh")
    val = value_of(spec, c.stats)
    if style == "mesh":
        pal = c.palette(spec.get("color"), "sunset")
        cv.mesh(x, y, w, h, 36, pal, c.index)
        labels = as_lines(spec.get("label"))[:2]
        base = y + h - 34 - 24 * len(labels)
        size = min(150, (base - y - 26) / 0.76)
        size = metrics.fit(val, w - 44, size, 800, -0.06)
        cv.text(x + 22, base, val, size, pal["ink"], 800, -0.06)
        for i, ln in enumerate(labels):
            cv.fitted(x + 26, y + h - 12 - (len(labels) - 1 - i) * 24, w - 52, 19, ln, pal["ink"], 700, -0.01)
    elif style == "outline":
        pal = c.palette(spec.get("color"), "aurora")
        cv.mesh(x, y, w, h, 36, pal, c.index, gloss=0.28)
        cv.uses_outline_font = True
        if spec.get("eyebrow"):
            cv.label(x + 26, y + 46, spec["eyebrow"], pal["ink"])
        n = max(1, len(val))
        size = 270 if n <= 3 else 215
        tl = min(w - 26, n * 124)
        cv.add(
            f'<text x="{x + 14}" y="{y + h - 164}" font-family="SoraOutline,Sora,sans-serif" font-size="{size}" '
            f'font-weight="200" fill="none" stroke="{pal["ink"]}" stroke-width="5" stroke-linejoin="round" '
            f'letter-spacing="-0.05em" textLength="{tl}" lengthAdjust="spacingAndGlyphs">{clean(val)}</text>'
        )
        cv.fitted(x + 26, y + h - 66, w - 52, 30, spec.get("label", ""), pal["ink"], 800, -0.03)
        if spec.get("caption"):
            cv.fitted(x + 28, y + h - 34, w - 52, 18, spec["caption"], pal["ink"], 600, 0)
    else:  # plain
        cv.card(x, y, w, h, 36, strong=True)
        cv.label(x + 24, y + 42, spec.get("label", ""))
        minis = spec.get("minis") or []
        accent = cv.gradient(spec.get("accent", "blue"))
        if minis:
            size = metrics.fit(val, w - 44, 88, 800, -0.05)
            cv.text(x + 22, y + h - 110, val, size, accent, 800, -0.05)
            cv.add(
                f'<line x1="{x + 24}" y1="{y + h - 84}" x2="{x + w - 24}" y2="{y + h - 84}" '
                f'stroke="{t["stroke"]}" stroke-opacity="{t["divider_opacity"]}"/>'
            )
            colw = (w - 48) / len(minis)
            for i, m in enumerate(minis):
                src = m if isinstance(m, str) else m.get("source")
                mval = compact(c.stats.get(src, 0)) if src else str(m.get("value", ""))
                mlabel = (m.get("label") if isinstance(m, dict) else None) or SOURCE_LABELS.get(src, src or "")
                mx = x + 24 + i * colw
                cv.fitted(mx, y + h - 44, colw - 6, 26, mval, t["text"], 800, -0.03)
                cv.fitted(mx, y + h - 22, colw - 6, 14, mlabel, t["muted"], 600, 0.02)
        else:
            size = metrics.fit(val, w - 44, 110, 800, -0.05)
            cv.text(x + 22, y + h - 40, val, size, accent, 800, -0.05)


# ------------------------------------------------------------------------- streak
def streak(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    cv.card(x, y, w, h)
    cv.label(x + 24, y + 42, spec.get("label", "current streak"))
    st = str(c.stats.get("streak", 0))
    cv.text(x + 22, y + 128, st, 92, t["text"], 800, -0.05)
    unit_x = x + 22 + metrics.width(st, 92, 800, -0.05) + 8
    cv.text(unit_x, y + 128, spec.get("unit", "days"), 24, t["muted"], 700, -0.01)
    last = ([0] * 20 + list(c.stats.get("last20", [])))[-20:]
    gap = 3.6
    bw = (w - 48 - 19 * gap) / 20
    seg = cv.gradient(spec.get("accent", "seg"))
    for i, n in enumerate(last):
        bx = x + 24 + i * (bw + gap)
        cv.add(f'<rect x="{bx:.1f}" y="{y + 154}" width="{bw:.1f}" height="38" rx="4" fill="{seg if n else t["off"]}"/>')
    cv.label(x + 24, y + 218, "last 20 days")


# --------------------------------------------------------------------------- now
def commit(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    cv.uses_pulse = True
    cv.card(x, y, w, h, 116, strong=True)
    now = c.stats.get("now") or {"repo": "", "message": "no recent public commits", "when": ""}
    cv.add(f'<circle class="pulse" cx="{x + 60}" cy="{y + 66}" r="6" fill="#30d158"/>')
    cv.label(x + 76, y + 71, spec.get("label", "now · last commit"))
    text_w = w - 52 - h - 20
    lines = metrics.wrap(str(now["message"]).lower(), text_w, 26, 700, -0.03, 2)
    for i, ln in enumerate(lines):
        cv.text(x + 52, y + 118 + i * 34, ln, 26, t["text"], 700, -0.03)
    sub = " · ".join(p for p in (now["repo"], now["when"]) if p)
    if sub:
        cv.fitted(x + 52, y + 118 + len(lines) * 34 + 12, text_w, 15, sub, t["muted"], 600, 0)
    cx, cy = x + w - h / 2, y + h / 2
    rg = cv.uid("rg")
    cv.defs.append(
        f'<radialGradient id="{rg}" cx=".3" cy=".25" r=".9"><stop offset="0" stop-color="#ffd60a"/>'
        '<stop offset=".45" stop-color="#ff2d92"/><stop offset=".8" stop-color="#5e5ce6"/>'
        '<stop offset="1" stop-color="#64d2ff"/></radialGradient>'
    )
    cv.add(f'<circle cx="{cx}" cy="{cy}" r="84" fill="url(#{rg})"/>')
    cv.add(f'<circle cx="{cx}" cy="{cy}" r="83" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>')
    cv.add(
        f'<path d="M{cx - 14} {cy - 26} L{cx - 42} {cy} L{cx - 14} {cy + 26} M{cx + 14} {cy - 26} L{cx + 42} {cy} '
        f'L{cx + 14} {cy + 26} M{cx + 8} {cy - 34} L{cx - 8} {cy + 34}" fill="none" stroke="#fff" stroke-width="9" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


# ------------------------------------------------------------------------- status
def status(c, spec, x, y, w, h):
    cv = c.cv
    pal = c.palette(spec.get("color"), "meadow")
    cv.mesh(x, y, w, h, 36, pal, c.index)
    on = spec.get("on", True)
    knob = x + 67 if on else x + 41
    cv.add(
        f'<rect x="{x + 24}" y="{y + 24}" width="60" height="34" rx="17" fill="#000" fill-opacity=".88"/>'
        f'<circle cx="{knob}" cy="{y + 41}" r="13" fill="#fff"/>'
    )
    word = str(spec.get("word", "on" if on else "off"))
    size = metrics.fit(word, w - 40, min(124, h * 0.53), 800, -0.06)
    cv.text(x + 20, y + h - 66, word, size, pal["ink"], 800, -0.06)
    if spec.get("caption"):
        cv.fitted(x + 24, y + h - 24, w - 48, 17, spec["caption"], pal["ink"], 700, -0.01)


# --------------------------------------------------------------------------- stack
def _chip_items(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            name, col = str(it.get("name", "")), it.get("color")
        else:
            name, col = str(it), None
        out.append((name, col or TECH_COLORS.get(name.lower(), FALLBACK_DOT)))
    return out


def stack(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    cv.card(x, y, w, h)
    cv.label(x + 24, y + 42, spec.get("label", "stack"))
    items = _chip_items(spec.get("items", []))
    max_name = w - 48 - 40
    items = [(metrics.wrap(n, max_name, 14, 600, 0, 1)[0] if n else n, col) for n, col in items]
    left, right, bottom = x + 24, x + w - 14, y + h - 14

    def layout(chips):
        placed, cx, cy = [], left, y + 62
        for name, col in chips:
            cw = metrics.width(name, 14, 600) + 40
            if cx + cw > right and cx > left:
                cx, cy = left, cy + 50
            if cy + 38 > bottom:
                return placed, False
            placed.append((cx, cy, cw, name, col))
            cx += cw + 8
        return placed, True

    placed, ok = layout(items)
    if not ok:  # not everything fits: drop chips from the end until "+n" fits
        k = len(placed)
        while k >= 0:
            extra = [(f"+{len(items) - k}", FALLBACK_DOT)]
            placed2, ok2 = layout(items[:k] + extra)
            if ok2:
                placed = placed2
                break
            k -= 1
    for cx, cy, cw, name, col in placed:
        cv.add(
            f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="38" rx="19" fill="{t["chip"]}" '
            f'fill-opacity="{t["chip_opacity"]}"/><circle cx="{cx + 20:.1f}" cy="{cy + 19}" r="6" fill="{col}"/>'
        )
        cv.text(cx + 33, cy + 24.5, name, 14, t["text"], 600, 0)


# ---------------------------------------------------------------------- languages
def languages(c, spec, x, y, w, h):
    cv, t = c.cv, c.t
    cv.card(x, y, w, h)
    cv.label(x + 24, y + 42, spec.get("label", "top languages"))
    langs = [(n, float(p)) for n, p in c.stats.get("languages", [])]
    n_rows = max(1, min(int(spec.get("limit", 8)), int((h - 104 - 18) / 28) + 1))
    shown = langs[:n_rows]
    bx, by, bw = x + 24, y + 62, w - 48
    clip = cv.uid("c")
    cv.defs.append(f'<clipPath id="{clip}"><rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath>')
    cv.add(f'<g clip-path="url(#{clip})"><rect x="{bx}" y="{by}" width="{bw}" height="14" fill="{t["off"]}"/>')
    cur = bx
    for name, pct in shown:
        seg = bw * pct / 100
        col = TECH_COLORS.get(name.lower(), FALLBACK_DOT)
        cv.add(f'<rect x="{cur:.1f}" y="{by}" width="{max(seg - 2, 0):.1f}" height="14" fill="{col}"/>')
        cur += seg
    cv.add("</g>")
    for i, (name, pct) in enumerate(shown):
        ry = y + 104 + i * 28
        cv.add(f'<circle cx="{x + 29}" cy="{ry - 5}" r="5" fill="{TECH_COLORS.get(name.lower(), FALLBACK_DOT)}"/>')
        cv.fitted(x + 44, ry, w - 44 - 80, 15, name.lower(), t["text"], 600, 0)
        cv.text(x + w - 24, ry, f"{pct:.0f}%" if pct >= 1 else "<1%", 15, t["muted"], 600, 0, anchor="end")


# ---------------------------------------------------------------------------- cta
def cta(c, spec, x, y, w, h):
    cv = c.cv
    pal = c.palette(spec.get("color"), "lime")
    cv.mesh(x, y, w, h, 116, pal, c.index, 0.28)
    tw = w - 56 - 160
    size = metrics.fit(str(spec.get("text", "")), tw, 58, 800, -0.04)
    cv.text(x + 56, y + 134, spec.get("text", ""), size, pal["ink"], 800, -0.04)
    if spec.get("caption"):
        cv.fitted(x + 58, y + 176, tw, 17, spec["caption"], pal["ink"], 600, -0.01)
    cx, cy = x + w - 116, y + h / 2
    cv.add(f'<circle cx="{cx}" cy="{cy}" r="64" fill="#fff"/>')
    cv.add(
        f'<path d="M{cx - 26} {cy} H{cx + 24} M{cx + 6} {cy - 20} L{cx + 26} {cy} L{cx + 6} {cy + 20}" fill="none" '
        f'stroke="#0b0b0c" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# --------------------------------------------------------------------------- band
def band(c, spec, x, y, w, h):
    cv = c.cv
    pal = c.palette(spec.get("color"), "candy")
    cv.mesh(x, y, w, h, 44, pal, c.index, 0.4)
    upd = f'{spec.get("updated_label", "updated")} {c.stats.get("updated", "")}' if spec.get("show_updated", True) else ""
    upd_w = metrics.width(upd, 19, 700) + 60 if upd else 0
    size = min(84, h * 0.62)
    cv.fitted(x + 40, y + h / 2 + size * 0.34, w - 80 - upd_w, size, spec.get("text", ""), pal["ink"], 800, -0.05)
    if upd:
        cv.text(x + w - 40, y + h / 2 + 7, upd, 19, pal["ink"], 700, 0, anchor="end")


# ------------------------------------------------------------------------ registry
class CardType:
    def __init__(self, fn, size, keys, cols, rows):
        self.fn, self.default_size, self.cols, self.rows = fn, size, cols, rows
        self.keys = {"type", "size", "color"} | set(keys)


CARDS = {
    "hero": CardType(hero, "2x2", {"title", "subtitle", "intro", "headline", "accent"}, (2, 4), (1, 2)),
    "number": CardType(
        number, "1x1",
        {"value", "source", "label", "caption", "eyebrow", "style", "minis", "accent"}, (1, 2), (1, 2),
    ),
    "streak": CardType(streak, "1x1", {"label", "unit", "accent"}, (1, 2), (1,)),
    "commit": CardType(commit, "2x1", {"label"}, (2, 4), (1,)),
    "status": CardType(status, "1x1", {"word", "caption", "on"}, (1, 2), (1, 2)),
    "stack": CardType(stack, "1x1", {"label", "items"}, (1, 4), (1, 2)),
    "languages": CardType(languages, "1x1", {"label", "limit"}, (1, 4), (1, 2)),
    "cta": CardType(cta, "2x1", {"text", "caption"}, (2, 4), (1,)),
    "band": CardType(band, "4x0.5", {"text", "show_updated", "updated_label"}, (2, 4), (0.5, 1)),
}


def render(c, spec, rect):
    CARDS[spec["type"]].fn(c, spec, *rect)


assert UNIT_H == 108  # card height maths above assumes a 232px full row
