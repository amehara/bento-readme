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
    "lavender": {"base": "#b9a7ff", "blobs": ["#e0d4ff", "#8fb0ff", "#ffc8f0", "#c7b8ff"], "ink": "#0b0b0c"},
    "peach": {"base": "#ffb4a2", "blobs": ["#ffd6a5", "#ff8fa3", "#ffe5d9", "#ffcdb2"], "ink": "#0b0b0c"},
    "forest": {"base": "#0b3d2e", "blobs": ["#1b9e77", "#a3e635", "#0e7c66", "#2d6a4f"], "ink": "#ffffff"},
    "mint": {"base": "#b7f5d8", "blobs": ["#e6fff3", "#7ee8c8", "#c9f7a5", "#8de5ff"], "ink": "#0b0b0c"},
    "rose": {"base": "#ff6b9d", "blobs": ["#ffb3c7", "#ff3d7f", "#ffd1dc", "#c86dd7"], "ink": "#0b0b0c"},
    "gold": {"base": "#f5b700", "blobs": ["#ffe066", "#ff9f1c", "#fff3b0", "#e09f00"], "ink": "#0b0b0c"},
    "ice": {"base": "#d7f0ff", "blobs": ["#ffffff", "#a5d8ff", "#e0e7ff", "#b8f2e6"], "ink": "#0b0b0c"},
    "cherry": {"base": "#8b0a30", "blobs": ["#e63962", "#ff6b6b", "#5c0a26", "#c9184a"], "ink": "#ffffff"},
    "slate": {"base": "#334155", "blobs": ["#64748b", "#475569", "#94a3b8", "#1e293b"], "ink": "#ffffff"},
    "coral": {"base": "#ff6f61", "blobs": ["#ffb88c", "#ff3d68", "#ffd6c9", "#ff8a5c"], "ink": "#0b0b0c"},
    "neon": {"base": "#0a0a0a", "blobs": ["#00ffa3", "#ff00e5", "#00d1ff", "#ffee00"], "ink": "#ffffff"},
    "cotton": {"base": "#ffe4f2", "blobs": ["#cfe8ff", "#fff5ba", "#d4ffe6", "#ffd1ec"], "ink": "#0b0b0c"},
    "mocha": {"base": "#3b2a24", "blobs": ["#a47551", "#d9a066", "#6f4e37", "#c68b59"], "ink": "#ffffff"},
    "lagoon": {"base": "#006d77", "blobs": ["#83c5be", "#00b4d8", "#e29578", "#48cae4"], "ink": "#ffffff"},
    "frost": {"base": "#e5e5ea", "blobs": ["#ffffff", "#d1d1d6", "#f2f2f7", "#c7c7cc"], "ink": "#0b0b0c"},
}

# Text gradients usable as `accent:`.
GRADIENTS = {
    "pink": [(0, "#ff2d92"), (0.55, "#ff7a45"), (1, "#ffc400")],
    "blue": [(0, "#64d2ff"), (0.55, "#7d7aff"), (1, "#ff5fa8")],
    "green": [(0, "#30d158"), (0.55, "#a8ff78"), (1, "#ffd60a")],
    "violet": [(0, "#bf5af2"), (0.55, "#5e5ce6"), (1, "#64d2ff")],
    "seg": [(0, "#64d2ff"), (1, "#bf5af2")],
    "sunset": [(0, "#ff512f"), (1, "#dd2476")],
    "ocean": [(0, "#00c6ff"), (1, "#0072ff")],
    "fire": [(0, "#f12711"), (1, "#f5af19")],
    "mint": [(0, "#11998e"), (1, "#38ef7d")],
    "candy": [(0, "#ff9a9e"), (1, "#a18cd1")],
    "gold": [(0, "#f7971e"), (1, "#ffd200")],
    "mono": [(0, "#ffffff"), (1, "#8e8e93")],
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
