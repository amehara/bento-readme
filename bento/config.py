"""Loads and validates bento.yml, with errors that tell people how to fix them."""
import difflib
import json
import os
import re

from .cards import CARDS, SOURCES
from .layout import LayoutError, parse_size
from .palettes import GRADIENTS, PALETTES

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
THEMES = ("dark", "light", "auto")
TOP_KEYS = {"github", "output", "theme", "alt", "palettes", "cards"}
USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


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


def _check_palettes(custom):
    if not isinstance(custom, dict):
        raise ConfigError("'palettes' must be a mapping of name -> {base, blobs, ink}")
    out = {}
    for name, p in custom.items():
        where = f"palettes.{name}"
        if not isinstance(p, dict) or not {"base", "blobs", "ink"} <= set(p):
            raise ConfigError(f"{where}: needs base, blobs (list of colors) and ink")
        colors = [p["base"], p["ink"], *(p["blobs"] if isinstance(p["blobs"], list) else [None])]
        if not p["blobs"] or not all(isinstance(c, str) and HEX.match(c) for c in colors):
            raise ConfigError(f"{where}: colors must be 6-digit hex like \"#ff8a00\"")
        out[str(name)] = {"base": p["base"], "blobs": list(p["blobs"]), "ink": p["ink"]}
    return out


def _check_card(i, spec, palettes):
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
    if spec.get("color") is not None and spec["color"] not in palettes:
        raise ConfigError(f"{where}: unknown color {spec['color']!r}.{_suggest(spec['color'], palettes)} "
                          f"Choose one of: {', '.join(sorted(palettes))}")
    if spec.get("accent") is not None and spec["accent"] not in GRADIENTS:
        raise ConfigError(f"{where}: unknown accent {spec['accent']!r}. Choose one of: {', '.join(GRADIENTS)}")
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
        for it in spec.get("items", []):
            col = it.get("color") if isinstance(it, dict) else None
            if col is not None and not (isinstance(col, str) and HEX.match(col)):
                raise ConfigError(f"{where}: item colors must be 6-digit hex like \"#3178c6\"")
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
    return cols, units


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

    theme = data.get("theme", "dark")
    if theme not in THEMES:
        raise ConfigError(f"theme must be one of: {', '.join(THEMES)}")

    palettes = dict(PALETTES)
    palettes.update(_check_palettes(data.get("palettes") or {}))

    raw_cards = data.get("cards")
    if not isinstance(raw_cards, list) or not raw_cards:
        raise ConfigError("'cards' must be a non-empty list")
    cards = []
    for i, spec in enumerate(raw_cards):
        if isinstance(spec, dict):  # `title:` with nothing after it means "not set"
            spec = {k: v for k, v in spec.items() if v is not None}
        cols, units = _check_card(i, spec, palettes)
        cards.append({"spec": spec, "cols": cols, "units": units})

    output = str(data.get("output", "bento.svg"))
    if os.path.isabs(output) or ".." in output.replace("\\", "/").split("/") or not output.lower().endswith(".svg"):
        raise ConfigError("'output' must be a relative .svg path inside the repository (e.g. bento.svg)")

    return {
        "user": str(user),
        "output": output,
        "theme": theme,
        "alt": str(data.get("alt") or (f"bento grid about {user}" if user else "bento grid")),
        "palettes": palettes,
        "cards": cards,
    }
