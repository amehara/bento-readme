"""Loads and validates bento.yml, with errors that tell people how to fix them."""
import base64
import difflib
import json
import os
import re

from . import themes as themes_mod
from .cards import CARDS, PATTERNS, SOURCES
from .colors import norm
from .layout import LayoutError, parse_size
from .palettes import GRADIENTS, PALETTES

TOP_KEYS = {"github", "output", "theme", "themes", "style", "alt", "palettes", "gradients", "cards"}
USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
FONTS = ("sora", "system", "serif", "mono")
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
               "webp": "image/webp", "svg": "image/svg+xml"}
MAX_IMAGE_BYTES = 400_000

STYLE_KEYS = {"corners", "gap", "padding", "border", "border_width", "border_opacity", "gloss", "shadow", "grain",
              "background", "font", "text_case", "pattern", "pattern_opacity", "mesh_blur"}


class ConfigError(Exception):
    pass


def _suggest(word, options):
    m = difflib.get_close_matches(str(word), list(options), n=1)
    return f" Did you mean {m[0]!r}?" if m else ""


def _read(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if path.lower().endswith(".json"):
        return json.loads(raw)
    try:
        import yaml
    except ImportError:
        raise ConfigError("PyYAML is required to read .yml files: pip install pyyaml (or use a .json config)") from None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigError(f"{path} is not valid YAML:\n{e}") from None


def _num(v, lo, hi, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
        raise ConfigError(f"{where} must be a number between {lo} and {hi}")
    return float(v)


def _hex(v, where):
    c = norm(v)
    if c is None:
        raise ConfigError(f"{where} must be a hex color like \"#ff8a00\"")
    return c


def _hex_list(v, where, lo=2, hi=4):
    if not isinstance(v, list) or not lo <= len(v) <= hi:
        raise ConfigError(f"{where} must be a list of {lo}-{hi} hex colors")
    return [_hex(c, f"{where}[{i}]") for i, c in enumerate(v)]


# --------------------------------------------------------------------------- style
def _check_style(raw, palettes):
    if not isinstance(raw, dict):
        raise ConfigError("'style' must be a mapping")
    for k in raw:
        if k not in STYLE_KEYS:
            raise ConfigError(f"style: unknown key {k!r}.{_suggest(k, STYLE_KEYS)} Valid keys: {', '.join(sorted(STYLE_KEYS))}")
    st = {"corner_scale": 1.0, "border": True, "border_width": 1.0, "border_opacity": None, "gloss": 1.0,
          "shadow": 0.0, "grain": 0.0, "background": "transparent", "font": "sora", "text_case": "keep", "pattern": None,
          "pattern_opacity": 0.10, "mesh_blur": 1.0, "gap": 16, "padding": 24}
    c = raw.get("corners")
    if c is not None:
        scales = {"round": 1.0, "soft": 0.55, "sharp": 0.12}
        if isinstance(c, str):
            if c not in scales:
                raise ConfigError("style.corners must be round, soft, sharp or a number of pixels (0-60)")
            st["corner_scale"] = scales[c]
        else:
            st["corner_scale"] = _num(c, 0, 60, "style.corners") / 36
    if "border" in raw:
        b = raw["border"]
        st["border"] = b if isinstance(b, bool) else _hex(b, "style.border (true, false or a hex color)")
    if "border_width" in raw:
        st["border_width"] = _num(raw["border_width"], 0, 8, "style.border_width")
    if "border_opacity" in raw:
        st["border_opacity"] = _num(raw["border_opacity"], 0, 1, "style.border_opacity")
    for key, on_value, hi in (("gloss", 1.0, 2), ("shadow", 0.5, 1), ("grain", 0.12, 0.5)):
        if key in raw:
            v = raw[key]
            st[key] = (on_value if v else 0.0) if isinstance(v, bool) else _num(v, 0, hi, f"style.{key}")
    if "background" in raw:
        b = raw["background"]
        if isinstance(b, list):
            st["background"] = _hex_list(b, "style.background")
        elif isinstance(b, str) and b in ("theme", "transparent"):
            st["background"] = b
        elif isinstance(b, str) and b in palettes:
            st["background"] = b
        else:
            st["background"] = _hex(b, "style.background (theme, transparent, a palette name, a hex color or a list of hex colors)")
    if "font" in raw:
        if raw["font"] not in FONTS:
            raise ConfigError(f"style.font must be one of: {', '.join(FONTS)}")
        st["font"] = raw["font"]
    if "text_case" in raw:
        if raw["text_case"] not in ("keep", "lower", "upper"):
            raise ConfigError("style.text_case must be keep, lower or upper")
        st["text_case"] = raw["text_case"]
    if "pattern" in raw:
        if raw["pattern"] not in (*PATTERNS, "none"):
            raise ConfigError(f"style.pattern must be one of: none, {', '.join(PATTERNS)}")
        st["pattern"] = None if raw["pattern"] == "none" else raw["pattern"]
    if "pattern_opacity" in raw:
        st["pattern_opacity"] = _num(raw["pattern_opacity"], 0, 1, "style.pattern_opacity")
    if "mesh_blur" in raw:
        st["mesh_blur"] = _num(raw["mesh_blur"], 0.3, 2, "style.mesh_blur")
    if "gap" in raw:
        st["gap"] = _num(raw["gap"], 0, 40, "style.gap")
    if "padding" in raw:
        st["padding"] = _num(raw["padding"], 0, 64, "style.padding")
    else:
        # a transparent canvas shows only the cards, so no outer margin; shadows and opaque canvases need some room
        st["padding"] = 0 if st["background"] == "transparent" and not st["shadow"] else 24
    return st


# ------------------------------------------------------------------------ palettes
def _check_palettes(custom):
    if not isinstance(custom, dict):
        raise ConfigError("'palettes' must be a mapping of name -> {base, blobs, ink}")
    out = {}
    for name, p in custom.items():
        where = f"palettes.{name}"
        if not isinstance(p, dict) or not {"base", "blobs", "ink"} <= set(p):
            raise ConfigError(f"{where}: needs base, blobs (list of colors) and ink")
        out[str(name)] = {
            "base": _hex(p["base"], f"{where}.base"),
            "blobs": _hex_list(p["blobs"], f"{where}.blobs", 1, 8),
            "ink": _hex(p["ink"], f"{where}.ink"),
        }
    return out


def _check_gradients(custom):
    if not isinstance(custom, dict):
        raise ConfigError("'gradients' must be a mapping of name -> list of 2-4 hex colors")
    out = {}
    for name, colors in custom.items():
        cols = _hex_list(colors, f"gradients.{name}")
        n = len(cols)
        out[str(name)] = [(round(i / (n - 1), 3), c) for i, c in enumerate(cols)]
    return out


# --------------------------------------------------------------------------- themes
def _build_themes(data):
    custom = {}
    for name, spec in (data.get("themes") or {}).items():
        try:
            themes_mod.validate(spec, f"themes.{name}")
            custom[str(name)] = themes_mod.resolve(spec, custom)
        except themes_mod.ThemeError as e:
            raise ConfigError(str(e)) from None

    def one(spec, where):
        try:
            themes_mod.validate(spec, where)
            return themes_mod.resolve(spec, custom)
        except themes_mod.ThemeError as e:
            known = sorted({*themes_mod.THEMES, *custom})
            raise ConfigError(f"{e}.{_suggest(spec, known) if isinstance(spec, str) else ''} Available: {', '.join(known)}") from None

    spec = data.get("theme", "dark")
    if spec == "auto":
        return [("dark", one("dark", "theme")), ("light", one("light", "theme"))]
    if isinstance(spec, list):
        if len(spec) != 2:
            raise ConfigError("theme as a list needs exactly two entries: [dark theme, light theme]")
        return [("dark", one(spec[0], "theme[0]")), ("light", one(spec[1], "theme[1]"))]
    return [("", one(spec, "theme"))]


# ----------------------------------------------------------------------------- cards
def _load_image(spec, where, base_dir):
    src = spec.get("src")
    if not isinstance(src, str) or not src:
        raise ConfigError(f"{where}: 'src' is required (a path to an image next to bento.yml)")
    if os.path.isabs(src) or ".." in src.replace("\\", "/").split("/"):
        raise ConfigError(f"{where}: 'src' must be a relative path inside the repository")
    full = os.path.realpath(os.path.join(base_dir, src))
    if not full.startswith(os.path.realpath(base_dir) + os.sep) or not os.path.isfile(full):
        raise ConfigError(f"{where}: image not found: {src}")
    ext = full.rsplit(".", 1)[-1].lower()
    if ext not in IMAGE_TYPES:
        raise ConfigError(f"{where}: unsupported image type .{ext}; use {', '.join(IMAGE_TYPES)}")
    if os.path.getsize(full) > MAX_IMAGE_BYTES:
        raise ConfigError(f"{where}: {src} is larger than {MAX_IMAGE_BYTES // 1000} KB; shrink it first")
    with open(full, "rb") as f:
        return IMAGE_TYPES[ext], base64.b64encode(f.read()).decode()


def _check_card(i, spec, palettes, gradients, base_dir):
    where = f"cards[{i}]"
    if not isinstance(spec, dict) or "type" not in spec:
        raise ConfigError(f"{where}: every card needs a 'type' ({', '.join(CARDS)})")
    kind = spec["type"]
    if kind not in CARDS:
        raise ConfigError(f"{where}: unknown type {kind!r}.{_suggest(kind, CARDS)} Valid types: {', '.join(CARDS)}")
    ct = CARDS[kind]
    where = f"{where} ({kind})"
    for k in spec:
        if k not in ct.keys:
            raise ConfigError(f"{where}: unknown key {k!r}.{_suggest(k, ct.keys)} Valid keys: {', '.join(sorted(ct.keys))}")
    spec = dict(spec)
    names = ", ".join(sorted(palettes))
    if spec.get("color") is not None and spec["color"] not in palettes:
        raise ConfigError(f"{where}: unknown color {spec['color']!r}.{_suggest(spec['color'], palettes)} Choose one of: {names}")
    if "bg" in spec:
        bg = spec["bg"]
        if isinstance(bg, list):
            spec["bg"] = _hex_list(bg, f"{where}: bg")
        elif isinstance(bg, str) and bg in palettes:
            pass
        else:
            spec["bg"] = _hex(bg, f"{where}: bg (a palette name, a hex color or a list of hex colors)")
    if "fg" in spec:
        spec["fg"] = _hex(spec["fg"], f"{where}: fg")
    if "bg_angle" in spec:
        _num(spec["bg_angle"], 0, 360, f"{where}: bg_angle")
    if "radius" in spec:
        _num(spec["radius"], 0, 120, f"{where}: radius")
    if "border" in spec:
        b = spec["border"]
        if b is False or b == "none":
            spec["border"] = False
        elif b is not True:
            spec["border"] = _hex(b, f"{where}: border (none, true or a hex color)")
    if spec.get("pattern") is not None and spec["pattern"] not in (*PATTERNS, "none"):
        raise ConfigError(f"{where}: pattern must be one of: none, {', '.join(PATTERNS)}")
    if "pattern_opacity" in spec:
        _num(spec["pattern_opacity"], 0, 1, f"{where}: pattern_opacity")
    acc = spec.get("accent")
    if acc is not None:
        if isinstance(acc, list):
            spec["accent"] = _hex_list(acc, f"{where}: accent")
        elif acc not in gradients:
            raise ConfigError(f"{where}: unknown accent {acc!r}.{_suggest(acc, gradients)} Choose one of: "
                              f"{', '.join(sorted(gradients))} or a list of hex colors")
    if spec.get("source") is not None and spec["source"] not in SOURCES:
        raise ConfigError(f"{where}: unknown source {spec['source']!r}.{_suggest(spec['source'], SOURCES)} "
                          f"Valid sources: {', '.join(SOURCES)}")
    if kind == "number":
        style = spec.get("style", "mesh")
        if style not in ("mesh", "outline", "plain"):
            raise ConfigError(f"{where}: style must be mesh, outline or plain")
        if "value" not in spec and "source" not in spec:
            raise ConfigError(f"{where}: set either 'value' (any text) or 'source' ({', '.join(SOURCES)})")
        for m in spec.get("minis") or []:
            src = m if isinstance(m, str) else (m or {}).get("source")
            if src is not None and src not in SOURCES:
                raise ConfigError(f"{where}: minis source {src!r} is not one of {', '.join(SOURCES)}")
    if kind == "stack":
        if spec.get("chip_style", "dot") not in ("dot", "filled", "outline"):
            raise ConfigError(f"{where}: chip_style must be dot, filled or outline")
        items = []
        for it in spec.get("items", []):
            if isinstance(it, dict):
                it = dict(it)
                if it.get("color") is not None:
                    it["color"] = _hex(it["color"], f"{where}: item colors")
            items.append(it)
        spec["items"] = items
    if kind == "text" and spec.get("style", "plain") not in ("plain", "quote"):
        raise ConfigError(f"{where}: style must be plain or quote")
    if kind == "image":
        if spec.get("fit", "cover") not in ("cover", "contain"):
            raise ConfigError(f"{where}: fit must be cover or contain")
        spec["_image"] = _load_image(spec, where, base_dir)
    if kind == "ring":
        _num(spec.get("value", 0), 0, 100, f"{where}: value")
    if kind == "heatmap" and "weeks" in spec:
        _num(spec["weeks"], 4, 53, f"{where}: weeks")
    default = "1x2" if (kind == "number" and spec.get("style") == "outline") else ct.default_size
    try:
        cols, units = parse_size(spec.get("size"), default)
    except LayoutError as e:
        raise ConfigError(f"{where}: {e}") from None
    style_rows = (2,) if (kind == "number" and spec.get("style") == "outline") else ct.rows
    lo, hi = ct.cols
    if not lo <= cols <= hi or units / 2 not in style_rows:
        rows = " or ".join(str(r) for r in style_rows)
        raise ConfigError(f"{where}: size {spec.get('size')!r} is not supported; columns {lo}-{hi}, rows {rows}")
    return spec, cols, units


DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "default.yml")


def load_or_default(path):
    """Like load(), but a missing file means "use the built-in bento made from your GitHub profile"."""
    if os.path.exists(path):
        return load(path)
    cfg = load(DEFAULT_PATH)
    cfg["default"] = True
    return cfg


def load(path):
    if not os.path.exists(path):
        raise ConfigError(f"config file not found: {path}  (create one with: python -m bento init)")
    try:
        data = _read(path)
    except ValueError as e:
        raise ConfigError(f"{path} is not valid JSON: {e}") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    for k in data:
        if k not in TOP_KEYS:
            raise ConfigError(f"unknown top-level key {k!r}.{_suggest(k, TOP_KEYS)} Valid keys: {', '.join(sorted(TOP_KEYS))}")

    gh = data.get("github") or {}
    if not isinstance(gh, dict) or set(gh) - {"user"}:
        raise ConfigError("'github' only accepts 'user'")
    user = gh.get("user") or os.environ.get("GH_USER") or ""
    if user and not USER_RE.match(str(user)):
        raise ConfigError(f"github.user {user!r} does not look like a GitHub username")

    palettes = dict(PALETTES)
    palettes.update(_check_palettes(data.get("palettes") or {}))
    gradients = dict(GRADIENTS)
    gradients.update(_check_gradients(data.get("gradients") or {}))
    style = _check_style(data.get("style") or {}, palettes)
    variants = _build_themes(data)

    raw_cards = data.get("cards")
    if not isinstance(raw_cards, list) or not raw_cards:
        raise ConfigError("'cards' must be a non-empty list")
    base_dir = os.path.dirname(os.path.abspath(path))
    cards = []
    for i, spec in enumerate(raw_cards):
        if isinstance(spec, dict):  # `title:` with nothing after it means "not set"
            spec = {k: v for k, v in spec.items() if v is not None}
        spec, cols, units = _check_card(i, spec, palettes, gradients, base_dir)
        cards.append({"spec": spec, "cols": cols, "units": units})

    output = str(data.get("output", "bento.svg"))
    if os.path.isabs(output) or ".." in output.replace("\\", "/").split("/") or not output.lower().endswith(".svg"):
        raise ConfigError("'output' must be a relative .svg path inside the repository (e.g. bento.svg)")

    return {
        "user": str(user),
        "output": output,
        "variants": variants,
        "alt": str(data.get("alt") or (f"bento grid about {user}" if user else "bento grid")),
        "palettes": palettes,
        "gradients": gradients,
        "style": style,
        "cards": cards,
    }
