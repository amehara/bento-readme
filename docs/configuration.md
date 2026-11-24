# Configuration reference

Everything lives in one file, `bento.yml` (or `.json`). Check it any time with `python -m bento validate -c bento.yml`: errors name the exact card and key, and suggest fixes for typos.

```yaml
github:
  user: octocat          # defaults to the repository owner when run in the Action
output: bento.svg        # relative path, must end in .svg
theme: dark              # dark | light | auto
alt: bento grid about me # accessible description of the image
palettes: {}             # optional custom palettes, see below
cards: []                # the grid, in order
```

| Key | Default | Notes |
| --- | --- | --- |
| `github.user` | repository owner | Whose stats to show. Leave the placeholder `your-github-username` and the build uses demo data. |
| `output` | `bento.svg` | With `theme: auto`, `bento-dark.svg` and `bento-light.svg` are written instead. |
| `theme` | `dark` | `auto` writes both and prints a `<picture>` snippet that follows the visitor's theme. |
| `alt` | `bento grid about <user>` | Read by screen readers. |

## The grid

The canvas is 1200 px wide with **4 columns**. A card's `size` is `COLSxROWS`:

- `1x1` is one cell, `2x1` is two cells wide, `1x2` is two cells tall, `2x2` is a big block.
- Rows can be half-height: `4x0.5` is a slim band.
- Cards are placed in the order you list them, each in the first free spot, so small cards fill any gaps. If the grid looks uneven, reorder the cards.

Every card also accepts `color` where it makes sense (a palette name). Unknown keys are rejected with a suggestion.

## Cards

### `hero`

Name, role, intro and a giant headline. Sizes: columns 2-4, rows 1 or 2 (the headline needs 2 rows).

| Key | Description |
| --- | --- |
| `title` | Big name at the top. |
| `subtitle` | Role or tagline under it. |
| `intro` | One or two lines of small text. In YAML, `[a, b]` is two lines. |
| `headline` | One or two giant words or phrases that fill the width. |
| `accent` | Gradient for the last headline line: `pink` (default), `blue`, `green`, `violet`. |

### `number`

A big number or word. Sizes: columns 1-2, rows 1-2. Give it either `source` (live data) or `value` (any text).

| Key | Description |
| --- | --- |
| `source` | `contributions`, `streak`, `repos`, `stars`, `followers` or `lines`. |
| `value` | Any text, e.g. `"2+"` or `":3"`. Quote it so YAML keeps it a string. |
| `style` | `mesh` (default, colorful gradient), `outline` (always 2 rows tall; defaults to `1x2`) or `plain` (dark card with gradient digits). |
| `label` | `mesh`: one or two lines at the bottom (`[line one, line two]`). `outline`: the title at the bottom. `plain`: small text at the top. |
| `caption` | `outline` only: the small line under the label. |
| `eyebrow` | `outline` only: small text at the top. |
| `minis` | `plain` only: up to three small stats at the bottom, e.g. `[repos, stars, followers]`. |
| `color` | Palette for `mesh` and `outline`. Defaults: `sunset` / `aurora`. |
| `accent` | Gradient of the digits in `plain` (default `blue`). |

### `streak`

Current contribution streak and a bar for each of the last 20 days. Size: columns 1-2, 1 row.
Keys: `label` (default `current streak`), `unit` (default `days`), `accent` (default `seg`; also `pink`, `blue`, `green`, `violet`).

### `commit`

Your latest public commit with a pulsing "live" dot. Size: columns 2-4, 1 row. Key: `label` (default `now · last commit`).

### `status`

A toggle plus a big word. Size: columns 1-2, rows 1-2.
Keys: `word` (default `on`/`off`), `on` (`true`/`false`, moves the knob), `caption`, `color` (default `meadow`).

### `stack`

Chips with a colored dot. Size: columns 1-4, rows 1-2. Chips that do not fit become a `+n` chip.
Keys: `label` (default `stack`), `items`. Each item is a name (`typescript`) or `{name: custom, color: "#ff0066"}`. About 60 technologies have built-in brand colors; others get a neutral dot.

### `languages`

Your most used languages across your repos, as a bar and a legend. Size: columns 1-4, rows 1-2.
Keys: `label` (default `top languages`), `limit` (max rows shown).

### `cta`

A big call to action with an arrow button. Size: columns 2-4, 1 row.
Keys: `text`, `caption`, `color` (default `lime`). SVGs cannot hold links; put the link in Markdown below the image.

### `band`

A slim banner, usually the last card. Size: columns 2-4, rows `0.5` or `1`.
Keys: `text`, `color` (default `candy`), `show_updated` (default `true`), `updated_label` (default `updated`).

## Colors

Built-in palettes for the `color` key:

`sunset` · `aurora` · `meadow` · `grape` · `lime` · `candy` · `ocean` · `ember` · `sky` · `mono`

Each is a base color with blurred blobs of other colors, plus an `ink` color chosen for contrast with the text.

### Custom palettes

```yaml
palettes:
  brand:
    base: "#0b3d2e"
    blobs: ["#2dd4a8", "#a3e635", "#0ea5e9"]
    ink: "#ffffff"       # text color on top of this palette

cards:
  - type: number
    value: "42"
    label: answers
    color: brand
```

All colors must be 6-digit hex values. Use a light `ink` on dark palettes and a dark one on light palettes.

## Fonts and languages

Text uses the embedded **Sora** font, which covers Latin characters including accents (`áéíóúñü`, `ç`, `ß`, ...). Characters outside that set (CJK, emoji, `→`, `—`) fall back to the viewer's system font, so they render but may not fit as tightly. Long text shrinks to fit its card and is cut with `…` as a last resort.

## Data sources

| Source | Where it comes from |
| --- | --- |
| `contributions`, `streak`, `followers` | GitHub GraphQL contributions calendar |
| `repos`, `stars` | Your own, non-fork repositories |
| `lines` | Lines you added across your 40 most recently pushed repos (never decreases) |
| `commit` card | Latest push in your public events |
| `languages` | Bytes per language across those repos |

Anything that fails to load keeps its previous value from `.bento/stats.json`, so a bad day on the GitHub API never blanks your profile. Commit that file along with the SVG (the Action does it for you).
