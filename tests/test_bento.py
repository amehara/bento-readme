import contextlib
import io
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bento import cli, colors, layout, metrics, render, stats, themes  # noqa: E402
from bento.config import ConfigError, load  # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")
EXAMPLE_NAMES = sorted(f[:-4] for f in os.listdir(EXAMPLES) if f.endswith(".yml"))


def write_cfg(text, name="bento.yml", folder=None):
    d = folder or tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def svg_of(cfg, data=None, variant=0):
    return render.render_svg(cfg, data or stats.demo("someone"), cfg["variants"][variant][1])


def card(kind, extra=""):
    return f"cards:\n  - type: {kind}\n{extra}"


# one of every card type, with enough content to exercise every code path
KITCHEN_SINK = """
cards:
  - {type: hero, size: 2x2, title: Name, subtitle: role, intro: [one, two], headline: [big, words]}
  - {type: number, source: contributions, label: [a, b]}
  - {type: number, style: outline, source: contributions, eyebrow: x, label: y, caption: z}
  - {type: number, style: plain, source: lines, label: l, minis: [repos, stars, followers]}
  - {type: streak}
  - {type: commit}
  - {type: status, word: "on", caption: c}
  - {type: stack, items: [python, rust, "a very long tool name indeed"], chip_style: filled}
  - {type: languages}
  - {type: cta, text: hello, caption: there}
  - {type: text, body: some words to wrap around a few lines, title: t, author: me}
  - {type: contact, items: ["a: b", "c: d"]}
  - {type: heatmap, size: 2x1}
  - {type: repos}
  - {type: bars, items: ["x: 40", "y: 90"]}
  - {type: ring, value: 66, label: l, caption: c}
  - {type: band, text: bye}
"""


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

    def test_default_geometry_matches_original_sizes(self):
        g = layout.geometry()
        self.assertEqual(layout.rect(g, 0, 0, 2, 2)[2:], (568, 232))
        self.assertEqual(layout.rect(g, 0, 0, 2, 4)[2:], (568, 480))

    def test_custom_gap_and_padding_keep_rows_and_fit_canvas(self):
        for pad, gap in ((0, 0), (12, 8), (24, 16), (64, 40)):
            g = layout.geometry(pad, gap)
            x, y, w, h = layout.rect(g, 0, 0, 1, 2)
            self.assertAlmostEqual(h, 232, delta=0.1)  # a row is always 232px
            x, y, w, h = layout.rect(g, 3, 0, 1, 2)
            self.assertAlmostEqual(x + w, layout.CANVAS_W - pad, delta=0.1)


class MetricsTests(unittest.TestCase):
    def tearDown(self):
        metrics.set_font("sora")

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

    def test_other_fonts_are_narrower_and_mono_is_fixed_width(self):
        sora = metrics.width("hello world", 20)
        metrics.set_font("serif")
        self.assertLess(metrics.width("hello world", 20), sora)
        metrics.set_font("mono")
        self.assertAlmostEqual(metrics.width("iiii", 10, ls=0), metrics.width("WWWW", 10, ls=0))


class ColorTests(unittest.TestCase):
    def test_norm_accepts_short_hex_only(self):
        self.assertEqual(colors.norm("#ABC"), "#aabbcc")
        self.assertEqual(colors.norm("#AABBCC"), "#aabbcc")
        for bad in ("red", "#12", "#gggggg", "ff0000", None, 5, "#fff;x"):
            self.assertIsNone(colors.norm(bad))

    def test_ink_picks_readable_text(self):
        self.assertEqual(colors.ink_for("#ffffff"), "#0b0b0c")
        self.assertEqual(colors.ink_for("#000000"), "#ffffff")
        self.assertEqual(colors.ink_for("#ffcc00"), "#0b0b0c")
        self.assertEqual(colors.ink_for("#1a1a40"), "#ffffff")

    def test_mix(self):
        self.assertEqual(colors.mix("#000000", "#ffffff", 0.5), "#808080")


class ConfigTests(unittest.TestCase):
    def test_all_examples_validate_and_render(self):
        for name in EXAMPLE_NAMES:
            with self.subTest(example=name):
                cfg = load(os.path.join(EXAMPLES, f"{name}.yml"))
                for i in range(len(cfg["variants"])):
                    svg = svg_of(cfg, variant=i)
                    self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))
                    self.assertLess(len(svg), 250_000)

    def test_cards_stay_inside_canvas(self):
        cfg = load(os.path.join(EXAMPLES, "pastel.yml"))  # custom gap/padding
        geo = layout.geometry(cfg["style"]["padding"], cfg["style"]["gap"])
        spots, total = layout.place([(c["cols"], c["units"]) for c in cfg["cards"]])
        h = layout.canvas_height(geo, total)
        for c, (col, unit) in zip(cfg["cards"], spots):
            x, y, w, hh = layout.rect(geo, col, unit, c["cols"], c["units"])
            self.assertLessEqual(x + w, layout.CANVAS_W - geo.pad + 0.1)
            self.assertLessEqual(y + hh, h - geo.pad + 1)

    def test_errors_are_helpful(self):
        s = "  - type: streak\n"
        cases = {
            "cards:\n  - type: numbr\n": "Did you mean 'number'",
            "cards:\n  - type: number\n    valeu: 1\n": "Did you mean 'value'",
            "cards:\n  - type: number\n    value: 1\n    color: nope\n": "unknown color",
            "cards:\n  - type: number\n": "set either 'value'",
            "cards:\n  - type: streak\n    size: 4x2\n": "not supported",
            "cards: []\n": "non-empty",
            "theme: neon\ncards:\n" + s: "unknown theme",
            "theme: nrod\ncards:\n" + s: "Did you mean 'nord'",
            "theme: [dark]\ncards:\n" + s: "exactly two",
            "theme: {base: dark, card: red}\ncards:\n" + s: "hex color",
            "theme: {bogus: 1}\ncards:\n" + s: "unknown key",
            "output: ../evil.svg\ncards:\n" + s: "relative .svg",
            "output: /etc/x.svg\ncards:\n" + s: "relative .svg",
            "bogus: 1\ncards:\n" + s: "unknown top-level key",
            "cards:\n  - type: stack\n    items:\n      - {name: x, color: 'red\" onload=\"x'}\n": "hex",
            "palettes:\n  p: {base: red, blobs: ['#000000'], ink: '#000000'}\ncards:\n" + s: "hex color",
            "github: {user: 'bad user!'}\ncards:\n" + s: "username",
            "style: {corners: wobbly}\ncards:\n" + s: "style.corners",
            "style: {font: comic}\ncards:\n" + s: "style.font",
            "style: {gap: 99}\ncards:\n" + s: "style.gap",
            "style: {shaddow: true}\ncards:\n" + s: "Did you mean 'shadow'",
            "style: {background: 'url(x)'}\ncards:\n" + s: "style.background",
            "cards:\n  - type: streak\n    bg: 'red'\n": "bg",
            "cards:\n  - type: streak\n    fg: 12\n": "fg",
            "cards:\n  - type: streak\n    radius: 500\n": "radius",
            "cards:\n  - type: streak\n    pattern: stripes\n": "pattern",
            "cards:\n  - type: streak\n    accent: [red, blue]\n": "accent",
            "cards:\n  - type: streak\n    accent: nope\n": "unknown accent",
            "cards:\n  - type: ring\n    value: 140\n": "value",
            "cards:\n  - type: image\n    src: ../secret.png\n": "relative path",
            "cards:\n  - type: image\n    src: missing.png\n": "not found",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(ConfigError) as cm:
                    load(write_cfg(text))
                self.assertIn(expected, str(cm.exception))

    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            load(os.path.join(tempfile.gettempdir(), "does-not-exist.yml"))

    def test_outline_defaults_to_two_rows_and_empty_values_are_unset(self):
        cfg = load(write_cfg("cards:\n  - type: number\n    style: outline\n    value: 7\n    eyebrow:\n"))
        self.assertEqual((cfg["cards"][0]["cols"], cfg["cards"][0]["units"]), (1, 4))
        self.assertNotIn("eyebrow", cfg["cards"][0]["spec"])
        self.assertNotIn("None", svg_of(cfg))

    def test_custom_palette_and_gradient(self):
        cfg = load(write_cfg(
            "palettes:\n  mine: {base: '#112233', blobs: ['#445566'], ink: '#fff'}\n"
            "gradients:\n  g: ['#ff0000', '#00ff00']\n"
            "cards:\n  - type: number\n    value: hi\n    color: mine\n  - type: ring\n    value: 5\n    accent: g\n"
            "  - type: ring\n    value: 5\n    accent: ['#abc', '#def']\n"
        ))
        svg = svg_of(cfg)
        self.assertIn("#112233", svg)
        self.assertIn("#ff0000", svg)
        self.assertIn("#aabbcc", svg)  # short hex gets normalised

    def test_theme_forms(self):
        s = "cards:\n  - type: streak\n"
        self.assertEqual(len(load(write_cfg("theme: nord\n" + s))["variants"]), 1)
        auto = load(write_cfg("theme: auto\n" + s))
        self.assertEqual([n for n, _ in auto["variants"]], ["dark", "light"])
        pair = load(write_cfg("theme: [dracula, paper]\n" + s))
        self.assertEqual(pair["variants"][0][1]["canvas"], themes.THEMES["dracula"]["canvas"])
        self.assertEqual(pair["variants"][1][1]["canvas"], themes.THEMES["paper"]["canvas"])
        inline = load(write_cfg("theme: {base: nord, card: '#123456'}\n" + s))
        t = inline["variants"][0][1]
        self.assertEqual(t["card"], "#123456")
        self.assertEqual(t["canvas"], themes.THEMES["nord"]["canvas"])
        self.assertEqual(t["card_strong"], "#123456")  # derived, not left on the old colour
        named = load(write_cfg("themes:\n  mine: {base: light, text: '#112233'}\ntheme: mine\n" + s))
        self.assertEqual(named["variants"][0][1]["text"], "#112233")

    def test_image_is_embedded_and_size_limited(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "a.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
        cfg = load(write_cfg("cards:\n  - type: image\n    src: a.png\n    caption: hi\n", folder=d))
        self.assertIn("data:image/png;base64,", svg_of(cfg))
        with open(os.path.join(d, "big.png"), "wb") as f:
            f.write(b"0" * 500_000)
        with self.assertRaises(ConfigError):
            load(write_cfg("cards:\n  - type: image\n    src: big.png\n", folder=d))
        with open(os.path.join(d, "x.exe"), "wb") as f:
            f.write(b"MZ")
        with self.assertRaises(ConfigError):
            load(write_cfg("cards:\n  - type: image\n    src: x.exe\n", folder=d))


class RenderTests(unittest.TestCase):
    def tearDown(self):
        metrics.set_font("sora")

    def test_every_card_under_every_theme_and_font(self):
        for font in ("sora", "system", "serif", "mono"):
            for theme in themes.THEMES:
                with self.subTest(font=font, theme=theme):
                    cfg = load(write_cfg(f"theme: {theme}\nstyle: {{font: {font}}}\n" + KITCHEN_SINK))
                    ET.fromstring(svg_of(cfg))

    def test_style_options_change_output(self):
        cards = "cards:\n  - {type: streak, label: Streak}\n  - {type: number, value: hi, color: ocean}\n"
        base = svg_of(load(write_cfg(cards)))
        for style in ("shadow: true", "grain: true", "corners: sharp", "pattern: dots", "border: false",
                      "background: transparent", "background: ['#000000', '#222222']", "background: ocean",
                      "gap: 4, padding: 0", "mesh_blur: 1.5", "gloss: false", "border: '#ff0000'",
                      "border_width: 4", "text_case: upper"):
            with self.subTest(style=style):
                svg = svg_of(load(write_cfg("style: {" + style + "}\n" + card("streak"))))
                ET.fromstring(svg)
                self.assertNotEqual(svg, base)

    def test_card_overrides(self):
        cfg = load(write_cfg(
            "cards:\n  - {type: stack, items: [a], bg: '#ffcc00', fg: '#112233', radius: 5, border: '#ff0000',"
            " pattern: grid, pattern_opacity: 0.3}\n  - {type: streak, bg: [ '#000000', '#ffffff' ], bg_angle: 90}\n"
            "  - {type: streak, color: ocean}\n  - {type: streak, border: none}\n"
        ))
        svg = svg_of(cfg)
        ET.fromstring(svg)
        for needle in ("#ffcc00", "#112233", "#ff0000", "patternUnits"):
            self.assertIn(needle, svg)

    def test_text_color_adapts_to_custom_backgrounds(self):
        light = svg_of(load(write_cfg("cards:\n  - {type: ring, value: 1, label: LABEL1, bg: '#ffffff'}\n")))
        dark = svg_of(load(write_cfg("cards:\n  - {type: ring, value: 1, label: LABEL1, bg: '#000000'}\n")))
        self.assertIn('fill="#0b0b0c"', light.split("LABEL1")[0].rsplit("<text", 1)[1])
        self.assertIn('fill="#ffffff"', dark.split("LABEL1")[0].rsplit("<text", 1)[1])

    def test_text_case(self):
        cfg = load(write_cfg("style: {text_case: upper}\ncards:\n  - {type: ring, value: 1, label: Hello}\n  - type: commit\n"))
        svg = svg_of(cfg)
        self.assertIn("HELLO", svg)
        self.assertNotIn("Hello", svg)
        self.assertIn("ADD DAILY STATS", svg)

    def test_non_embedded_fonts_skip_the_font_file_and_pin_big_text(self):
        sora = svg_of(load(write_cfg("cards:\n  - {type: number, value: 42, label: x}\n")))
        mono = svg_of(load(write_cfg("style: {font: mono}\ncards:\n  - {type: number, value: 42, label: x}\n")))
        self.assertIn("font/woff2", sora)
        self.assertNotIn("font/woff2", mono)
        self.assertIn("textLength", mono)
        self.assertLess(len(mono), len(sora) / 3)

    def test_heatmap_and_empty_data(self):
        cfg = load(write_cfg("cards:\n  - {type: heatmap}\n  - type: repos\n  - type: languages\n  - type: streak\n"))
        ET.fromstring(svg_of(cfg, stats.empty("me")))


class SafetyTests(unittest.TestCase):
    def test_untrusted_text_cannot_inject_markup(self):
        evil = '<script>alert(1)</script> & "quotes" \x00\x08'
        cfg = load(write_cfg(KITCHEN_SINK))
        data = stats.demo()
        data["now"] = {"repo": evil, "message": evil, "when": evil}
        data["languages"] = [[evil, 100.0]]
        data["top_repos"] = [{"name": evil, "stars": 1, "language": evil}]
        svg = svg_of(cfg, data)
        ET.fromstring(svg)
        self.assertNotIn("<script", svg)

    def test_untrusted_config_text_is_escaped(self):
        cfg = load(write_cfg("alt: 'x\" onload=\"alert(1)'\ncards:\n  - {type: text, body: '</text><script>x</script>'}\n"))
        svg = svg_of(cfg)
        ET.fromstring(svg)
        self.assertNotIn("<script", svg)
        self.assertNotIn('onload="alert', svg)

    def test_long_text_is_fitted_not_overflowing(self):
        cfg = load(write_cfg(
            "cards:\n  - type: hero\n    title: " + "W" * 80 + "\n    headline: [" + "m" * 60 + "]\n"
            "  - type: stack\n    items: [" + ", ".join("tool%d" % i for i in range(60)) + "]\n"
        ))
        ET.fromstring(svg_of(cfg))


class BuildTests(unittest.TestCase):
    def test_auto_theme_writes_both_files_and_snippet(self):
        p = write_cfg("theme: auto\noutput: out/b.svg\ncards:\n  - type: streak\n")
        cfg = load(p)
        files = render.build(cfg, stats.demo(), os.path.dirname(p))
        self.assertEqual([os.path.basename(f) for f in files], ["b-dark.svg", "b-light.svg"])
        self.assertIn("prefers-color-scheme: dark", render.readme_snippet(cfg))

    def test_single_theme_writes_one_file(self):
        p = write_cfg("theme: nord\ncards:\n  - type: streak\n")
        cfg = load(p)
        self.assertEqual(len(render.build(cfg, stats.demo(), os.path.dirname(p))), 1)
        self.assertIn('<img src="./bento.svg"', render.readme_snippet(cfg))

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

    def test_every_example_is_a_valid_init_template(self):
        for name in EXAMPLE_NAMES:
            with self.subTest(template=name):
                self.assertIn(name, cli.TEMPLATES)

    def test_empty_stats_render_without_fake_data(self):
        cfg = load(write_cfg("cards:\n  - type: commit\n  - type: languages\n  - type: streak\n"))
        svg = svg_of(cfg, stats.empty("me"))
        ET.fromstring(svg)
        self.assertIn("no recent public", svg)  # wraps onto two lines
        self.assertNotIn("my-project", svg)

    def test_cache_roundtrip(self):
        d = tempfile.mkdtemp()
        stats.save_cache(stats.demo("me"), d)
        self.assertEqual(stats.load_cache(d)["username"], "me")

    def test_demo_calendar_is_deterministic(self):
        self.assertEqual(stats.demo()["calendar"], stats.demo()["calendar"])
        self.assertEqual(len(stats.demo()["calendar"]), 53)


if __name__ == "__main__":
    unittest.main()
