"""Built-in themes and the logic that builds a theme from a base plus overrides."""
from .colors import mix, norm

COLOR_KEYS = ("canvas", "card", "card_strong", "text", "text_soft", "muted", "stroke", "off", "chip")
NUMBER_KEYS = ("stroke_opacity", "gloss", "chip_opacity", "divider_opacity")
THEME_KEYS = set(COLOR_KEYS) | set(NUMBER_KEYS) | {"base"}


def _make(canvas, card, text, muted, strong=None, dark=True, gloss=None, stroke=None, stroke_opacity=None):
    return {
        "canvas": canvas,
        "card": card,
        "card_strong": strong or card,
        "text": text,
        "text_soft": mix(text, card, 0.12),
        "muted": muted,
        "stroke": stroke or ("#ffffff" if dark else "#000000"),
        "stroke_opacity": stroke_opacity if stroke_opacity is not None else (0.12 if dark else 0.08),
        "gloss": gloss if gloss is not None else (0.08 if dark else 0.0),
        "off": mix(card, text, 0.2),
        "chip": text,
        "chip_opacity": 0.12 if dark else 0.07,
        "divider_opacity": 0.14 if dark else 0.10,
    }


THEMES = {
    # the two originals, kept pixel-identical to the first release
    "dark": {
        "canvas": "#000000", "card": "#161618", "card_strong": "#111113", "text": "#ffffff",
        "text_soft": "#e5e5ea", "muted": "#a1a1a6", "stroke": "#ffffff", "stroke_opacity": 0.12,
        "gloss": 0.10, "off": "#3a3a3c", "chip": "#ffffff", "chip_opacity": 0.12, "divider_opacity": 0.14,
    },
    "light": {
        "canvas": "#f2f2f7", "card": "#ffffff", "card_strong": "#ffffff", "text": "#0b0b0c",
        "text_soft": "#3a3a3c", "muted": "#6e6e73", "stroke": "#000000", "stroke_opacity": 0.08,
        "gloss": 0.0, "off": "#d1d1d6", "chip": "#000000", "chip_opacity": 0.06, "divider_opacity": 0.10,
    },
    "midnight": _make("#0b1020", "#131a2e", "#e8ecff", "#8b95b8", "#0f1526"),
    "nord": _make("#2e3440", "#3b4252", "#eceff4", "#a7b1c5", "#353c4a"),
    "dracula": _make("#1e1f29", "#282a36", "#f8f8f2", "#a4abd0", "#21222c"),
    "solarized-dark": _make("#002b36", "#073642", "#eee8d5", "#93a1a1", "#00323d"),
    "solarized-light": _make("#fdf6e3", "#eee8d5", "#073642", "#657b83", "#f5eedc", dark=False),
    "catppuccin-mocha": _make("#11111b", "#1e1e2e", "#cdd6f4", "#a6adc8", "#181825"),
    "catppuccin-latte": _make("#e6e9ef", "#eff1f5", "#4c4f69", "#6c6f85", "#ffffff", dark=False),
    "github-dark": _make("#0d1117", "#161b22", "#e6edf3", "#8b949e", "#0d1117", gloss=0.0, stroke_opacity=0.14),
    "github-light": _make("#f6f8fa", "#ffffff", "#1f2328", "#59636e", "#ffffff", dark=False, stroke_opacity=0.12),
    "rose-pine": _make("#191724", "#1f1d2e", "#e0def4", "#908caa", "#26233a"),
    "paper": _make("#f4efe6", "#fffaf0", "#2b2418", "#7a6e5c", "#fbf5e9", dark=False, stroke_opacity=0.10),
    "terminal": _make("#000000", "#04120a", "#4af626", "#2f9a1a", "#020a05", gloss=0.0, stroke="#4af626", stroke_opacity=0.35),
    "brutalist": _make("#fff4d6", "#ffffff", "#000000", "#444444", "#ffffff", dark=False, gloss=0.0, stroke_opacity=1.0),
}


class ThemeError(ValueError):
    pass


def resolve(spec, custom=None):
    """spec: a theme name or a mapping {base, <overrides>} -> complete theme dict."""
    custom = custom or {}
    if isinstance(spec, str):
        if spec in custom:
            return custom[spec]
        if spec in THEMES:
            return dict(THEMES[spec])
        raise ThemeError(f"unknown theme {spec!r}")
    base = spec.get("base", "dark")
    t = resolve(base, custom)
    given = {k: v for k, v in spec.items() if k != "base"}
    for k in COLOR_KEYS:
        if k in given:
            t[k] = norm(given[k])
    for k in NUMBER_KEYS:
        if k in given:
            t[k] = float(given[k])
    # derive what the author did not set explicitly from what they did
    if "card" in given and "card_strong" not in given:
        t["card_strong"] = t["card"]
    if "card" in given or "text" in given:
        if "text_soft" not in given:
            t["text_soft"] = mix(t["text"], t["card"], 0.12)
        if "muted" not in given:
            t["muted"] = mix(t["text"], t["card"], 0.42)
        if "off" not in given:
            t["off"] = mix(t["card"], t["text"], 0.2)
    if "text" in given and "chip" not in given:
        t["chip"] = t["text"]
    return t


def validate(spec, where="theme"):
    """Raises ThemeError with a helpful message if a theme mapping is malformed."""
    if isinstance(spec, str):
        return
    if not isinstance(spec, dict):
        raise ThemeError(f"{where}: must be a theme name or a mapping")
    for k, v in spec.items():
        if k not in THEME_KEYS:
            raise ThemeError(f"{where}: unknown key {k!r}. Valid keys: {', '.join(sorted(THEME_KEYS))}")
        if k in COLOR_KEYS and norm(v) is None:
            raise ThemeError(f"{where}.{k}: must be a hex color like \"#1e1e2e\"")
        if k in NUMBER_KEYS and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1):
            raise ThemeError(f"{where}.{k}: must be a number between 0 and 1")
