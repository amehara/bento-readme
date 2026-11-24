"""Colour data: card palettes, light/dark themes, accent gradients, brand colours."""

# A palette is a "mesh gradient" card: a base colour, blurred blobs on top and the
# ink colour used for text so it always stays readable.
PALETTES = {
    "sunset": {"base": "#ff8a00", "blobs": ["#ffd60a", "#ff6a00", "#ffcc00", "#ff9500"], "ink": "#0b0b0c"},
    "aurora": {"base": "#2a1066", "blobs": ["#5e5ce6", "#d6247f", "#ff5e3a", "#ff3b30"], "ink": "#ffffff"},
    "meadow": {"base": "#30d158", "blobs": ["#ffd60a", "#a8ff78", "#d4fc79", "#30d158"], "ink": "#0b0b0c"},
    "grape": {"base": "#5b1480", "blobs": ["#ff2dd4", "#ff2d55", "#bf5af2", "#ff2dd4"], "ink": "#ffffff"},
    "lime": {"base": "#d4fc79", "blobs": ["#30d158", "#ffd60a", "#64d2ff", "#ffffff"], "ink": "#0b0b0c"},
    "candy": {"base": "#fff1f6", "blobs": ["#ffc2e0", "#b9c6ff", "#ffcf8a", "#ff9ec4"], "ink": "#0b0b0c"},
    "ocean": {"base": "#0a3d91", "blobs": ["#64d2ff", "#5e5ce6", "#30d0c8", "#0a84ff"], "ink": "#ffffff"},
    "ember": {"base": "#c1121f", "blobs": ["#ff9500", "#ff2d55", "#ffd60a", "#ff3b30"], "ink": "#ffffff"},
    "sky": {"base": "#bfe3ff", "blobs": ["#ffffff", "#c8b6ff", "#9be7ff", "#a0c4ff"], "ink": "#0b0b0c"},
    "mono": {"base": "#1c1c1e", "blobs": ["#3a3a3c", "#636366", "#2c2c2e", "#48484a"], "ink": "#ffffff"},
}

# Text gradients usable as `accent:`.
GRADIENTS = {
    "pink": [(0, "#ff2d92"), (0.55, "#ff7a45"), (1, "#ffc400")],
    "blue": [(0, "#64d2ff"), (0.55, "#7d7aff"), (1, "#ff5fa8")],
    "green": [(0, "#30d158"), (0.55, "#a8ff78"), (1, "#ffd60a")],
    "violet": [(0, "#bf5af2"), (0.55, "#5e5ce6"), (1, "#64d2ff")],
    "seg": [(0, "#64d2ff"), (1, "#bf5af2")],
}

THEMES = {
    "dark": {
        "canvas": "#000000",
        "card": "#161618",
        "card_strong": "#111113",
        "text": "#ffffff",
        "text_soft": "#e5e5ea",
        "muted": "#a1a1a6",
        "stroke": "#ffffff",
        "stroke_opacity": 0.12,
        "gloss": 0.10,
        "off": "#3a3a3c",
        "chip": "#ffffff",
        "chip_opacity": 0.12,
        "divider_opacity": 0.14,
    },
    "light": {
        "canvas": "#f2f2f7",
        "card": "#ffffff",
        "card_strong": "#ffffff",
        "text": "#0b0b0c",
        "text_soft": "#3a3a3c",
        "muted": "#6e6e73",
        "stroke": "#000000",
        "stroke_opacity": 0.08,
        "gloss": 0.0,
        "off": "#d1d1d6",
        "chip": "#000000",
        "chip_opacity": 0.06,
        "divider_opacity": 0.10,
    },
}

# Brand colours for stack chips / language bars. Unknown names get a neutral dot.
TECH_COLORS = {
    "typescript": "#3178c6", "javascript": "#f7df1e", "python": "#ffd43b", "java": "#f89820",
    "kotlin": "#a97bff", "swift": "#f05138", "go": "#00add8", "rust": "#dea584", "c": "#aaaaaa",
    "c++": "#f34b7d", "c#": "#68217a", "ruby": "#cc342d", "php": "#777bb4", "dart": "#00b4ab",
    "html": "#e34c26", "css": "#563d7c", "scss": "#c6538c", "shell": "#89e051", "lua": "#51a0ff",
    "react": "#61dafb", "next.js": "#ffffff", "vue": "#42b883", "svelte": "#ff3e00", "angular": "#dd0031",
    "astro": "#ff5d01", "node": "#5fa04e", "node.js": "#5fa04e", "deno": "#70ffaf", "bun": "#fbf0df",
    "tailwind": "#38bdf8", "figma": "#ff7262", "framer": "#0055ff", "blender": "#ea7600",
    "docker": "#2496ed", "kubernetes": "#326ce5", "postgres": "#4169e1", "postgresql": "#4169e1",
    "mysql": "#00758f", "mongodb": "#47a248", "redis": "#dc382d", "graphql": "#e10098",
    "supabase": "#3ecf8e", "firebase": "#ffca28", "aws": "#ff9900", "vercel": "#ffffff",
    "git": "#f05032", "linux": "#fcc624", "vim": "#019733", "unity": "#ffffff", "godot": "#478cbf",
    "three.js": "#ffffff", "gsap": "#88ce02", "remotion": "#0b84f3", "sass": "#cc6699",
    "jupyter notebook": "#da5b0b", "vue.js": "#42b883",
}

FALLBACK_DOT = "#8e8e93"
