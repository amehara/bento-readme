# Themes and palettes

How to use them: set `theme:` in your `bento.yml`, or `color:` on a card. See the [configuration reference](configuration.md#themes) for custom themes and palettes.

## Themes

Every image below is the same layout rendered with a different `theme`.

| | |
| --- | --- |
| **dark** `dark`<br><img src="img/theme-dark.svg" alt="dark theme"> | **light** `light`<br><img src="img/theme-light.svg" alt="light theme"> |
| **midnight**<br><img src="img/theme-midnight.svg" alt="midnight theme"> | **nord**<br><img src="img/theme-nord.svg" alt="nord theme"> |
| **dracula**<br><img src="img/theme-dracula.svg" alt="dracula theme"> | **rose-pine**<br><img src="img/theme-rose-pine.svg" alt="rose-pine theme"> |
| **catppuccin-mocha**<br><img src="img/theme-catppuccin-mocha.svg" alt="catppuccin-mocha theme"> | **catppuccin-latte**<br><img src="img/theme-catppuccin-latte.svg" alt="catppuccin-latte theme"> |
| **solarized-dark**<br><img src="img/theme-solarized-dark.svg" alt="solarized-dark theme"> | **solarized-light**<br><img src="img/theme-solarized-light.svg" alt="solarized-light theme"> |
| **github-dark**<br><img src="img/theme-github-dark.svg" alt="github-dark theme"> | **github-light**<br><img src="img/theme-github-light.svg" alt="github-light theme"> |
| **paper**<br><img src="img/theme-paper.svg" alt="paper theme"> | **brutalist**<br><img src="img/theme-brutalist.svg" alt="brutalist theme"> |
| **terminal**<br><img src="img/theme-terminal.svg" alt="terminal theme"> | |

Pair a dark and a light theme so your profile follows each visitor's GitHub appearance: `theme: [nord, solarized-light]`.

## Palettes

`color: <name>` on a card (or `bg: <name>`) gives it one of these mesh gradients. The text color is picked for contrast automatically.

<img src="img/palettes.svg" alt="all built-in palettes" width="100%">

## Regenerate these images

```bash
python tools/build_gallery.py
```
