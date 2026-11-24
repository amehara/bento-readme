"""Bridge between the web configurator (JavaScript) and the bento engine, run inside Pyodide."""
import json

from bento import cards, config, palettes, render, stats, themes

CONFIG_PATH = "/tmp/bento.yml"


def schema():
    """Everything the form needs to know about the engine, as JSON."""
    return json.dumps({
        "cards": {k: {"size": v.default_size, "cols": list(v.cols), "rows": list(v.rows)} for k, v in cards.CARDS.items()},
        "palettes": sorted(palettes.PALETTES),
        "themes": sorted(themes.THEMES),
        "gradients": sorted(palettes.GRADIENTS),
    })


def preview(yaml_text, profile_json="{}"):
    """Validates a config and renders it with sample numbers (and the real profile text, if given)."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(yaml_text)
        cfg = config.load_or_default(CONFIG_PATH)
        data = stats.demo(cfg["user"] or "octocat")
        prof = json.loads(profile_json or "{}")
        data["profile"].update({k: v for k, v in prof.items() if isinstance(v, str) and v})
        files = [
            {"variant": suffix or "single", "name": rel, "svg": render.render_svg(cfg, data, theme)}
            for suffix, theme, rel in render.outputs(cfg)
        ]
        return json.dumps({"error": None, "files": files, "snippet": render.readme_snippet(cfg, data),
                           "user": cfg["user"], "default": bool(cfg.get("default"))})
    except config.ConfigError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:  # noqa: BLE001 - never let a bad config break the page
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
