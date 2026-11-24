"use strict";

/* bento-readme web configurator.
 * The page keeps ONE object (`cfg`) that mirrors bento.yml. The form edits it, the YAML box shows it,
 * and the real Python engine (running in the browser through Pyodide) turns it into the preview. */

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const PLACEHOLDER_USER = "your-github-username";
const MAX_LINK = 7000; // GitHub links with a pre-filled file stop working when they get too long

const WORKFLOW = `name: update bento

on:
  schedule:
    - cron: "17 4 * * *"   # every day at 04:17 UTC
  workflow_dispatch:         # run it by hand from the Actions tab
  push:
    branches: [main]
    paths: ["bento.yml"]

permissions:
  contents: write

jobs:
  bento:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amehara/bento-readme@v1
`;

/* ------------------------------------------------------------------ i18n */
const I18N = {
  en: {
    repo: "GitHub", title: "Build your GitHub bento",
    subtitle: "Pick a style, make it yours and watch it change live. Nothing to install, no code.",
    h_start: "Start from", h_you: "About you", h_look: "Look", h_cards: "Cards", h_yaml: "Advanced: edit the config file",
    h_preview: "Live preview", h_install: "Put it on your profile",
    f_user: "Your GitHub username",
    user_hint: "We use it to fill in your name and bio. Your real numbers appear once it is installed.",
    user_found: "Found {name}. Your name and bio are used in the preview.", user_missing: "We could not find that user on GitHub.",
    f_theme: "Theme", f_font: "Font", f_corners: "Corners", f_case: "Text case", f_pattern: "Texture", f_shadow: "Shadows",
    f_grain: "Film grain", f_gap: "Spacing", f_padding: "Margin", add: "Add card",
    yaml_hint: "This is the file the buttons write. You can paste an existing bento.yml here to keep editing it.",
    preview_hint: "The numbers are samples. Yours are filled in automatically every day.",
    foot: "Free and open source (MIT). It runs entirely in your browser: nothing you type here is sent anywhere, except your username to GitHub to read your public profile.",
    loading: "Loading the engine… the first time takes a few seconds.", ready: "Ready", rendering: "Updating…",
    load_error: "The engine could not be loaded. Check your connection and reload the page.",
    yaml_ok: "Applied.", yaml_bad: "That is not valid YAML yet: {msg}",
    custom: "custom (see YAML)", auto: "auto (follows light/dark)", none: "none", keep: "as typed", lower: "lowercase", upper: "UPPERCASE",
    round: "round", soft: "soft", sharp: "sharp", variant_dark: "Dark", variant_light: "Light",
    move_up: "Move up", move_down: "Move down", remove: "Remove", theme_default: "theme color", source_custom: "my own text",
    preset_profile: "My profile (automatic)", preset_designer: "Designer", preset_developer: "Developer", preset_minimal: "Minimal",
    preset_neon: "Neon", preset_editorial: "Editorial", preset_terminal: "Terminal", preset_pastel: "Pastel",
    size: "Size", color: "Color",
    t_hero: "Hero (name and headline)", t_number: "Big number", t_streak: "Contribution streak", t_commit: "Latest commit",
    t_status: "Status toggle", t_stack: "Tech stack", t_languages: "Top languages", t_cta: "Call to action", t_band: "Footer band",
    t_text: "Text or quote", t_contact: "Contact list", t_heatmap: "Contribution calendar", t_repos: "Top repositories",
    t_bars: "Skill bars", t_ring: "Progress ring",
    k_title: "Title", k_subtitle: "Subtitle", k_intro: "Intro (one line each)", k_headline: "Giant headline (1-2 lines)",
    k_source: "Show", k_value: "Text", k_label: "Label (one line each)", k_style: "Style", k_word: "Big word", k_caption: "Caption",
    k_items: "Items", k_items_csv: "Items (separated by commas)", k_items_pairs: "Items (one per line, like \"Mail: me@example.com\")",
    k_items_bars: "Skills (one per line, like \"Python: 80\")", k_text: "Text", k_body: "Text", k_author: "Author", k_value_num: "Percentage (0-100)",
    s_contributions: "Contributions", s_streak: "Streak", s_repos: "Repositories", s_stars: "Stars", s_followers: "Followers", s_lines: "Lines of code",
    st_mesh: "Colorful", st_outline: "Outline (tall)", st_plain: "Plain",
    i_need_user: "Type your GitHub username above to get your personalized install steps.",
    i_s1_t: "Create your profile repository", i_s1_p: "It must be public and named exactly like your username ({user}). If you already have it, skip this step.",
    i_s1_b: "Create the repository",
    i_s2_t: "Add the updater", i_s2_p: "A small file that refreshes your bento every day. On GitHub just press the green \"Commit changes\" button.",
    i_s3_t: "Add your design", i_s3_p: "This file holds everything you chose here. Press \"Commit changes\" again.",
    i_s3_zero: "You do not need this step: with \"My profile (automatic)\" your bento is built from your GitHub profile. You can come back later to customize it.",
    i_open: "Open on GitHub with the file ready", i_copy: "Copy", i_copied: "Copied", i_download: "Download", i_show: "Show the file",
    i_long: "This file is too long for a one-click link. Use Copy, then create the file on GitHub and paste it.",
    i_manual: "If the page opens empty, use Copy and paste the text yourself.",
    i_s4_t: "Run it once", i_s4_p: "Open the Actions page, choose \"update bento\" and press \"Run workflow\". Within a minute your bento file appears in the repository.",
    i_s4_b: "Open Actions",
    i_s5_t: "Show it on your profile", i_s5_p: "Edit your repository's README.md and paste this where you want the bento to appear.",
    i_s5_b: "Edit README.md",
  },
  es: {
    repo: "GitHub", title: "Crea tu bento de GitHub",
    subtitle: "Elige un estilo, hazlo tuyo y míralo cambiar en directo. Sin instalar nada y sin código.",
    h_start: "Empieza con", h_you: "Sobre ti", h_look: "Aspecto", h_cards: "Tarjetas", h_yaml: "Avanzado: editar el archivo de configuración",
    h_preview: "Vista previa en vivo", h_install: "Ponlo en tu perfil",
    f_user: "Tu usuario de GitHub",
    user_hint: "Lo usamos para rellenar tu nombre y tu bio. Tus números reales aparecen cuando esté instalado.",
    user_found: "Encontrado: {name}. Usamos tu nombre y tu bio en la vista previa.", user_missing: "No encontramos ese usuario en GitHub.",
    f_theme: "Tema", f_font: "Fuente", f_corners: "Esquinas", f_case: "Mayúsculas", f_pattern: "Textura", f_shadow: "Sombras",
    f_grain: "Grano de película", f_gap: "Separación", f_padding: "Margen", add: "Añadir tarjeta",
    yaml_hint: "Este es el archivo que escriben los botones. Puedes pegar aquí un bento.yml existente para seguir editándolo.",
    preview_hint: "Los números son de ejemplo. Los tuyos se rellenan solos cada día.",
    foot: "Gratis y de código abierto (MIT). Funciona entero en tu navegador: nada de lo que escribes aquí se envía a ningún sitio, salvo tu usuario a GitHub para leer tu perfil público.",
    loading: "Cargando el motor… la primera vez tarda unos segundos.", ready: "Listo", rendering: "Actualizando…",
    load_error: "No se pudo cargar el motor. Revisa tu conexión y recarga la página.",
    yaml_ok: "Aplicado.", yaml_bad: "Todavía no es un YAML válido: {msg}",
    custom: "personalizado (ver YAML)", auto: "auto (sigue claro/oscuro)", none: "ninguna", keep: "como se escribe", lower: "minúsculas", upper: "MAYÚSCULAS",
    round: "redondas", soft: "suaves", sharp: "rectas", variant_dark: "Oscuro", variant_light: "Claro",
    move_up: "Subir", move_down: "Bajar", remove: "Quitar", theme_default: "color del tema", source_custom: "mi propio texto",
    preset_profile: "Mi perfil (automático)", preset_designer: "Diseñador", preset_developer: "Desarrollador", preset_minimal: "Mínimo",
    preset_neon: "Neón", preset_editorial: "Editorial", preset_terminal: "Terminal", preset_pastel: "Pastel",
    size: "Tamaño", color: "Color",
    t_hero: "Principal (nombre y titular)", t_number: "Número grande", t_streak: "Racha de contribuciones", t_commit: "Último commit",
    t_status: "Interruptor de estado", t_stack: "Tecnologías", t_languages: "Lenguajes más usados", t_cta: "Llamada a la acción", t_band: "Banda final",
    t_text: "Texto o cita", t_contact: "Lista de contacto", t_heatmap: "Calendario de contribuciones", t_repos: "Repositorios destacados",
    t_bars: "Barras de habilidades", t_ring: "Anillo de progreso",
    k_title: "Título", k_subtitle: "Subtítulo", k_intro: "Introducción (una línea por renglón)", k_headline: "Titular gigante (1-2 líneas)",
    k_source: "Mostrar", k_value: "Texto", k_label: "Etiqueta (una línea por renglón)", k_style: "Estilo", k_word: "Palabra grande", k_caption: "Pie",
    k_items: "Elementos", k_items_csv: "Elementos (separados por comas)", k_items_pairs: "Elementos (uno por línea, como \"Correo: yo@ejemplo.com\")",
    k_items_bars: "Habilidades (una por línea, como \"Python: 80\")", k_text: "Texto", k_body: "Texto", k_author: "Autor", k_value_num: "Porcentaje (0-100)",
    s_contributions: "Contribuciones", s_streak: "Racha", s_repos: "Repositorios", s_stars: "Estrellas", s_followers: "Seguidores", s_lines: "Líneas de código",
    st_mesh: "Colorido", st_outline: "Contorno (alto)", st_plain: "Sencillo",
    i_need_user: "Escribe arriba tu usuario de GitHub para ver tus pasos de instalación personalizados.",
    i_s1_t: "Crea tu repositorio de perfil", i_s1_p: "Tiene que ser público y llamarse exactamente como tu usuario ({user}). Si ya lo tienes, salta este paso.",
    i_s1_b: "Crear el repositorio",
    i_s2_t: "Añade el actualizador", i_s2_p: "Un archivo pequeño que refresca tu bento cada día. En GitHub solo pulsa el botón verde \"Commit changes\".",
    i_s3_t: "Añade tu diseño", i_s3_p: "Este archivo guarda todo lo que elegiste aquí. Pulsa de nuevo \"Commit changes\".",
    i_s3_zero: "No necesitas este paso: con \"Mi perfil (automático)\" tu bento se crea a partir de tu perfil de GitHub. Puedes volver luego a personalizarlo.",
    i_open: "Abrir en GitHub con el archivo listo", i_copy: "Copiar", i_copied: "Copiado", i_download: "Descargar", i_show: "Ver el archivo",
    i_long: "Este archivo es demasiado largo para un enlace de un clic. Usa Copiar, crea el archivo en GitHub y pégalo.",
    i_manual: "Si la página se abre vacía, usa Copiar y pega el texto tú mismo.",
    i_s4_t: "Ejecútalo una vez", i_s4_p: "Abre la página de Actions, elige \"update bento\" y pulsa \"Run workflow\". En un minuto aparece tu archivo de bento en el repositorio.",
    i_s4_b: "Abrir Actions",
    i_s5_t: "Muéstralo en tu perfil", i_s5_p: "Edita el README.md de tu repositorio y pega esto donde quieras que aparezca el bento.",
    i_s5_b: "Editar README.md",
  },
};

let lang = (new URLSearchParams(location.search).get("lang") || localStorage.getItem("bento-lang") || navigator.language || "en").slice(0, 2);
if (!I18N[lang]) lang = "en";
const t = (key, vars = {}) =>
  (I18N[lang][key] ?? I18N.en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : `{${k}}`));

/* ------------------------------------------------------------ card editing */
const SOURCES = ["contributions", "streak", "repos", "stars", "followers", "lines"];
const F = (key, kind, extra = {}) => ({ key, kind, ...extra });
const FIELDS = {
  hero: [F("title", "text"), F("subtitle", "text"), F("intro", "lines"), F("headline", "lines")],
  number: [F("source", "source"), F("value", "text"), F("label", "lines"), F("style", "select", { options: ["mesh", "outline", "plain"], prefix: "st_" })],
  streak: [], commit: [], languages: [], repos: [], heatmap: [],
  status: [F("word", "text"), F("caption", "text")],
  stack: [F("items", "csv")],
  cta: [F("text", "text"), F("caption", "text")],
  band: [F("text", "text")],
  text: [F("title", "text"), F("body", "area"), F("author", "text")],
  contact: [F("label", "text"), F("items", "lines", { labelKey: "k_items_pairs" })],
  bars: [F("label", "text"), F("items", "lines", { labelKey: "k_items_bars" })],
  ring: [F("value", "num"), F("label", "text"), F("caption", "text")],
};
const NEW_CARD = {
  hero: { type: "hero", size: "2x2", title: "your name", subtitle: "what you do", intro: ["a short line about you."], headline: ["hello,", "world."] },
  number: { type: "number", source: "contributions", label: ["contributions", "this year"], color: "ocean" },
  streak: { type: "streak" }, commit: { type: "commit" }, languages: { type: "languages" }, repos: { type: "repos" },
  heatmap: { type: "heatmap" },
  status: { type: "status", word: "open", caption: "for new projects", color: "meadow" },
  stack: { type: "stack", items: ["python", "javascript", "git"] },
  cta: { type: "cta", text: "let's talk", caption: "i reply to everything", color: "lime" },
  band: { type: "band", text: "thanks for stopping by.", color: "candy" },
  text: { type: "text", title: "about", body: "A few words about what you do and what you love." },
  contact: { type: "contact", label: "find me", items: ["Mail: you@example.com", "Web: example.com"] },
  bars: { type: "bars", label: "skills", items: ["Design: 90", "Code: 75"] },
  ring: { type: "ring", value: 70, label: "learning", caption: "this year" },
};
const ORDER = ["hero", "number", "streak", "heatmap", "commit", "languages", "repos", "stack", "status", "ring", "bars", "text", "contact", "cta", "band"];

/* -------------------------------------------------------------- app state */
let cfg = { github: {}, theme: "dark", cards: [] };
let schema = null;
let api = null;
let preset = "profile";
let dirty = false;
let renderToken = 0;
let activeVariant = 0;
let lastResult = null;
let profile = {};
let blobUrl = null;

const $ = (id) => document.getElementById(id);
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (v === true) n.setAttribute(k, "");
    else if (v !== false && v != null) n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) n.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return n;
}
const debounce = (fn, ms) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };

function ensure() {
  if (!cfg || typeof cfg !== "object" || Array.isArray(cfg)) cfg = {};
  if (!cfg.github || typeof cfg.github !== "object") cfg.github = {};
  if (!Array.isArray(cfg.cards)) cfg.cards = [];
  if (cfg.style && typeof cfg.style !== "object") delete cfg.style;
}
function yamlText() {
  return "# bento.yml · made with bento-readme\n" + jsyaml.dump(cfg, { lineWidth: 100, noRefs: true });
}
function touch(structural = false) {
  dirty = true;
  if (structural) renderCards();
  syncYaml();
  schedulePreview();
}
function setStyle(key, value, dflt) {
  cfg.style = cfg.style || {};
  if (value === dflt || value === "" || value === false) delete cfg.style[key]; else cfg.style[key] = value;
  if (!Object.keys(cfg.style).length) delete cfg.style;
  touch();
}

/* ---------------------------------------------------------------- controls */
function option(value, text, selected) { return el("option", { value, selected: !!selected }, text); }

function fillSelect(sel, items, current, customLabel) {
  sel.replaceChildren();
  let found = false;
  for (const [v, label] of items) { const on = v === current; found = found || on; sel.append(option(v, label, on)); }
  if (!found) sel.append(option("__custom", customLabel || t("custom"), true));
}

function renderStyleControls() {
  const st = cfg.style || {};
  const themeValue = typeof cfg.theme === "string" ? cfg.theme : (cfg.theme === undefined ? "dark" : "__custom");
  fillSelect($("theme"), [["auto", t("auto")], ...schema.themes.map((n) => [n, n])], themeValue);
  fillSelect($("font"), ["sora", "system", "serif", "mono"].map((n) => [n, n]), st.font || "sora");
  const corners = st.corners === undefined ? "round" : st.corners;
  fillSelect($("corners"), [["round", t("round")], ["soft", t("soft")], ["sharp", t("sharp")]], corners, `${st.corners}px`);
  fillSelect($("text_case"), [["keep", t("keep")], ["lower", t("lower")], ["upper", t("upper")]], st.text_case || "keep");
  fillSelect($("pattern"), [["none", t("none")], ["dots", "dots"], ["grid", "grid"], ["lines", "lines"], ["grain", "grain"]], st.pattern || "none");
  $("shadow").checked = !!st.shadow;
  $("grain").checked = !!st.grain;
  $("gap").value = st.gap ?? 16; $("gap-out").textContent = `${st.gap ?? 16}px`;
  $("padding").value = st.padding ?? 24; $("padding-out").textContent = `${st.padding ?? 24}px`;
}

function bindStyleControls() {
  const pick = (id, key, dflt) => $(id).addEventListener("change", (e) => {
    if (e.target.value !== "__custom") setStyle(key, e.target.value, dflt);
  });
  $("theme").addEventListener("change", (e) => {
    if (e.target.value === "__custom") return;
    cfg.theme = e.target.value; touch();
  });
  pick("font", "font", "sora"); pick("corners", "corners", "round"); pick("text_case", "text_case", "keep"); pick("pattern", "pattern", "none");
  $("shadow").addEventListener("change", (e) => setStyle("shadow", e.target.checked, false));
  $("grain").addEventListener("change", (e) => setStyle("grain", e.target.checked ? 0.1 : false, false));
  $("gap").addEventListener("input", (e) => { $("gap-out").textContent = `${e.target.value}px`; setStyle("gap", +e.target.value, 16); });
  $("padding").addEventListener("input", (e) => { $("padding-out").textContent = `${e.target.value}px`; setStyle("padding", +e.target.value, 24); });
}

function sizeOptions(spec) {
  const info = schema.cards[spec.type];
  if (!info) return [];
  const rows = spec.type === "number" && spec.style === "outline" ? [2] : info.rows;
  const out = [];
  for (let c = info.cols[0]; c <= info.cols[1]; c++) for (const r of rows) out.push(`${c}x${r}`);
  return out;
}

function fieldValue(spec, f) {
  const v = spec[f.key];
  if (v == null) return "";
  if (f.kind === "lines") return (Array.isArray(v) ? v : [v]).map((x) => (typeof x === "object" ? `${x.name ?? x.label}: ${x.value ?? ""}` : x)).join("\n");
  if (f.kind === "csv") return (Array.isArray(v) ? v : [v]).map((x) => (typeof x === "object" ? x.name : x)).join(", ");
  return String(v);
}
function writeField(spec, f, raw) {
  const key = f.key;
  if (f.kind === "lines") {
    const lines = raw.split("\n").map((s) => s.trim()).filter(Boolean);
    if (lines.length) spec[key] = lines; else delete spec[key];
  } else if (f.kind === "csv") {
    const old = Array.isArray(spec[key]) ? spec[key] : [];
    const names = raw.split(",").map((s) => s.trim()).filter(Boolean);
    spec[key] = names.map((n) => old.find((o) => typeof o === "object" && o.name === n) || n);
  } else if (f.kind === "num") {
    const n = Number(raw);
    if (raw === "" || Number.isNaN(n)) delete spec[key]; else spec[key] = Math.max(0, Math.min(100, n));
  } else if (raw === "") delete spec[key]; else spec[key] = raw;
}

function labelFor(f) {
  if (f.labelKey) return t(f.labelKey);
  if (f.kind === "csv") return t("k_items_csv");
  if (f.kind === "num") return t("k_value_num");
  return t(`k_${f.key}`);
}

function fieldControl(spec, f) {
  const label = labelFor(f);
  if (f.kind === "source") {
    const sel = el("select", {}, option("", t("source_custom"), !spec.source), ...SOURCES.map((s) => option(s, t(`s_${s}`), spec.source === s)));
    sel.addEventListener("change", () => { if (sel.value) { spec.source = sel.value; delete spec.value; } else delete spec.source; touch(true); });
    return el("label", { class: "field" }, el("span", {}, label), sel);
  }
  if (f.kind === "select") {
    const cur = spec[f.key] || f.options[0];
    const sel = el("select", {}, ...f.options.map((o) => option(o, t(f.prefix + o), cur === o)));
    sel.addEventListener("change", () => {
      spec[f.key] = sel.value;
      if (f.key === "style" && sel.value === "outline") delete spec.size; // outline cards are always 2 rows tall
      touch(true);
    });
    return el("label", { class: "field" }, el("span", {}, label), sel);
  }
  const multi = f.kind === "lines" || f.kind === "area";
  const input = multi
    ? el("textarea", { rows: f.kind === "area" ? 3 : 2, spellcheck: "false" })
    : el("input", { type: f.kind === "num" ? "number" : "text", ...(f.kind === "num" ? { min: 0, max: 100 } : {}) });
  input.value = fieldValue(spec, f);
  input.addEventListener("input", () => { writeField(spec, f, input.value); touch(false); });
  return el("label", { class: "field" }, el("span", {}, label), input);
}

function cardTitle(spec) {
  const hint = spec.title || spec.text || spec.word || spec.body || (Array.isArray(spec.headline) ? spec.headline.join(" ") : "") ||
    (spec.value != null ? String(spec.value) : "") || spec.source || "";
  return hint ? `${hint}`.slice(0, 40) : "";
}

function renderCards() {
  const box = $("cards");
  const open = new Set([...box.querySelectorAll("details[open]")].map((d) => d.dataset.i));
  box.replaceChildren();
  cfg.cards.forEach((spec, i) => {
    const known = !!FIELDS[spec.type] || !!(schema.cards[spec.type]);
    const move = (d) => () => { const j = i + d; [cfg.cards[i], cfg.cards[j]] = [cfg.cards[j], cfg.cards[i]]; touch(true); };
    const body = el("div", { class: "card-body" });
    const sizes = sizeOptions(spec);
    if (sizes.length) {
      const dflt = schema.cards[spec.type].size;
      const cur = String(spec.size || (spec.type === "number" && spec.style === "outline" ? "1x2" : dflt));
      const sel = el("select", {}, ...sizes.map((s) => option(s, s, s === cur)));
      if (!sizes.includes(cur)) sel.append(option(cur, cur, true));
      sel.addEventListener("change", () => { if (sel.value === dflt) delete spec.size; else spec.size = sel.value; touch(false); });
      body.append(el("label", { class: "field" }, el("span", {}, t("size")), sel));
    }
    for (const f of FIELDS[spec.type] || []) body.append(fieldControl(spec, f));
    if (schema.cards[spec.type] && spec.type !== "image") {
      const colors = el("select", {}, option("", t("theme_default"), !spec.color), ...schema.palettes.map((p) => option(p, p, spec.color === p)));
      if (spec.color && !schema.palettes.includes(spec.color)) colors.append(option(spec.color, spec.color, true));
      colors.addEventListener("change", () => { if (colors.value) spec.color = colors.value; else delete spec.color; touch(false); });
      body.append(el("label", { class: "field" }, el("span", {}, t("color")), colors));
    }
    const d = el("details", { class: "card-item", "data-i": String(i) },
      el("summary", {},
        el("span", { class: "name" }, known ? t(`t_${spec.type}`) : String(spec.type), " ", el("span", { class: "tag" }, cardTitle(spec))),
        el("button", { type: "button", class: "icon-btn", title: t("move_up"), "aria-label": t("move_up"), disabled: i === 0, onclick: (e) => { e.preventDefault(); move(-1)(); } }, "↑"),
        el("button", { type: "button", class: "icon-btn", title: t("move_down"), "aria-label": t("move_down"), disabled: i === cfg.cards.length - 1, onclick: (e) => { e.preventDefault(); move(1)(); } }, "↓"),
        el("button", { type: "button", class: "icon-btn danger", title: t("remove"), "aria-label": t("remove"), onclick: (e) => { e.preventDefault(); cfg.cards.splice(i, 1); touch(true); } }, "×"),
      ),
      body);
    if (open.has(String(i))) d.open = true;
    box.append(d);
  });
}

function renderAddSelect() {
  const sel = $("add-type");
  sel.replaceChildren(...ORDER.filter((k) => schema.cards[k]).map((k) => option(k, t(`t_${k}`))));
}

/* ------------------------------------------------------------------ YAML box */
function syncYaml() {
  const box = $("yaml");
  if (document.activeElement !== box) box.value = yamlText();
}
const onYamlInput = debounce(() => {
  try {
    const parsed = jsyaml.load($("yaml").value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("the file must contain settings, like theme: dark");
    cfg = parsed; ensure(); dirty = true;
    $("yaml-status").textContent = t("yaml_ok");
    $("user").value = userFromCfg();
    renderAll(false);
    schedulePreview();
  } catch (e) {
    $("yaml-status").textContent = t("yaml_bad", { msg: String(e.message || e).split("\n")[0] });
  }
}, 400);

function userFromCfg() {
  const u = cfg.github && cfg.github.user;
  return u && u !== PLACEHOLDER_USER ? String(u) : "";
}

/* ----------------------------------------------------------------- presets */
async function loadPreset(name) {
  const res = await fetch(`presets/${name}.yml`);
  if (!res.ok) return;
  const keep = $("user").value.trim();
  cfg = jsyaml.load(await res.text());
  ensure();
  preset = name; dirty = false;
  if (keep) cfg.github.user = keep; else delete cfg.github.user;
  document.querySelectorAll("#presets .chip").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.name === name)));
  renderAll(true);
  schedulePreview();
}

/* ----------------------------------------------------------------- preview */
const schedulePreview = debounce(runPreview, 180);

async function runPreview() {
  if (!api) return;
  const token = ++renderToken;
  $("status").textContent = t("rendering");
  await new Promise((r) => setTimeout(r, 0)); // let the browser paint before the (synchronous) render
  let res;
  try { res = JSON.parse(api.preview(yamlText(), JSON.stringify(profile))); } catch (e) { res = { error: String(e) }; }
  if (token !== renderToken) return;
  const err = $("error");
  if (res.error) { err.textContent = res.error; err.hidden = false; $("status").textContent = ""; return; }
  err.hidden = true;
  lastResult = res;
  if (activeVariant >= res.files.length) activeVariant = 0;
  showVariant();
  renderVariantButtons();
  $("status").textContent = t("ready");
  renderInstall();
}
function showVariant() {
  const f = lastResult.files[activeVariant];
  if (blobUrl) URL.revokeObjectURL(blobUrl);
  blobUrl = URL.createObjectURL(new Blob([f.svg], { type: "image/svg+xml" }));
  $("preview").src = blobUrl;
}
function renderVariantButtons() {
  const box = $("variants");
  const files = lastResult.files;
  box.hidden = files.length < 2;
  box.replaceChildren(...files.map((f, i) => el("button", {
    type: "button", "aria-pressed": String(i === activeVariant),
    onclick: () => { activeVariant = i; showVariant(); renderVariantButtons(); },
  }, f.variant === "dark" ? t("variant_dark") : f.variant === "light" ? t("variant_light") : f.variant)));
}

/* ----------------------------------------------------------------- install */
function copyButton(text) {
  const b = el("button", { type: "button", class: "secondary" }, t("i_copy"));
  b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(text); b.textContent = t("i_copied"); setTimeout(() => (b.textContent = t("i_copy")), 1500); }
    catch { /* clipboard blocked: the file is also shown below */ }
  });
  return b;
}
function download(name, text) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const a = el("a", { href: url, download: name, class: "btn plain" }, t("i_download"));
  return a;
}
function fileStep(title, desc, user, folder, filename, text) {
  const base = `https://github.com/${encodeURIComponent(user)}/${encodeURIComponent(user)}/new/main`;
  const path = folder ? `/${folder}` : "";
  const link = `${base}${path}?filename=${encodeURIComponent(filename)}&value=${encodeURIComponent(text)}`;
  const tooLong = link.length > MAX_LINK;
  const kids = [el("h3", {}, title), el("p", {}, desc), el("div", { class: "row" })];
  const row = kids[2];
  if (!tooLong) row.append(el("a", { class: "btn", href: link, target: "_blank", rel: "noopener" }, t("i_open")));
  row.append(copyButton(text), download(filename, text));
  kids.push(el("p", { class: "hint" }, tooLong ? "" : t("i_manual")));
  if (tooLong) kids.push(el("p", { class: "warn" }, t("i_long")));
  kids.push(el("details", {}, el("summary", {}, t("i_show"), ` (${folder ? folder + "/" : ""}${filename})`), el("pre", {}, text)));
  return el("li", { class: "step" }, ...kids);
}

function renderInstall() {
  const box = $("install-body");
  const user = $("user").value.trim();
  if (!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/.test(user)) { box.replaceChildren(el("p", { class: "empty" }, t("i_need_user"))); return; }
  const zero = preset === "profile" && !dirty;
  const steps = [];
  steps.push(el("li", { class: "step" }, el("h3", {}, t("i_s1_t")), el("p", {}, t("i_s1_p", { user })),
    el("div", { class: "row" }, el("a", { class: "btn", target: "_blank", rel: "noopener",
      href: `https://github.com/new?name=${encodeURIComponent(user)}&visibility=public` }, t("i_s1_b")))));
  steps.push(fileStep(t("i_s2_t"), t("i_s2_p"), user, ".github/workflows", "bento.yml", WORKFLOW));
  if (zero) steps.push(el("li", { class: "step" }, el("h3", {}, t("i_s3_t")), el("p", { class: "ok" }, t("i_s3_zero"))));
  else {
    const c = JSON.parse(JSON.stringify(cfg));
    c.github = { ...(c.github || {}), user };
    steps.push(fileStep(t("i_s3_t"), t("i_s3_p"), user, "", "bento.yml", "# bento.yml · made with bento-readme\n" + jsyaml.dump(c, { lineWidth: 100, noRefs: true })));
  }
  steps.push(el("li", { class: "step" }, el("h3", {}, t("i_s4_t")), el("p", {}, t("i_s4_p")),
    el("div", { class: "row" }, el("a", { class: "btn", target: "_blank", rel: "noopener",
      href: `https://github.com/${encodeURIComponent(user)}/${encodeURIComponent(user)}/actions/workflows/bento.yml` }, t("i_s4_b")))));
  const snippet = lastResult ? lastResult.snippet : "";
  steps.push(el("li", { class: "step" }, el("h3", {}, t("i_s5_t")), el("p", {}, t("i_s5_p")), el("pre", {}, snippet),
    el("div", { class: "row" }, copyButton(snippet), el("a", { class: "btn plain", target: "_blank", rel: "noopener",
      href: `https://github.com/${encodeURIComponent(user)}/${encodeURIComponent(user)}/edit/main/README.md` }, t("i_s5_b")))));
  box.replaceChildren(el("ol", { class: "steps" }, ...steps));
}

/* ----------------------------------------------------------------- profile */
const lookupProfile = debounce(async () => {
  const user = $("user").value.trim();
  const hint = $("user-hint");
  profile = {};
  if (!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/.test(user)) { hint.textContent = t("user_hint"); schedulePreview(); return; }
  try {
    const r = await fetch(`https://api.github.com/users/${encodeURIComponent(user)}`, { signal: AbortSignal.timeout(6000) });
    if (!r.ok) throw new Error("not found");
    const u = await r.json();
    profile = { name: u.name || "", login: u.login || "", bio: u.bio || "", location: u.location || "", company: u.company || "", blog: u.blog || "" };
    hint.textContent = t("user_found", { name: u.name || u.login });
  } catch { hint.textContent = t("user_missing"); }
  schedulePreview();
}, 600);

/* -------------------------------------------------------------------- boot */
function renderAll(structural) {
  renderStyleControls();
  renderCards();
  syncYaml();
  if (structural) $("user").value = userFromCfg() || $("user").value;
}

function applyTexts() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.dataset.i18n); });
  $("lang").textContent = lang === "es" ? "EN" : "ES";
  const chips = $("presets");
  if (chips.children.length) chips.querySelectorAll(".chip").forEach((b) => { b.textContent = t(`preset_${b.dataset.name}`); });
}

async function boot() {
  applyTexts();
  $("lang").addEventListener("click", () => {
    lang = lang === "es" ? "en" : "es"; localStorage.setItem("bento-lang", lang);
    applyTexts();
    if (schema) {
      renderAddSelect(); renderAll(false); renderInstall();
      if (lastResult) { renderVariantButtons(); $("status").textContent = t("ready"); }
    }
  });
  $("status").textContent = t("loading");
  try {
    const py = await loadPyodide({ indexURL: PYODIDE_URL });
    await py.loadPackage("pyyaml");
    const files = await (await fetch("py/manifest.json")).json();
    await Promise.all(files.map(async (rel) => {
      const buf = new Uint8Array(await (await fetch(`py/${rel}`)).arrayBuffer());
      const full = `/home/pyodide/${rel}`;
      py.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
      py.FS.writeFile(full, buf);
    }));
    py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
    api = py.pyimport("webapi");
    schema = JSON.parse(api.schema());
  } catch (e) {
    console.error(e);
    $("status").textContent = ""; $("error").textContent = t("load_error"); $("error").hidden = false;
    return;
  }

  const names = await (await fetch("presets/index.json")).json();
  $("presets").replaceChildren(...names.map((n) => el("button", {
    type: "button", class: "chip", "data-name": n, "aria-pressed": "false", onclick: () => loadPreset(n),
  }, t(`preset_${n}`))));
  renderAddSelect();
  bindStyleControls();
  $("add").addEventListener("click", () => { cfg.cards.push(JSON.parse(JSON.stringify(NEW_CARD[$("add-type").value]))); touch(true); });
  $("yaml").addEventListener("input", onYamlInput);
  $("user").addEventListener("input", () => {
    const u = $("user").value.trim();
    if (u) cfg.github.user = u; else delete cfg.github.user;
    syncYaml(); renderInstall(); lookupProfile();
  });
  await loadPreset(new URLSearchParams(location.search).get("preset") || "profile");
}

boot();
