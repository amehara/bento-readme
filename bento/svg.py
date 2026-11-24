"""SVG builder: shapes, gradients, patterns and the document wrapper."""
import base64
import hashlib
import math
import os
import re
from xml.sax.saxutils import escape as _escape

from . import metrics
from .colors import average

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fonts")
_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")

FONT_STACKS = {
    "sora": "'Sora',-apple-system,'SF Pro Display','Helvetica Neue',Arial,sans-serif",
    "system": "-apple-system,'SF Pro Display','Segoe UI','Helvetica Neue',Arial,sans-serif",
    "serif": "'New York','Iowan Old Style',Georgia,'Times New Roman',serif",
    "mono": "'SF Mono','JetBrains Mono',Menlo,Consolas,'Courier New',monospace",
}


def clean(value):
    """Make arbitrary (possibly untrusted) text safe to embed in SVG."""
    return _escape(_BAD_XML.sub("", str(value)), {'"': "&quot;"})


def _b64(name):
    with open(os.path.join(_DATA, name), "rb") as f:
        return base64.b64encode(f.read()).decode()


class Canvas:
    def __init__(self, theme, style, gradients):
        self.t = theme
        self.style = style
        self.gradients = gradients  # name -> [(offset, color)]
        self.defs, self.body = [], []
        self._n = 0
        self._cache = {}
        self.uses_outline_font = False
        self.uses_pulse = False

    # ---- ids / defs -------------------------------------------------------
    def uid(self, prefix):
        self._n += 1
        return f"{prefix}{self._n}"

    def once(self, key, make):
        """Registers a def the first time `key` is seen; returns its id."""
        if key not in self._cache:
            ident = f"d{len(self._cache)}"
            self._cache[key] = ident
            self.defs.append(make(ident))
        return self._cache[key]

    def stops_for(self, accent):
        """accent: gradient name, or a list of 2-4 hex colors -> [(offset, color)]."""
        if isinstance(accent, str):
            return self.gradients[accent]
        n = len(accent)
        return [(round(i / (n - 1), 3), c) for i, c in enumerate(accent)]

    def paint(self, accent, horizontal=True):
        """Gradient paint reference for text/bars (`url(#id)`)."""
        stops = tuple(self.stops_for(accent))
        axis = (1, 0) if horizontal else (0, 1)

        def make(i):
            st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
            return f'<linearGradient id="{i}" x1="0" y1="0" x2="{axis[0]}" y2="{axis[1]}">{st}</linearGradient>'

        return f"url(#{self.once(('paint', stops, axis), make)})"

    def first_color(self, accent):
        return self.stops_for(accent)[0][1]

    # ---- geometry helpers -------------------------------------------------
    def radius(self, base, w, h, override=None):
        r = override if override is not None else base * self.style["corner_scale"]
        return round(max(0, min(r, w / 2, h / 2)), 2)

    def add(self, markup):
        self.body.append(markup)

    # ---- surfaces ---------------------------------------------------------
    def shadow(self, x, y, w, h, r):
        amount = self.style["shadow"]
        if not amount:
            return
        f = self.once(
            ("shadow", amount),
            lambda i: f'<filter id="{i}" x="-25%" y="-25%" width="150%" height="160%"><feDropShadow dx="0" dy="10" '
            f'stdDeviation="14" flood-color="#000" flood-opacity="{0.5 * amount:.2f}"/></filter>',
        )
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="#000" filter="url(#{f})"/>')

    def border(self, x, y, w, h, r, color, opacity, width):
        if not width or not opacity:
            return
        hw = width / 2
        self.add(
            f'<rect x="{x + hw:.2f}" y="{y + hw:.2f}" width="{w - width:.2f}" height="{h - width:.2f}" '
            f'rx="{max(r - hw, 0):.2f}" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="{width}"/>'
        )

    def gloss_overlay(self, x, y, w, h, r, gloss):
        g = self.once(
            ("gloss", gloss),
            lambda i: f'<linearGradient id="{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" '
            f'stop-opacity="{gloss:.3f}"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>',
        )
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#{g})"/>')

    def solid(self, x, y, w, h, r, fill, gloss=0.0):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
        if gloss:
            self.gloss_overlay(x, y, w, h, r, gloss)

    def linear(self, x, y, w, h, r, stops, angle=135, gloss=0.0):
        stops = tuple(stops)
        a = math.radians(angle)
        dx, dy = math.sin(a), -math.cos(a)

        def make(i):
            st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
            return (
                f'<linearGradient id="{i}" x1="{0.5 - dx / 2:.3f}" y1="{0.5 - dy / 2:.3f}" '
                f'x2="{0.5 + dx / 2:.3f}" y2="{0.5 + dy / 2:.3f}">{st}</linearGradient>'
            )

        g = self.once(("linear", stops, angle), make)
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#{g})"/>')
        if gloss:
            self.gloss_overlay(x, y, w, h, r, gloss)

    def mesh(self, x, y, w, h, r, palette, variant=0, gloss=0.28):
        """Blurred colour blobs clipped to a rounded rect (Apple-ish mesh gradient)."""
        c, f, g = self.uid("c"), self.uid("f"), self.uid("g")
        area = math.sqrt(w * h)
        blur = max(30, min(50, area * 0.17)) * self.style["mesh_blur"]
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
        self.add(s)

    def pattern(self, kind, x, y, w, h, r, color, opacity):
        """Decorative overlay clipped to the card: dots, grid, lines or grain."""
        c = self.uid("c")
        self.defs.append(f'<clipPath id="{c}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
        if kind == "grain":
            f = self.grain_filter()
            self.add(
                f'<g clip-path="url(#{c})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#808080" '
                f'filter="url(#{f})" opacity="{min(1, opacity * 3):.2f}"/></g>'
            )
            return
        shapes = {
            "dots": (18, 18, f'<circle cx="9" cy="9" r="1.6" fill="{color}"/>', ""),
            "grid": (24, 24, f'<path d="M24 0H0V24" fill="none" stroke="{color}" stroke-width="1"/>', ""),
            "lines": (12, 12, f'<line x1="0" y1="0" x2="0" y2="12" stroke="{color}" stroke-width="2"/>', ' patternTransform="rotate(45)"'),
        }
        pw, ph, inner, extra = shapes[kind]
        p = self.once(
            ("pattern", kind, color),
            lambda i: f'<pattern id="{i}" width="{pw}" height="{ph}" patternUnits="userSpaceOnUse"{extra}>{inner}</pattern>',
        )
        self.add(
            f'<g clip-path="url(#{c})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{p})" '
            f'opacity="{opacity}"/></g>'
        )

    def grain_filter(self):
        return self.once(
            "grain",
            lambda i: f'<filter id="{i}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" '
            f'baseFrequency=".85" numOctaves="2" stitchTiles="stitch" result="n"/><feColorMatrix in="n" type="matrix" '
            f'values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.2 -.35"/></filter>',
        )

    # ---- canvas background / grain ---------------------------------------
    def background(self, width, height, palettes):
        r = self.canvas_radius()
        bg = self.style["background"]
        if bg == "transparent":
            return
        if bg is None or bg == "theme":
            self.add(f'<rect width="{width}" height="{height}" rx="{r}" fill="{self.t["canvas"]}"/>')
        elif isinstance(bg, list):
            self.linear(0, 0, width, height, r, self.stops_for(bg), 160)
        elif bg in palettes:
            self.mesh(0, 0, width, height, r, palettes[bg], 0, 0.15)
        else:  # hex
            self.add(f'<rect width="{width}" height="{height}" rx="{r}" fill="{bg}"/>')

    def canvas_radius(self):
        return round(48 * self.style["corner_scale"])

    def finish(self, width, height):
        g = self.style["grain"]
        if g:
            f = self.grain_filter()
            c = self.uid("c")
            self.defs.append(
                f'<clipPath id="{c}"><rect width="{width}" height="{height}" rx="{self.canvas_radius()}"/></clipPath>'
            )
            self.add(
                f'<g clip-path="url(#{c})" style="pointer-events:none"><rect width="{width}" height="{height}" '
                f'fill="#808080" filter="url(#{f})" opacity="{g:.2f}"/></g>'
            )

    # ---- text -------------------------------------------------------------
    def text(self, x, y, s, size, fill, weight=800, ls=-0.03, anchor=None, extra="", exact=False):
        a = f' text-anchor="{anchor}"' if anchor else ""
        if exact and self.style["font"] != "sora":
            # fonts we do not embed: pin the width so the layout is the same on every system
            tl = metrics.width(str(s), size, weight, ls)
            extra += f' textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs"'
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{ls}em"{a} {extra}>{clean(s)}</text>'
        )

    def fitted(self, x, y, max_w, size, s, fill, weight=800, ls=-0.03, **kw):
        """Text shrunk (never stretched) so it fits `max_w`. Returns the size used."""
        s = str(s)
        size = metrics.fit(s, max_w, size, weight, ls, min_size=11)
        s = metrics.clip(s, max_w, size, weight, ls)  # last resort for absurdly long text
        self.text(x, y, s, size, fill, weight, ls, **kw)
        return size

    # ---- output -----------------------------------------------------------
    def document(self, width, height, title, alt):
        font = self.style["font"]
        css = ""
        if font == "sora":
            css += (
                "@font-face{font-family:'Sora';font-weight:100 800;src:url(data:font/woff2;base64,"
                + _b64("sora-subset.woff2")
                + ") format('woff2')}"
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
        style = f"<style>{css}</style>\n" if css else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="{FONT_STACKS[font]}" role="img" aria-label="{clean(alt)}">\n'
            f"<title>{clean(title)}</title>\n{style}<defs>{''.join(self.defs)}</defs>\n"
            f"{''.join(self.body)}\n</svg>\n"
        )

    @property
    def outline_family(self):
        return "SoraOutline,Sora,sans-serif" if self.style["font"] == "sora" else FONT_STACKS[self.style["font"]]


__all__ = ["Canvas", "clean", "average"]
