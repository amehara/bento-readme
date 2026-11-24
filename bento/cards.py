"""Card renderers. Each card type declares its keys, default size and allowed sizes."""
from . import metrics
from .colors import average, ink_for, luminance, mix, norm
from .palettes import FALLBACK_DOT, TECH_COLORS
from .svg import clean

SOURCES = ("contributions", "streak", "repos", "stars", "followers", "lines")
SOURCE_LABELS = {
    "contributions": "contributions", "streak": "streak", "repos": "repos",
    "stars": "stars", "followers": "followers", "lines": "lines of code",
}
PATTERNS = ("dots", "grid", "lines", "grain")


class Look:
    """Text colours that stay readable on whatever surface a card ended up with."""

    def __init__(self, text, soft, muted, off, chip, chip_op, divider_op, stroke, rep):
        self.text, self.soft, self.muted, self.off = text, soft, muted, off
        self.chip, self.chip_op, self.divider_op, self.stroke, self.rep = chip, chip_op, divider_op, stroke, rep

    @classmethod
    def from_theme(cls, t, rep):
        return cls(t["text"], t["text_soft"], t["muted"], t["off"], t["chip"], t["chip_opacity"],
                   t["divider_opacity"], t["stroke"], rep)

    @classmethod
    def from_ink(cls, ink, rep):
        dark_ink = luminance(ink) < 0.5
        return cls(ink, mix(ink, rep, 0.12), mix(ink, rep, 0.42), mix(rep, ink, 0.2), ink,
                   0.07 if dark_ink else 0.14, 0.12 if dark_ink else 0.16, ink, rep)


class Ctx:
    """Everything a card needs besides its own config."""

    def __init__(self, canvas, theme, stats, palettes, index, spec):
        self.cv, self.t, self.stats, self.palettes, self.index, self.spec = canvas, theme, stats, palettes, index, spec

    def accent(self, default):
        return self.cv.paint(self.spec.get("accent", default))

    def surface(self, rect, base_r=36, mesh=None, strong=False, gloss=0.28):
        """Draws the card background (honouring bg/fg/radius/border/pattern) and returns a Look."""
        x, y, w, h = rect
        cv, t, st, spec = self.cv, self.t, self.cv.style, self.spec
        r = cv.radius(base_r, w, h, spec.get("radius"))
        bg = spec.get("bg", spec.get("color"))
        if bg is None:
            bg = mesh
        cv.shadow(x, y, w, h, r)
        theme_gloss = t["gloss"] * st["gloss"]
        if bg is None:
            fill = t["card_strong"] if strong else t["card"]
            cv.solid(x, y, w, h, r, fill, theme_gloss)
            look, border = Look.from_theme(t, fill), (t["stroke"], t["stroke_opacity"])
        elif isinstance(bg, list):
            stops = cv.stops_for(bg)
            rep = average([c for _, c in stops])
            cv.linear(x, y, w, h, r, stops, spec.get("bg_angle", 135), theme_gloss)
            look, border = Look.from_ink(ink_for(rep), rep), (ink_for(rep), 0.12)
        elif bg in self.palettes:
            pal = self.palettes[bg]
            cv.mesh(x, y, w, h, r, pal, self.index, gloss * st["gloss"])
            look, border = Look.from_ink(pal["ink"], pal["base"]), ("#ffffff", 0.35)
        else:
            cv.solid(x, y, w, h, r, bg, theme_gloss)
            look, border = Look.from_ink(ink_for(bg), bg), (ink_for(bg), 0.12)
        fg = spec.get("fg")
        if fg:
            look = Look(fg, mix(fg, look.rep, 0.12), mix(fg, look.rep, 0.42), look.off, fg, look.chip_op,
                        look.divider_op, fg, look.rep)
        # border: card override > global style > theme/palette default
        b = spec.get("border", st["border"])
        if b is not False and b != "none":
            color = norm(b) if isinstance(b, str) else border[0]
            opacity = st["border_opacity"] if st["border_opacity"] is not None else border[1]
            if isinstance(b, str):
                opacity = 1.0 if st["border_opacity"] is None else st["border_opacity"]
            cv.border(x, y, w, h, r, color, opacity, st["border_width"])
        pat = spec.get("pattern", st["pattern"])
        if pat and pat != "none":
            op = spec.get("pattern_opacity", st["pattern_opacity"])
            cv.pattern(pat, x, y, w, h, r, look.text, op)
        return look


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


def label(c, L, x, y, s):
    c.cv.text(x, y, s, 14, L.muted, 600, 0.02)


# --------------------------------------------------------------------------- hero
def hero(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h), 44, strong=True)
    pad = 36
    inner = w - pad * 2
    cv.fitted(x + pad, y + 70, inner, 34, spec.get("title", ""), L.text, 800, -0.03)
    if spec.get("subtitle"):
        cv.fitted(x + pad, y + 102, inner, 17, spec["subtitle"], L.muted, 600, 0)
    intro = as_lines(spec.get("intro"))[:2]
    headline = as_lines(spec.get("headline"))[:2]
    full = h >= 330 and headline
    for i, ln in enumerate(intro):
        cv.fitted(x + pad, y + 148 + i * 28, inner, 21, ln, L.soft, 500, -0.01)
    if full:
        accent = c.accent("pink")
        cap = h * 0.34
        lines = list(reversed(headline))  # drawn bottom-up
        sizes = [metrics.fill(ln, w - 64, 800, -0.05, max_size=cap) for ln in lines]
        # keep clear of the intro text: shrink the whole block if it would climb into it
        top_limit = y + (140 + 28 * len(intro) if intro else 124)
        extent = sum(s * 0.865 for s in sizes[:-1]) + sizes[-1] * 0.74
        room = (y + h - 30) - top_limit
        if extent > room:
            sizes = [s * room / extent for s in sizes]
        bottom = y + h - 30
        for i, (ln, size) in enumerate(zip(lines, sizes)):
            cv.text(x + 32, bottom, ln, size, accent if i == 0 else L.text, 800, -0.05, exact=True)
            bottom -= size * 0.865


# ------------------------------------------------------------------------- number
def number(c, spec, x, y, w, h):
    cv = c.cv
    style = spec.get("style", "mesh")
    val = value_of(spec, c.stats)
    if style == "mesh":
        L = c.surface((x, y, w, h), 36, mesh="sunset")
        labels = as_lines(spec.get("label"))[:2]
        base = y + h - 34 - 24 * len(labels)
        size = min(150, (base - y - 26) / 0.76)
        size = metrics.fit(val, w - 44, size, 800, -0.06)
        cv.text(x + 22, base, val, size, L.text, 800, -0.06, exact=True)
        for i, ln in enumerate(labels):
            cv.fitted(x + 26, y + h - 12 - (len(labels) - 1 - i) * 24, w - 52, 19, ln, L.text, 700, -0.01)
    elif style == "outline":
        L = c.surface((x, y, w, h), 36, mesh="aurora")
        cv.uses_outline_font = True
        if spec.get("eyebrow"):
            cv.text(x + 26, y + 46, spec["eyebrow"], 14, L.text, 600, 0.02)
        n = max(1, len(val))
        size = 270 if n <= 3 else 215
        tl = min(w - 26, n * 124)
        cv.add(
            f'<text x="{x + 14}" y="{y + h - 164}" font-family="{cv.outline_family}" font-size="{size}" '
            f'font-weight="200" fill="none" stroke="{L.text}" stroke-width="5" stroke-linejoin="round" '
            f'letter-spacing="-0.05em" textLength="{tl}" lengthAdjust="spacingAndGlyphs">{clean(val)}</text>'
        )
        cv.fitted(x + 26, y + h - 66, w - 52, 30, spec.get("label", ""), L.text, 800, -0.03)
        if spec.get("caption"):
            cv.fitted(x + 28, y + h - 34, w - 52, 18, spec["caption"], L.text, 600, 0)
    else:  # plain
        L = c.surface((x, y, w, h), 36, strong=True)
        label(c, L, x + 24, y + 42, spec.get("label", ""))
        minis = spec.get("minis") or []
        accent = c.accent("blue")
        if minis:
            size = metrics.fit(val, w - 44, 88, 800, -0.05)
            cv.text(x + 22, y + h - 110, val, size, accent, 800, -0.05)
            cv.add(
                f'<line x1="{x + 24}" y1="{y + h - 84}" x2="{x + w - 24}" y2="{y + h - 84}" '
                f'stroke="{L.stroke}" stroke-opacity="{L.divider_op}"/>'
            )
            colw = (w - 48) / len(minis)
            for i, m in enumerate(minis):
                src = m if isinstance(m, str) else m.get("source")
                mval = compact(c.stats.get(src, 0)) if src else str(m.get("value", ""))
                mlabel = (m.get("label") if isinstance(m, dict) else None) or SOURCE_LABELS.get(src, src or "")
                mx = x + 24 + i * colw
                cv.fitted(mx, y + h - 44, colw - 6, 26, mval, L.text, 800, -0.03)
                cv.fitted(mx, y + h - 22, colw - 6, 14, mlabel, L.muted, 600, 0.02)
        else:
            size = metrics.fit(val, w - 44, 110, 800, -0.05)
            cv.text(x + 22, y + h - 40, val, size, accent, 800, -0.05)


# ------------------------------------------------------------------------- streak
def streak(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "current streak"))
    st = str(c.stats.get("streak", 0))
    cv.text(x + 22, y + 128, st, 92, L.text, 800, -0.05)
    unit_x = x + 22 + metrics.width(st, 92, 800, -0.05) + 8
    cv.text(unit_x, y + 128, spec.get("unit", "days"), 24, L.muted, 700, -0.01)
    last = ([0] * 20 + list(c.stats.get("last20", [])))[-20:]
    gap = 3.6
    bw = (w - 48 - 19 * gap) / 20
    seg = c.accent("seg")
    for i, n in enumerate(last):
        bx = x + 24 + i * (bw + gap)
        cv.add(f'<rect x="{bx:.1f}" y="{y + 154}" width="{bw:.1f}" height="38" rx="{min(4, bw / 2):.1f}" fill="{seg if n else L.off}"/>')
    label(c, L, x + 24, y + 218, "last 20 days")


# --------------------------------------------------------------------------- now
def commit(c, spec, x, y, w, h):
    cv = c.cv
    cv.uses_pulse = True
    L = c.surface((x, y, w, h), 116, strong=True)
    now = c.stats.get("now") or {"repo": "", "message": "no recent public commits", "when": ""}
    cv.add(f'<circle class="pulse" cx="{x + 60}" cy="{y + 66}" r="6" fill="#30d158"/>')
    label(c, L, x + 76, y + 71, spec.get("label", "now · last commit"))
    text_w = w - 52 - h - 20
    lines = metrics.wrap(str(now["message"]), text_w, 26, 700, -0.03, 2)
    for i, ln in enumerate(lines):
        cv.text(x + 52, y + 118 + i * 34, ln, 26, L.text, 700, -0.03)
    sub = " · ".join(p for p in (now["repo"], now["when"]) if p)
    if sub:
        cv.fitted(x + 52, y + 118 + len(lines) * 34 + 12, text_w, 15, sub, L.muted, 600, 0)
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
    L = c.surface((x, y, w, h), 36, mesh="meadow")
    on = spec.get("on", True)
    knob_x = x + 67 if on else x + 41
    cv.add(
        f'<rect x="{x + 24}" y="{y + 24}" width="60" height="34" rx="17" fill="{L.text}" fill-opacity=".88"/>'
        f'<circle cx="{knob_x}" cy="{y + 41}" r="13" fill="{ink_for(L.text)}"/>'
    )
    word = str(spec.get("word", "on" if on else "off"))
    size = metrics.fit(word, w - 40, min(124, h * 0.53), 800, -0.06)
    cv.text(x + 20, y + h - 66, word, size, L.text, 800, -0.06, exact=True)
    if spec.get("caption"):
        cv.fitted(x + 24, y + h - 24, w - 48, 17, spec["caption"], L.text, 700, -0.01)


# --------------------------------------------------------------------------- stack
def _chip_items(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            name, col = str(it.get("name", "")), norm(it.get("color"))
        else:
            name, col = str(it), None
        out.append((name, col or TECH_COLORS.get(name.lower(), FALLBACK_DOT)))
    return out


def stack(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "stack"))
    chip_style = spec.get("chip_style", "dot")
    items = _chip_items(spec.get("items", []))
    pad_l = 14 if chip_style == "filled" else 40
    max_name = w - 48 - pad_l - 14
    items = [(metrics.wrap(n, max_name, 14, 600, 0, 1)[0] if n else n, col) for n, col in items]
    left, right, bottom = x + 24, x + w - 14, y + h - 14

    def layout(chips):
        placed, cx, cy = [], left, y + 62
        for name, col in chips:
            cw = metrics.width(name, 14, 600) + pad_l + 14 if chip_style == "filled" else metrics.width(name, 14, 600) + 40
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
            placed2, ok2 = layout(items[:k] + [(f"+{len(items) - k}", FALLBACK_DOT)])
            if ok2:
                placed = placed2
                break
            k -= 1
    for cx, cy, cw, name, col in placed:
        if chip_style == "filled":
            cv.add(f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="38" rx="19" fill="{col}" fill-opacity=".22"/>')
            cv.text(cx + 14, cy + 24.5, name, 14, L.text, 600, 0)
            continue
        if chip_style == "outline":
            cv.add(f'<rect x="{cx + .5:.1f}" y="{cy + .5}" width="{cw - 1:.1f}" height="37" rx="18.5" fill="none" stroke="{col}" stroke-opacity=".8"/>')
        else:
            cv.add(f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="38" rx="19" fill="{L.chip}" fill-opacity="{L.chip_op}"/>')
        cv.add(f'<circle cx="{cx + 20:.1f}" cy="{cy + 19}" r="6" fill="{col}"/>')
        cv.text(cx + 33, cy + 24.5, name, 14, L.text, 600, 0)


# ---------------------------------------------------------------------- languages
def languages(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "top languages"))
    langs = [(n, float(p)) for n, p in c.stats.get("languages", [])]
    n_rows = max(1, min(int(spec.get("limit", 8)), int((h - 104 - 18) / 28) + 1))
    shown = langs[:n_rows]
    bx, by, bw = x + 24, y + 62, w - 48
    clip = cv.uid("c")
    cv.defs.append(f'<clipPath id="{clip}"><rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath>')
    cv.add(f'<g clip-path="url(#{clip})"><rect x="{bx}" y="{by}" width="{bw}" height="14" fill="{L.off}"/>')
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
        cv.fitted(x + 44, ry, w - 44 - 80, 15, name, L.text, 600, 0)
        cv.text(x + w - 24, ry, f"{pct:.0f}%" if pct >= 1 else "<1%", 15, L.muted, 600, 0, anchor="end")


# ---------------------------------------------------------------------------- cta
def cta(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h), 116, mesh="lime")
    tw = w - 56 - 160
    size = metrics.fit(str(spec.get("text", "")), tw, 58, 800, -0.04)
    cv.text(x + 56, y + 134, spec.get("text", ""), size, L.text, 800, -0.04, exact=True)
    if spec.get("caption"):
        cv.fitted(x + 58, y + 176, tw, 17, spec["caption"], L.text, 600, -0.01)
    cx, cy = x + w - 116, y + h / 2
    cv.add(f'<circle cx="{cx}" cy="{cy}" r="64" fill="#fff"/>')
    cv.add(
        f'<path d="M{cx - 26} {cy} H{cx + 24} M{cx + 6} {cy - 20} L{cx + 26} {cy} L{cx + 6} {cy + 20}" fill="none" '
        f'stroke="#0b0b0c" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# --------------------------------------------------------------------------- band
def band(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h), 44, mesh="candy", gloss=0.4)
    upd = f'{spec.get("updated_label", "updated")} {c.stats.get("updated", "")}' if spec.get("show_updated", True) else ""
    upd_w = metrics.width(upd, 19, 700) + 60 if upd else 0
    size = min(84, h * 0.62)
    cv.fitted(x + 40, y + h / 2 + size * 0.34, w - 80 - upd_w, size, spec.get("text", ""), L.text, 800, -0.05)
    if upd:
        cv.text(x + w - 40, y + h / 2 + 7, upd, 19, L.text, 700, 0, anchor="end")


# ---------------------------------------------------------------------------- text
def text_card(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    quote = spec.get("style") == "quote"
    top = y + 40
    if spec.get("title"):
        cv.fitted(x + 26, y + 46, w - 52, 22, spec["title"], L.text, 800, -0.02)
        top = y + 82
    size = 24 if quote else 16
    weight = 700 if quote else 500
    step = size * 1.5
    foot = 34 if spec.get("author") else 22
    n = max(1, int((y + h - foot - top) // step) + 1)
    lines = metrics.wrap(str(spec.get("body", "")), w - 52, size, weight, -0.01 if quote else 0, n)
    for i, ln in enumerate(lines):
        cv.text(x + 26, top + size * 0.8 + i * step, ln, size, L.text if quote else L.soft, weight, -0.01 if quote else 0)
    if spec.get("author"):
        cv.fitted(x + 26, y + h - 22, w - 52, 14, spec["author"], L.muted, 600, 0.02)


# --------------------------------------------------------------------------- image
def image(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    mime, data = spec["_image"]
    r = cv.radius(36, w, h, spec.get("radius"))
    href = f"data:{mime};base64,{data}"
    if spec.get("fit", "cover") == "cover":
        clip = cv.uid("c")
        cv.defs.append(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
        cv.add(
            f'<image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clip})"/>'
        )
    else:
        cv.add(f'<image href="{href}" x="{x + 18}" y="{y + 18}" width="{w - 36}" height="{h - 36}" preserveAspectRatio="xMidYMid meet"/>')
    if spec.get("caption"):
        g = cv.uid("g")
        cv.defs.append(
            f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".62"/></linearGradient>'
        )
        clip = cv.uid("c")
        cv.defs.append(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
        cv.add(f'<g clip-path="url(#{clip})"><rect x="{x}" y="{y + h - 90}" width="{w}" height="90" fill="url(#{g})"/></g>')
        cv.fitted(x + 24, y + h - 24, w - 48, 17, spec["caption"], "#ffffff", 700, -0.01)


# ------------------------------------------------------------------------ contact
def _pairs(items, a="label", b="value"):
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append((str(it.get(a, "")), str(it.get(b, ""))))
        else:
            left, _, right = str(it).partition(":")
            out.append((left.strip(), right.strip()))
    return out


def contact(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "find me"))
    rows = _pairs(spec.get("items"))
    n = max(1, int((h - 84 - 14) // 36) + 1)
    for i, (k, v) in enumerate(rows[:n]):
        ry = y + 84 + i * 36
        cv.fitted(x + 24, ry, (w - 48) * 0.36, 14, k, L.muted, 600, 0.02)
        cv.fitted(x + w - 24, ry, (w - 48) * 0.62, 17, v, L.text, 700, -0.01, anchor="end")


# ------------------------------------------------------------------------ heatmap
def heatmap(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "contributions"))
    cal = [wk for wk in (c.stats.get("calendar") or [])]
    avail = w - 48
    if spec.get("weeks"):
        n = min(53, int(spec["weeks"]))
        pitch = min(22.0, avail / n)
    else:
        pitch = 17.0
        n = min(53, int(avail // pitch))
    cell = pitch - 3
    weeks = cal[-n:]
    mx = max([max(wk) for wk in weeks if wk] or [0]) or 1
    col = cv.first_color(spec.get("accent", "green"))
    levels = [L.off] + [mix(L.off, col, f) for f in (0.35, 0.6, 0.8, 1.0)]
    for wi, wk in enumerate(weeks):
        for di, cnt in enumerate(wk[:7]):
            if cnt is None:
                continue
            ratio = cnt / mx
            lv = 0 if cnt <= 0 else 1 if ratio <= 0.25 else 2 if ratio <= 0.5 else 3 if ratio <= 0.75 else 4
            cv.add(
                f'<rect x="{x + 24 + wi * pitch:.1f}" y="{y + 62 + di * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                f'rx="{min(4, cell / 3):.1f}" fill="{levels[lv]}"/>'
            )
    total = sum(sum(v for v in wk if v) for wk in weeks)
    cv.text(x + 24, y + h - 16, f"{compact(total)} in the last {len(weeks)} weeks", 14, L.muted, 600, 0.02)


# -------------------------------------------------------------------------- repos
def repos(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "top repos · stars"))
    rows = c.stats.get("top_repos") or []
    n = max(1, min(int(spec.get("limit", 8)), int((h - 84 - 14) // 34) + 1))
    for i, rp in enumerate(rows[:n]):
        ry = y + 86 + i * 34
        col = TECH_COLORS.get(str(rp.get("language") or "").lower(), FALLBACK_DOT)
        cv.add(f'<circle cx="{x + 29}" cy="{ry - 5}" r="5" fill="{col}"/>')
        count = compact(rp.get("stars", 0))
        cv.fitted(x + 44, ry, w - 44 - 24 - metrics.width(count, 14, 600) - 10, 16, rp.get("name", ""), L.text, 700, -0.01)
        cv.text(x + w - 24, ry, count, 14, L.muted, 600, 0, anchor="end")


# --------------------------------------------------------------------------- bars
def bars(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    label(c, L, x + 24, y + 42, spec.get("label", "skills"))
    rows = []
    for k, v in _pairs(spec.get("items"), "name", "value"):
        try:
            rows.append((k, max(0.0, min(100.0, float(v)))))
        except ValueError:
            rows.append((k, 0.0))
    n = max(1, int((h - 62 - 8) // 40))
    accent = c.accent("seg")
    bw = w - 48
    for i, (k, v) in enumerate(rows[:n]):
        ry = y + 78 + i * 40
        cv.fitted(x + 24, ry, bw - 50, 15, k, L.text, 600, 0)
        cv.text(x + w - 24, ry, f"{v:.0f}", 14, L.muted, 600, 0, anchor="end")
        cv.add(f'<rect x="{x + 24}" y="{ry + 10}" width="{bw}" height="8" rx="4" fill="{L.off}"/>')
        if v:
            cv.add(f'<rect x="{x + 24}" y="{ry + 10}" width="{max(8, bw * v / 100):.1f}" height="8" rx="4" fill="{accent}"/>')


# --------------------------------------------------------------------------- ring
def ring(c, spec, x, y, w, h):
    cv = c.cv
    L = c.surface((x, y, w, h))
    v = max(0.0, min(100.0, float(spec.get("value", 0))))
    cx, cy, r = x + w / 2, y + 96, 58
    accent = c.accent("seg")
    cv.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{L.off}" stroke-width="14"/>')
    if v:
        cv.add(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-width="14" stroke-linecap="round" '
            f'pathLength="100" stroke-dasharray="{v:.1f} 100" transform="rotate(-90 {cx} {cy})"/>'
        )
    cv.text(cx, cy + 14, f"{v:.0f}%", 38, L.text, 800, -0.04, anchor="middle")
    if spec.get("label"):
        cv.fitted(cx, y + h - 34, w - 40, 17, spec["label"], L.text, 700, -0.01, anchor="middle")
    if spec.get("caption"):
        cv.fitted(cx, y + h - 14, w - 40, 13, spec["caption"], L.muted, 600, 0.02, anchor="middle")


# ------------------------------------------------------------------------ registry
COMMON = {"type", "size", "color", "bg", "bg_angle", "fg", "radius", "border", "pattern", "pattern_opacity"}


class CardType:
    def __init__(self, fn, size, keys, cols, rows):
        self.fn, self.default_size, self.cols, self.rows = fn, size, cols, rows
        self.keys = COMMON | set(keys)


CARDS = {
    "hero": CardType(hero, "2x2", {"title", "subtitle", "intro", "headline", "accent"}, (2, 4), (1, 2)),
    "number": CardType(
        number, "1x1", {"value", "source", "label", "caption", "eyebrow", "style", "minis", "accent"}, (1, 2), (1, 2)
    ),
    "streak": CardType(streak, "1x1", {"label", "unit", "accent"}, (1, 2), (1,)),
    "commit": CardType(commit, "2x1", {"label"}, (2, 4), (1,)),
    "status": CardType(status, "1x1", {"word", "caption", "on"}, (1, 2), (1, 2)),
    "stack": CardType(stack, "1x1", {"label", "items", "chip_style"}, (1, 4), (1, 2)),
    "languages": CardType(languages, "1x1", {"label", "limit"}, (1, 4), (1, 2)),
    "cta": CardType(cta, "2x1", {"text", "caption"}, (2, 4), (1,)),
    "band": CardType(band, "4x0.5", {"text", "show_updated", "updated_label"}, (2, 4), (0.5, 1)),
    "text": CardType(text_card, "2x1", {"title", "body", "author", "style"}, (1, 4), (1, 2)),
    "image": CardType(image, "1x1", {"src", "fit", "caption"}, (1, 4), (1, 2)),
    "contact": CardType(contact, "1x1", {"label", "items"}, (1, 2), (1, 2)),
    "heatmap": CardType(heatmap, "2x1", {"label", "weeks", "accent"}, (1, 4), (1,)),
    "repos": CardType(repos, "1x1", {"label", "limit"}, (1, 2), (1, 2)),
    "bars": CardType(bars, "1x1", {"label", "items", "accent"}, (1, 2), (1, 2)),
    "ring": CardType(ring, "1x1", {"value", "label", "caption", "accent"}, (1, 2), (1, 2)),
}
