"""Colour helpers: parsing, mixing and automatic text contrast."""
import re

_HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
_HEX3 = re.compile(r"^#[0-9a-fA-F]{3}$")


def norm(value):
    """'#abc' / '#aabbcc' -> '#aabbcc' (lowercase); anything else -> None."""
    if not isinstance(value, str):
        return None
    if _HEX6.match(value):
        return value.lower()
    if _HEX3.match(value):
        return "#" + "".join(ch * 2 for ch in value[1:]).lower()
    return None


def rgb(h):
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def to_hex(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def mix(a, b, t):
    """Blend colour a towards b by t (0..1)."""
    ra, rb = rgb(a), rgb(b)
    return to_hex(*(x * (1 - t) + y * t for x, y in zip(ra, rb)))


def luminance(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ink_for(bg, dark="#0b0b0c", light="#ffffff"):
    """Whichever of dark/light text reads better on `bg`."""
    return dark if contrast(bg, dark) >= contrast(bg, light) else light


def average(colors):
    rs = [rgb(c) for c in colors]
    n = len(rs)
    return to_hex(*(sum(c[i] for c in rs) / n for i in range(3)))
