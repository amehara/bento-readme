"""Small SVG builder used by every card."""
import base64
import math
import os
import re
from xml.sax.saxutils import escape as _escape

from . import metrics
from .palettes import GRADIENTS

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fonts")
_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def clean(value):
    """Make arbitrary (possibly untrusted) text safe to embed in SVG."""
    return _escape(_BAD_XML.sub("", str(value)), {'"': "&quot;"})


def _b64(name):
    with open(os.path.join(_DATA, name), "rb") as f:
        return base64.b64encode(f.read()).decode()


class Canvas:
    def __init__(self, theme):
        self.t = theme
        self.defs, self.body = [], []
        self._n = 0
        self.uses_outline_font = False
        self.uses_pulse = False
        self._gradients = set()

    # ---- ids / defs -------------------------------------------------------
    def uid(self, prefix):
        self._n += 1
        return f"{prefix}{self._n}"

    def gradient(self, name):
        """Registers a named text gradient and returns a paint reference."""
        gid = f"grad-{name}"
        if gid not in self._gradients:
            self._gradients.add(gid)
            stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GRADIENTS[name])
            self.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>')
        return f"url(#{gid})"

    # ---- shapes -----------------------------------------------------------
    def add(self, markup):
        self.body.append(markup)

    def card(self, x, y, w, h, r=36, strong=False):
        t = self.t
        fill = t["card_strong"] if strong else t["card"]
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
        if t["gloss"]:
            g = self.uid("g")
            self.defs.append(
                f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" '
                f'stop-opacity="{t["gloss"]}"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            )
            self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#{g})"/>')
        self.add(
            f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" '
            f'stroke="{t["stroke"]}" stroke-opacity="{t["stroke_opacity"]}"/>'
        )

    def mesh(self, x, y, w, h, r, palette, variant=0, gloss=0.28):
        """Blurred colour blobs clipped to a rounded rect (Apple-ish mesh gradient)."""
        c, f, g = self.uid("c"), self.uid("f"), self.uid("g")
        area = math.sqrt(w * h)
        blur = max(30, min(50, area * 0.17))
        self.defs.append(f'<clipPath id="{c}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
        self.defs.append(
            f'<filter id="{f}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{blur:.0f}"/></filter>'
        )
        self.defs.append(
            f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" '
            f'stop-opacity="{gloss}"/><stop offset=".4" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        )
        # (x fraction of w, y fraction of h, radius fraction of sqrt(w*h)) per variant
        layouts = [
            [(0.22, 0.17, 0.40), (0.90, 0.86, 0.44), (0.83, 0.08, 0.26), (0.10, 0.95, 0.30)],
            [(0.15, 0.90, 0.42), (0.88, 0.15, 0.40), (0.50, 0.50, 0.22), (0.95, 0.90, 0.28)],
            [(0.80, 0.20, 0.42), (0.10, 0.75, 0.42), (0.45, 0.45, 0.26), (0.05, 0.05, 0.24)],
        ]
        blobs = layouts[variant % len(layouts)]
        s = f'<g clip-path="url(#{c})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{palette["base"]}"/>'
        s += f'<g filter="url(#{f})">'
        for i, (fx, fy, fr) in enumerate(blobs):
            col = palette["blobs"][i % len(palette["blobs"])]
            s += f'<circle cx="{x + fx * w:.1f}" cy="{y + fy * h:.1f}" r="{fr * area:.1f}" fill="{col}"/>'
        s += f'</g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{g})"/></g>'
        s += (
            f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" '
            f'stroke="#fff" stroke-opacity=".35"/>'
        )
        self.add(s)

    # ---- text -------------------------------------------------------------
    def text(self, x, y, s, size, fill, weight=800, ls=-0.03, anchor=None, extra=""):
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{ls}em"{a} {extra}>{clean(s)}</text>'
        )

    def label(self, x, y, s, fill=None):
        self.text(x, y, s, 14, fill or self.t["muted"], 600, 0.02)

    def fitted(self, x, y, max_w, size, s, fill, weight=800, ls=-0.03, **kw):
        """Text shrunk (never stretched) so it fits `max_w`. Returns the size used."""
        s = str(s)
        size = metrics.fit(s, max_w, size, weight, ls, min_size=11)
        s = metrics.clip(s, max_w, size, weight, ls)  # last resort for absurdly long text
        self.text(x, y, s, size, fill, weight, ls, **kw)
        return size

    # ---- output -----------------------------------------------------------
    def document(self, width, height, title, alt, lang="en"):
        sora = _b64("sora-subset.woff2")
        css = (
            "@font-face{font-family:'Sora';font-weight:100 800;src:url(data:font/woff2;base64," + sora + ") format('woff2')}"
        )
        if self.uses_outline_font:
            css += (
                "@font-face{font-family:'SoraOutline';font-weight:200;src:url(data:font/woff2;base64,"
                + _b64("sora-outline-digits.woff2")
                + ") format('woff2')}"
            )
        if self.uses_pulse:
            css += (
                "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}.pulse{animation:pulse 1.6s ease-in-out infinite}"
                "@media (prefers-reduced-motion:reduce){.pulse{animation:none}}"
            )
        family = "'Sora',-apple-system,'SF Pro Display','Helvetica Neue',Arial,sans-serif"
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="{family}" role="img" aria-label="{clean(alt)}">\n'
            f"<title>{clean(title)}</title>\n<style>{css}</style>\n<defs>{''.join(self.defs)}</defs>\n"
            f'<rect width="{width}" height="{height}" rx="48" fill="{self.t["canvas"]}"/>\n'
            f"{''.join(self.body)}\n</svg>\n"
        )
