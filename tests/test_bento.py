import contextlib
import io
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bento import cli, layout, metrics, render, stats  # noqa: E402
from bento.config import ConfigError, load  # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")


def write_cfg(text, name="bento.yml"):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class LayoutTests(unittest.TestCase):
    def test_parse_size(self):
        self.assertEqual(layout.parse_size("2x1", None), (2, 2))
        self.assertEqual(layout.parse_size("4x0.5", None), (4, 1))
        self.assertEqual(layout.parse_size(None, "1x2"), (1, 4))
        for bad in ("5x1", "0x1", "2x0.25", "wide", "2x"):
            with self.assertRaises(layout.LayoutError):
                layout.parse_size(bad, None)

    def test_dense_packing_fills_gaps_without_overlap(self):
        sizes = [(2, 4), (1, 2), (1, 4), (1, 2), (2, 2), (1, 2), (4, 1)]
        spots, total = layout.place(sizes)
        cells = set()
        for (cols, units), (c, u) in zip(sizes, spots):
            for dc in range(cols):
                for du in range(units):
                    self.assertNotIn((c + dc, u + du), cells)
                    self.assertLess(c + dc, layout.COLS)
                    cells.add((c + dc, u + du))
        self.assertEqual(total, max(u for _, u in cells) + 1)

    def test_full_row_geometry(self):
        self.assertEqual(layout.rect(0, 0, 2, 2)[2:], (568, 232))
        self.assertEqual(layout.rect(0, 0, 2, 4)[2:], (568, 480))
        self.assertEqual(layout.CANVAS_W, 1200)


class MetricsTests(unittest.TestCase):
    def test_width_scales_and_fit_shrinks(self):
        self.assertAlmostEqual(metrics.width("abc", 20) * 2, metrics.width("abc", 40))
        size = metrics.fit("headline", 100, 40)
        self.assertLess(size, 40)
        self.assertLessEqual(metrics.width("headline", size), 100.5)

    def test_clip_is_the_last_resort(self):
        text = metrics.clip("a very long headline indeed " * 3, 100, 12)
        self.assertTrue(text.endswith("…"))
        self.assertLessEqual(metrics.width(text, 12), 100)

    def test_wrap_limits_lines_and_adds_ellipsis(self):
        lines = metrics.wrap("one two three four five six seven eight nine ten", 120, 20, max_lines=2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("…"))
        for ln in lines:
            self.assertLessEqual(metrics.width(ln, 20), 120)


class ConfigTests(unittest.TestCase):
    def test_all_examples_validate_and_render(self):
        for name in ("designer", "developer", "minimal"):
            cfg = load(os.path.join(EXAMPLES, f"{name}.yml"))
            for theme, _ in render.outputs(cfg):
                svg = render.render_svg(cfg, stats.demo("someone"), theme)
                root = ET.fromstring(svg)  # well-formed XML
                self.assertTrue(root.tag.endswith("svg"))
                self.assertLess(len(svg), 200_000)

    def test_cards_stay_inside_canvas(self):
        cfg = load(os.path.join(EXAMPLES, "designer.yml"))
        spots, total = layout.place([(c["cols"], c["units"]) for c in cfg["cards"]])
        h = layout.canvas_height(total)
        for c, (col, unit) in zip(cfg["cards"], spots):
            x, y, w, hh = layout.rect(col, unit, c["cols"], c["units"])
            self.assertLessEqual(x + w, layout.CANVAS_W - layout.PAD)
            self.assertLessEqual(y + hh, h - layout.PAD)

    def test_errors_are_helpful(self):
        cases = {
            "cards:\n  - type: numbr\n": "Did you mean 'number'",
            "cards:\n  - type: number\n    valeu: 1\n": "Did you mean 'value'",
            "cards:\n  - type: number\n    value: 1\n    color: nope\n": "unknown color",
            "cards:\n  - type: number\n": "set either 'value'",
            "cards:\n  - type: streak\n    size: 4x2\n": "not supported",
            "cards: []\n": "non-empty",
            "theme: neon\ncards:\n  - type: streak\n": "theme must be",
            "output: ../evil.svg\ncards:\n  - type: streak\n": "relative .svg",
            "output: /etc/x.svg\ncards:\n  - type: streak\n": "relative .svg",
            "bogus: 1\ncards:\n  - type: streak\n": "unknown top-level key",
            "cards:\n  - type: stack\n    items:\n      - {name: x, color: 'red\" onload=\"x'}\n": "hex",
            "palettes:\n  p: {base: '#fff', blobs: ['#000000'], ink: '#000000'}\ncards:\n  - type: streak\n": "hex",
            "github: {user: 'bad user!'}\ncards:\n  - type: streak\n": "username",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(ConfigError) as cm:
                    load(write_cfg(text))
                self.assertIn(expected, str(cm.exception))

    def test_outline_defaults_to_two_rows_and_empty_values_are_unset(self):
        cfg = load(write_cfg("cards:\n  - type: number\n    style: outline\n    value: 7\n    eyebrow:\n"))
        self.assertEqual((cfg["cards"][0]["cols"], cfg["cards"][0]["units"]), (1, 4))
        self.assertNotIn("eyebrow", cfg["cards"][0]["spec"])
        self.assertNotIn("None", render.render_svg(cfg, stats.demo(), "dark"))

    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            load(os.path.join(tempfile.gettempdir(), "does-not-exist.yml"))

    def test_custom_palette_is_usable(self):
        cfg = load(write_cfg(
            "palettes:\n  mine: {base: '#112233', blobs: ['#445566'], ink: '#ffffff'}\n"
            "cards:\n  - type: number\n    value: hi\n    color: mine\n"
        ))
        svg = render.render_svg(cfg, stats.demo(), "dark")
        self.assertIn("#112233", svg)


class SafetyTests(unittest.TestCase):
    def test_untrusted_text_cannot_inject_markup(self):
        evil = '<script>alert(1)</script> & "quotes" \x00\x08'
        cfg = load(write_cfg("cards:\n  - type: commit\n  - type: number\n    value: x\n"))
        data = stats.demo()
        data["now"] = {"repo": evil, "message": evil, "when": evil}
        svg = render.render_svg(cfg, data, "dark")
        ET.fromstring(svg)
        self.assertNotIn("<script", svg)

    def test_long_text_is_fitted_not_overflowing(self):
        cfg = load(write_cfg(
            "cards:\n  - type: hero\n    title: " + "W" * 80 + "\n    headline: [" + "m" * 60 + "]\n"
            "  - type: stack\n    items: [" + ", ".join("tool%d" % i for i in range(60)) + "]\n"
        ))
        ET.fromstring(render.render_svg(cfg, stats.demo(), "light"))


class BuildTests(unittest.TestCase):
    def test_auto_theme_writes_both_files_and_snippet(self):
        p = write_cfg("theme: auto\noutput: out/b.svg\ncards:\n  - type: streak\n")
        cfg = load(p)
        files = render.build(cfg, stats.demo(), os.path.dirname(p))
        self.assertEqual([os.path.basename(f) for f in files], ["b-dark.svg", "b-light.svg"])
        self.assertIn("prefers-color-scheme: dark", render.readme_snippet(cfg))

    def test_cli_build_demo_and_init(self):
        d = tempfile.mkdtemp()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["init", "--dir", d, "--user", "octocat", "--template", "minimal"]), 0)
            self.assertEqual(cli.main(["build", "-c", os.path.join(d, "bento.yml"), "--demo"]), 0)
        self.assertTrue(os.path.exists(os.path.join(d, "bento.svg")))
        self.assertTrue(os.path.exists(os.path.join(d, ".github", "workflows", "bento.yml")))
        with open(os.path.join(d, "bento.yml"), encoding="utf-8") as f:
            self.assertIn("octocat", f.read())
        err = io.StringIO()
        with contextlib.redirect_stderr(err):  # refuses to overwrite
            self.assertEqual(cli.main(["init", "--dir", d]), 1)

    def test_empty_stats_render_without_fake_data(self):
        cfg = load(write_cfg("cards:\n  - type: commit\n  - type: languages\n  - type: streak\n"))
        svg = render.render_svg(cfg, stats.empty("me"), "dark")
        ET.fromstring(svg)
        self.assertIn("no recent public", svg)  # wraps onto two lines
        self.assertNotIn("my-project", svg)

    def test_cache_roundtrip(self):
        d = tempfile.mkdtemp()
        data = stats.demo("me")
        stats.save_cache(data, d)
        self.assertEqual(stats.load_cache(d)["username"], "me")


if __name__ == "__main__":
    unittest.main()
