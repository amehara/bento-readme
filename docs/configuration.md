# Configuration reference

Everything lives in one file, `bento.yml` (or `.json`). Check it any time with `python -m bento validate -c bento.yml`: errors name the exact card and key, and suggest fixes for typos.

```yaml
github:
  user: octocat            # defaults to the repository owner when run in the Action
output: bento.svg          # relative path, must end in .svg
alt: bento grid about me   # accessible description of the image
theme: dark                # a name, "auto", [dark, light] or an inline theme (see Themes)
themes: {}                 # your own named themes
style: {}                  # global look: corners, shadow, font, grain... (see Style)
palettes: {}               # your own mesh palettes
gradients: {}              # your own text gradients
cards: []                  # the grid, in order
```

- [Your GitHub profile in the texts](#your-github-profile-in-the-texts)
- [The grid](#the-grid)
- [Themes](#themes)
- [Style](#style)
- [Card options shared by every card](#options-every-card-accepts)
- [Cards](#cards)
- [Colors, gradients and custom palettes](#colors)
- [Fonts and languages](#fonts-and-languages)
- [Data sources](#data-sources)

## Your GitHub profile in the texts

Any text can pull from your GitHub profile. Quote the value so YAML keeps the braces.

| Placeholder | Value |
| --- | --- |
| `{name}` | Your display name (or your username if you have none) |
| `{first_name}` | The first word of your name |
| `{login}` | Your username |
| `{bio}`, `{location}`, `{company}`, `{blog}` | The matching profile fields |
| `{bio\|fallback}` | The value, or `fallback` when it is empty |

```yaml
- type: hero
  title: "{name}"
  subtitle: "@{login}"
  headline: ["hi, i'm", "{first_name}"]
- type: text
  body: "{bio|i build things and share them here.}"
```

Unknown placeholders are left exactly as typed. With **no `bento.yml` at all**, readme-bento uses a built-in config made of these placeholders ([`bento/data/default.yml`](../bento/data/default.yml)); copy it to `bento.yml` to start customizing.

## The grid

The canvas is 1200 px wide with **4 columns**. A card's `size` is `COLSxROWS`:

- `1x1` is one cell, `2x1` is two cells wide, `1x2` is two cells tall, `2x2` is a big block.
- Rows can be half-height: `4x0.5` is a slim band.
- Cards are placed in the order you list them, each in the first free spot, so small cards fill any gaps. If the grid looks uneven, reorder the cards or add a small one to fill the hole.
- A row is always 232 px tall. `style.gap` and `style.padding` change the spacing around it.
- By default the image has a **transparent background and no outer margin**, so only the cards show and they line up with your README text. Use `style.background` to put something behind them.

## Themes

A theme is the set of colors for the canvas, cards and text. **15 are built in** (see the [gallery](themes.md)):

`dark` · `light` · `midnight` · `nord` · `dracula` · `solarized-dark` · `solarized-light` · `catppuccin-mocha` · `catppuccin-latte` · `github-dark` · `github-light` · `rose-pine` · `paper` · `terminal` · `brutalist`

```yaml
theme: nord                      # one theme
theme: auto                      # dark + light: writes bento-dark.svg and bento-light.svg
theme: [dracula, solarized-light]   # your own dark/light pair, same two files
```

**Tweak a theme** by giving a mapping with a `base` plus the colors you want to change:

```yaml
theme:
  base: nord
  card: "#3b4252"
  text: "#ffffff"
  stroke: "#88c0d0"
  stroke_opacity: 0.5
```

**Define your own named themes** and reuse them (also inside a pair):

```yaml
themes:
  brand:
    base: dark
    canvas: "#0b1020"
    card: "#131a2e"
    text: "#e8ecff"
theme: [brand, paper]
```

| Key | Type | Meaning |
| --- | --- | --- |
| `base` | theme name | Start from this theme (default `dark`). |
| `canvas` | hex | Background behind all cards, used when `style.background: theme`. |
| `card`, `card_strong` | hex | Card fill. `card_strong` is used by hero / commit / plain number cards. |
| `text`, `text_soft`, `muted` | hex | Main, secondary and label text. |
| `stroke` | hex | Border color. |
| `off` | hex | Inactive bars and empty heatmap cells. |
| `chip` | hex | Tint of the stack chips. |
| `stroke_opacity`, `gloss`, `chip_opacity`, `divider_opacity` | 0-1 | Strengths of those effects. |

You only need to set what you want to change; `text_soft`, `muted`, `off` and `card_strong` are derived from `card` and `text` when you do not set them.

## Style

Global look, applied to every card. All keys are optional.

```yaml
style:
  corners: soft          # round | soft | sharp | a number of pixels (0-60, 36 is the default)
  gap: 16                # space between cards, 0-40
  padding: 0             # space around the grid, 0-64 (0 with a transparent background, 24 otherwise)
  shadow: true           # drop shadow under cards (true, false or 0-1)
  border: true           # true | false | a hex color
  border_width: 1        # 0-8
  border_opacity: 0.12   # overrides the theme's border strength
  gloss: true            # soft highlight on top of cards (true, false or 0-2)
  grain: 0.1             # film grain over everything (true, false or 0-0.5)
  pattern: dots          # none | dots | grid | lines | grain on every card
  pattern_opacity: 0.1
  background: transparent  # transparent (default) | theme | hex | palette name | [hex, hex]
  mesh_blur: 1           # softness of mesh gradients, 0.3-2
  font: sora             # sora | system | serif | mono
  text_case: keep        # keep | lower | upper
```

Some ideas:

| Look | Style |
| --- | --- |
| Soft & airy | `corners: soft`, `shadow: true`, `gap: 20` |
| Brutalist | `theme: brutalist`, `corners: 0`, `border_width: 3`, `gloss: false` |
| Retro terminal | `theme: terminal`, `font: mono`, `corners: 0`, `pattern: lines` |
| Film poster | `grain: 0.12`, `background: [ "#12002b", "#000000" ]` |
| Solid canvas behind the cards | `background: theme` (uses the theme's `canvas` color) |
| Floating cards with shadows | `shadow: true` (adds a margin so the shadow is not cut) |
| Lowercase aesthetic | `text_case: lower` |

## Options every card accepts

Besides its own keys, every card takes these. They override the theme and `style` for that card only.

| Key | Description |
| --- | --- |
| `size` | `COLSxROWS`, see [The grid](#the-grid). Each card type supports a range of sizes. |
| `color` | A [palette](#colors) name. Turns the card into a colorful mesh gradient. |
| `bg` | The background: a hex color (`"#ffcc00"`), a palette name, or a list of 2-4 hex colors for a linear gradient. |
| `bg_angle` | Angle in degrees of a gradient `bg` (default 135). |
| `fg` | Text color. When you do not set it, the text color is chosen automatically for contrast with `bg`. |
| `radius` | Corner radius in pixels (0-120). |
| `border` | `none`, `true` or a hex color. |
| `pattern`, `pattern_opacity` | `dots`, `grid`, `lines`, `grain` or `none`, and its strength (0-1). |

```yaml
- type: stack
  items: [python, rust]
  bg: ["#ff9a9e", "#a18cd1"]   # gradient background; text turns dark or light by itself
  radius: 8
  pattern: dots
```

## Cards

### `hero`

Name, role, intro and a giant headline. Sizes: columns 2-4, rows 1 or 2 (the headline needs 2 rows).

| Key | Description |
| --- | --- |
| `title` | Big name at the top. |
| `subtitle` | Role or tagline under it. |
| `intro` | One or two lines of small text. In YAML `[a, b]` is two lines; quote an item that contains a comma. |
| `headline` | One or two giant words or phrases that fill the width. |
| `accent` | Gradient for the last headline line (default `pink`). |

### `number`

A big number or word. Sizes: columns 1-2, rows 1-2. Give it either `source` (live data) or `value` (any text).

| Key | Description |
| --- | --- |
| `source` | `contributions`, `streak`, `repos`, `stars`, `followers` or `lines`. |
| `value` | Any text, e.g. `"2+"` or `":3"`. Quote it so YAML keeps it a string. |
| `style` | `mesh` (default, colorful gradient), `outline` (always 2 rows tall; defaults to `1x2`) or `plain` (card with gradient digits). |
| `label` | `mesh`: one or two lines at the bottom (`[line one, line two]`). `outline`: the title at the bottom. `plain`: small text at the top. |
| `caption` | `outline` only: the small line under the label. |
| `eyebrow` | `outline` only: small text at the top. |
| `minis` | `plain` only: up to three small stats at the bottom, e.g. `[repos, stars, followers]`. |
| `accent` | Gradient of the digits in `plain` (default `blue`). |

### `streak`

Current contribution streak and a bar for each of the last 20 days. Size: columns 1-2, 1 row.
Keys: `label` (default `current streak`), `unit` (default `days`), `accent` (default `seg`).

### `commit`

Your latest public commit with a pulsing "live" dot. Size: columns 2-4, 1 row. Key: `label` (default `now · last commit`).

### `status`

A toggle plus a big word. Size: columns 1-2, rows 1-2.
Keys: `word` (default `on`/`off`), `on` (`true`/`false`, moves the knob), `caption`.

### `stack`

Chips with a colored dot. Size: columns 1-4, rows 1-2. Chips that do not fit become a `+n` chip.
Keys: `label` (default `stack`), `items`, `chip_style` (`dot` default, `filled` or `outline`).
Each item is a name (`typescript`) or `{name: custom, color: "#ff0066"}`. About 60 technologies have built-in brand colors; others get a neutral dot.

### `languages`

Your most used languages across your repos, as a bar and a legend. Size: columns 1-4, rows 1-2.
Keys: `label` (default `top languages`), `limit` (max rows shown).

### `repos`

Your most starred public repositories. Size: columns 1-2, rows 1-2. Private and archived repositories are never listed.
Keys: `label` (default `top repos · stars`), `limit`.

### `heatmap`

Your contribution calendar as a grid of squares. Size: columns 1-4, 1 row.
Keys: `label`, `weeks` (4-53, default: as many as fit), `accent` (the first color of the gradient is used; default `green`).

### `ring`

A progress ring with a percentage. Size: columns 1-2, rows 1-2.
Keys: `value` (0-100), `label`, `caption`, `accent` (default `seg`).

### `bars`

Horizontal progress bars, handy for skills. Size: columns 1-2, rows 1-2.
Keys: `label` (default `skills`), `accent`, `items`: a list of `"Name: 80"` strings or `{name: Name, value: 80}`.

### `text`

Free text. Size: columns 1-4, rows 1-2.
Keys: `title`, `body` (wraps and ends with `…` if too long), `author`, `style` (`plain`, or `quote` for big text).

### `contact`

Label and value pairs, for links and handles. Size: columns 1-2, rows 1-2.
Keys: `label` (default `find me`), `items`: a list of `"Label: value"` strings or `{label: ..., value: ...}`.
SVGs cannot hold clickable links; put real links in Markdown under the image.

### `image`

A picture from your repository. Size: columns 1-4, rows 1-2.
Keys: `src` (relative path next to `bento.yml`), `fit` (`cover` default or `contain`), `caption`.
PNG, JPG, GIF, WebP or SVG up to 400 KB. The file is embedded in the SVG, so keep it small.

### `cta`

A big call to action with an arrow button. Size: columns 2-4, 1 row. Keys: `text`, `caption`.

### `band`

A slim banner, usually the last card. Size: columns 2-4, rows `0.5` or `1`.
Keys: `text`, `show_updated` (default `true`), `updated_label` (default `updated`).

## Colors

Built-in palettes for `color` (and `bg`), see the [gallery](themes.md#palettes):

`sunset` · `aurora` · `meadow` · `grape` · `lime` · `candy` · `ocean` · `ember` · `sky` · `mono` · `lavender` · `peach` · `forest` · `mint` · `rose` · `gold` · `ice` · `cherry` · `slate` · `coral` · `neon` · `cotton` · `mocha` · `lagoon` · `frost`

Each is a base color with blurred blobs of other colors, plus an `ink` color chosen for contrast with the text.

**Gradients** for `accent`: `pink` · `blue` · `green` · `violet` · `seg` · `sunset` · `ocean` · `fire` · `mint` · `candy` · `gold` · `mono`. Or pass your own list: `accent: ["#ff0066", "#ffcc00"]`.

### Custom palettes and gradients

```yaml
palettes:
  brand:
    base: "#0b3d2e"
    blobs: ["#2dd4a8", "#a3e635", "#0ea5e9"]
    ink: "#ffffff"       # text color on top of this palette

gradients:
  laser: ["#00e5ff", "#ff00e5"]

cards:
  - type: number
    value: "42"
    label: answers
    color: brand
    accent: laser
```

Colors are hex values (`#rrggbb` or `#rgb`). Use a light `ink` on dark palettes and a dark one on light palettes.

## Fonts and languages

`style.font` picks the typeface:

| Font | Notes |
| --- | --- |
| `sora` (default) | Embedded in the SVG, so it looks identical everywhere. Covers Latin characters with accents (`áéíóúñü`, `ç`, `ß`...). |
| `system` | The viewer's system UI font. |
| `serif` | A serif stack (New York / Georgia / Times). |
| `mono` | A monospaced stack (SF Mono / JetBrains Mono / Consolas...). |

Only Sora is embedded; the others are used if the viewer's system has them and fall back to a similar font otherwise, so small details can differ between devices. Giant texts keep a fixed width on every system. The SVG is also about 40 KB smaller without the embedded font.

Characters outside Sora's set (CJK, emoji, `→`, `—`) fall back to the viewer's system font. Long text shrinks to fit its card and is cut with `…` as a last resort.

## Data sources

| Source | Where it comes from |
| --- | --- |
| `contributions`, `streak`, `followers`, `heatmap` | GitHub GraphQL contributions calendar |
| `repos`, `stars` | Your own, non-fork repositories |
| `lines` | Lines you added across your 40 most recently pushed repos (never decreases) |
| `commit` card | Latest push in your public events |
| `languages` | Bytes per language across those repos |
| `repos` card | Your public repositories sorted by stars (private ones are excluded) |

Anything that fails to load keeps its previous value from `.bento/stats.json`, so a bad day on the GitHub API never blanks your profile. Commit that file along with the SVG (the Action does it for you).
