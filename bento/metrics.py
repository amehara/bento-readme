"""Text measuring, fitting and wrapping using the bundled Sora font advances."""
import json
import os

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
with open(os.path.join(_DATA, "metrics.json"), encoding="utf-8") as _f:
    _M = json.load(_f)

_WEIGHTS = sorted(int(w) for w in _M["sora"])
_FALLBACK_ADV = 0.62  # chars the font does not have are drawn by a system font

# Other fonts are not embedded, so we only approximate their width relative to Sora (which is wide).
FONT_SCALE = {"sora": 1.0, "system": 0.93, "serif": 0.88, "mono": None}
# Estimated widths of fonts we do not embed can be off by a few percent: keep a safety margin.
FONT_MARGIN = {"sora": 1.0, "system": 0.94, "serif": 0.94, "mono": 0.98}
_font = "sora"


def set_font(name):
    global _font
    _font = name if name in FONT_SCALE else "sora"


def _table(weight, outline=False):
    if outline:
        return _M["outline"]["200"]
    w = min(_WEIGHTS, key=lambda x: abs(x - weight))
    return _M["sora"][str(w)]


def width(text, size, weight=600, ls=0.0, outline=False):
    """Approximate rendered width of `text` in px (ls = letter-spacing in em)."""
    if _font == "mono":
        return len(text) * (0.6 * size + ls * size)
    scale = FONT_SCALE[_font]
    t = _table(weight, outline)
    fallback = _table(weight) if outline else None
    total = 0.0
    for ch in text:
        adv = t.get(ch)
        if adv is None and fallback is not None:
            adv = fallback.get(ch)
        total += (_FALLBACK_ADV if adv is None else adv) * size * scale + ls * size
    return total


def fit(text, max_w, size, weight=600, ls=0.0, min_size=10, outline=False):
    """Largest font size <= `size` for which `text` fits in `max_w`."""
    max_w *= FONT_MARGIN[_font]
    w = width(text, size, weight, ls, outline)
    if w <= max_w or w == 0:
        return size
    return max(min_size, size * max_w / w)


def clip(text, max_w, size, weight=600, ls=0.0):
    """Shorten `text` with an ellipsis until it fits `max_w`."""
    max_w *= FONT_MARGIN[_font]
    if width(text, size, weight, ls) <= max_w:
        return text
    while text and width(text + "…", size, weight, ls) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def fill(text, max_w, weight=800, ls=0.0, max_size=400, outline=False):
    """Font size at which `text` is exactly `max_w` wide (capped at `max_size`)."""
    w1 = width(text, 100, weight, ls, outline)
    if w1 == 0:
        return max_size
    return min(max_size, 100 * max_w / w1)


def wrap(text, max_w, size, weight=600, ls=0.0, max_lines=2):
    """Greedy word wrap by real width; the last line gets an ellipsis if cut."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if cur and width(trial, size, weight, ls) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and width(last + "…", size, weight, ls) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    # a single very long word: shorten it instead of overflowing
    out = []
    for ln in lines:
        if width(ln, size, weight, ls) > max_w:
            while ln and width(ln + "…", size, weight, ls) > max_w:
                ln = ln[:-1]
            ln = ln.rstrip() + "…"
        out.append(ln)
    return out
