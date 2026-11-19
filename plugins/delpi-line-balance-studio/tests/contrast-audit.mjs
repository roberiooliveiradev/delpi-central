import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = fileURLToPath(new URL("../preview-dist/", import.meta.url));
const origin = "https://studio.test/delpi-central/";
const contentTypes = { ".js": "text/javascript", ".css": "text/css", ".html": "text/html" };
const executablePath = process.env.LBS_CHROMIUM_EXECUTABLE;
const browser = await chromium.launch(executablePath
  ? { executablePath, args: ["--single-process", "--no-zygote"] }
  : {});
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 }, colorScheme: "light" });
  await page.route(origin + "**", async route => {
    const name = route.request().url().slice(origin.length) || "index.html";
    await route.fulfill({ path: path.join(root, name), contentType: contentTypes[path.extname(name)] });
  });
  await page.goto(origin);
  const host = page.locator("delpi-line-balance-studio");
  /* Fluxo OBSERVED — cobre badges de proveniência e o painel M1 oficial. */
  await host.getByRole("button", { name: /Produto DELPI/ }).click();
  await host.locator("#lb-product-code").fill("90264302");
  await host.getByRole("button", { name: "Buscar roteiro" }).click();
  const stageTrigger = host.getByRole("combobox", { name: "Estágio produtivo", exact: true });
  await stageTrigger.waitFor();
  await stageTrigger.click();
  await host.getByRole("listbox").getByRole("option", { name: "Estágio 10 · Montagem" }).click();
  await host.getByRole("heading", { name: "Yamazumi" }).waitFor();
  /* Estado com impedimentos de análise para medir o aviso warning (painel M1). */
  await host.getByRole("button", { name: /M1 · Capacidade e takt/ }).click();
  await host.getByRole("heading", { name: "Capacidade e takt" }).waitFor();
  await host.evaluate(element => {
    element.analysisState = { phase: "idle", issues: ["Demanda por turno ausente."] };
  });
  await host.locator(".analysis-issues").waitFor();

  const results = [];
  for (const theme of ["light", "dark"]) {
    await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
    await page.waitForTimeout(400);
    const measured = await host.evaluate(() => {
      const shadow = document.querySelector("delpi-line-balance-studio").shadowRoot;
      const oklabToSrgb = (L, a, b, alpha = 1) => {
        const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
        const m_ = L - 0.1055613458 * a - 0.0638541729 * b;
        const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
        const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
        const lr = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
        const lg = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
        const lb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
        const gamma = c => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055) * 255;
        const clamp = c => Math.min(255, Math.max(0, c));
        return { r: clamp(gamma(lr)), g: clamp(gamma(lg)), b: clamp(gamma(lb)), a: alpha };
      };
      const alphaOf = raw => raw == null ? 1 : (raw.endsWith("%") ? Number(raw.slice(0, -1)) / 100 : Number(raw));
      const parseFunctional = value => {
        const v = value.trim();
        let m = /^color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+%?))?\)$/i.exec(v);
        if (m) return { r: Number(m[1]) * 255, g: Number(m[2]) * 255, b: Number(m[3]) * 255, a: alphaOf(m[4]) };
        m = /^oklab\(\s*([\d.]+%?)\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s*\/\s*([\d.]+%?))?\s*\)$/i.exec(v);
        if (m) {
          const L = m[1].endsWith("%") ? Number(m[1].slice(0, -1)) / 100 : Number(m[1]);
          return oklabToSrgb(L, Number(m[2]), Number(m[3]), alphaOf(m[4]));
        }
        m = /^oklch\(\s*([\d.]+%?)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+%?))?\s*\)$/i.exec(v);
        if (m) {
          const L = m[1].endsWith("%") ? Number(m[1].slice(0, -1)) / 100 : Number(m[1]);
          const h = Number(m[3]) * Math.PI / 180;
          return oklabToSrgb(L, Number(m[2]) * Math.cos(h), Number(m[2]) * Math.sin(h), alphaOf(m[4]));
        }
        return null;
      };
      const colorContext = document.createElement("canvas").getContext("2d");
      const normalize = value => {
        const functional = parseFunctional(value);
        if (functional) return functional;
        colorContext.fillStyle = "#000";
        colorContext.fillStyle = value;
        const resolved = colorContext.fillStyle;
        const viaCanvas = parseFunctional(resolved);
        if (viaCanvas) return viaCanvas;
        const match = /rgba?\(([^)]+)\)/.exec(resolved);
        if (match) {
          const [r, g, b, a = 1] = match[1].split(",").map(Number);
          return { r, g, b, a };
        }
        const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?$/i.exec(resolved);
        if (!hex) return null;
        return { r: parseInt(hex[1], 16), g: parseInt(hex[2], 16), b: parseInt(hex[3], 16), a: hex[4] ? parseInt(hex[4], 16) / 255 : 1 };
      };
      const parse = normalize;
      const blend = (fg, bg) => ({
        r: fg.r * fg.a + bg.r * (1 - fg.a),
        g: fg.g * fg.a + bg.g * (1 - fg.a),
        b: fg.b * fg.a + bg.b * (1 - fg.a),
      });
      const luminance = ({ r, g, b }) => {
        const channel = c => {
          const s = c / 255;
          return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
        };
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
      };
      const gradientStops = element => {
        const image = getComputedStyle(element).backgroundImage;
        if (!image || !image.startsWith("linear-gradient")) return [];
        const stops = [];
        for (const match of image.matchAll(/(rgba?\([^)]*\)|oklab\([^)]*\)|oklch\([^)]*\)|color\([^)]*\)|#[0-9a-fA-F]{3,8}\b)/g)) {
          const color = normalize(match[1]);
          if (color && color.a > 0) stops.push(color);
        }
        return stops;
      };
      const effectiveBackground = element => {
        const layers = [];
        let node = element;
        while (node) {
          if (node instanceof Element) {
            const bg = parse(getComputedStyle(node).backgroundColor);
            if (bg && bg.a > 0) layers.push(bg);
          }
          node = node.parentElement || node.getRootNode().host || null;
        }
        let color = { r: 255, g: 255, b: 255 };
        for (let index = layers.length - 1; index >= 0; index -= 1) color = blend(layers[index], color);
        return color;
      };
      const probe = (element, kind = "text") => {
        const style = getComputedStyle(element);
        const fgBase = parse(style.color) || { r: 0, g: 0, b: 0, a: 1 };
        const stops = gradientStops(element);
        /* Gradiente próprio cobre o elemento: os stops são o fundo efetivo,
         * ignorando as camadas ancestrais por baixo dele. */
        const backgrounds = stops.length ? stops : [effectiveBackground(element)];
        let worst = { ratio: Infinity, bg: backgrounds[0] };
        for (const bg of backgrounds) {
          const fg = blend(fgBase, bg);
          const raw = (luminance(fg) + 0.05) / (luminance(bg) + 0.05);
          const ordered = raw >= 1 ? raw : 1 / raw;
          if (ordered < worst.ratio) worst = { ratio: ordered, bg };
        }
        const ratio = worst.ratio;
        const bg = worst.bg;
        const fontSize = Number.parseFloat(style.fontSize);
        const fontWeight = Number.parseFloat(style.fontWeight) || 400;
        const largeText = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
        const min = kind === "icon" ? 3 : (largeText ? 3 : 4.5);
        return {
          ratio: Math.round(ratio * 100) / 100,
          min,
          fg: style.color,
          bg: `rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)})`,
          font: `${style.fontSize}/${style.fontWeight}`,
          label: element.textContent.trim().slice(0, 30),
        };
      };
      const out = {};
      const text = (key, selector, kind = "text") => {
        const target = shadow.querySelector(selector);
        out[key] = target ? probe(target, kind) : "MISSING";
      };
      text("study-title", ".study-head .study-title-row");
      text("study-sub", ".study-sub");
      text("section-title", ".delpi-ui-section-card__title");
      text("table-header", ".delpi-ui-table th");
      text("table-cell", ".delpi-ui-table td");
      text("rail-item", ".delpi-ui-tool-rail__name");
      text("rail-status", ".delpi-ui-tool-rail__status");
      text("kpi-value", ".delpi-ui-kpi-card strong");
      text("primary-btn", ".delpi-ui-action-btn--primary");
      text("secondary-btn", ".delpi-ui-action-btn:not(.delpi-ui-action-btn--primary)");
      text("field-label", ".delpi-ui-field-label__text");
      text("help-trigger", ".delpi-ui-help-tooltip__trigger--icon", "icon");
      text("analysis-issues", ".analysis-issues li");
      text("chart-footer", ".delpi-ui-stacked-column-chart__footer");
      text("scenario-label", ".scenario-control .delpi-ui-field-label__text, .scenario-control label");
      const badges = [...shadow.querySelectorAll(".delpi-ui-status-badge")];
      badges.forEach((badge, index) => { out[`badge-${index}`] = probe(badge); });
      const hintIcons = [...shadow.querySelectorAll(".delpi-ui-help-tooltip__trigger--icon")];
      hintIcons.forEach((icon, index) => { out[`help-icon-${index}`] = probe(icon, "icon"); });
      return out;
    });
    for (const [key, value] of Object.entries(measured)) results.push({ theme, key, ...value });
  }

  const failures = [];
  for (const entry of results) {
    if (entry.ratio === undefined) continue;
    if (entry.ratio < entry.min) failures.push(`${entry.theme}:${entry.key} ${entry.ratio} < ${entry.min} (fg=${entry.fg} bg=${entry.bg} "${entry.label}")`);
    console.log(`${entry.theme.padEnd(5)} ${entry.key.padEnd(16)} ${String(entry.ratio).padStart(6)} min=${entry.min} font=${entry.font} "${entry.label}"`);
  }
  assert.deepEqual(failures, []);
  console.log(`PASS contrast-audit: ${results.filter(r => r.ratio !== undefined).length} pairs medidos em light+dark — WCAG AA (4.5 texto / 3.0 texto grande & ícones)`);
} finally {
  await browser.close();
}
