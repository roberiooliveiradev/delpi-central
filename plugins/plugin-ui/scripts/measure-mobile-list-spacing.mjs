#!/usr/bin/env node
/**
 * Mede espaçamentos reais do chrome de lista operacional em viewport 375px.
 * Requer Docker (imagem zenika/alpine-chrome:with-puppeteer).
 *
 * Uso: node scripts/measure-mobile-list-spacing.mjs
 */
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const stylesDir = join(here, "../src/styles");
const outDir = "/tmp/delpi-ui-spacing";
mkdirSync(outDir, { recursive: true });

const cssFiles = [
  "card-shell.css",
  "section-card.css",
  "dashboard-filters.css",
  "data-list-toolbar.css",
  "interactive-data-card.css",
  "data-cards-grid.css",
];
const css = cssFiles.map((f) => readFileSync(join(stylesDir, f), "utf8")).join("\n");

const html = `<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=375, initial-scale=1">
<style>
:root { --delpi-ui-surface:#111; --delpi-ui-text:#eee; --delpi-ui-border:#333; --delpi-ui-accent:#089bdb; }
body { margin:0; font-family: system-ui; background:#0b0e14; color:#eee; }
</style>
<style>${css.replace(/<\/style>/gi, "<\\/style>")}</style>
</head><body>
<div class="delpi-ui-card delpi-ui-section-card" id="section">
  <div class="delpi-ui-section-card__header"><h2 class="delpi-ui-section-card__title">Pedidos em aberto</h2></div>
  <div class="delpi-ui-section-card__body">
    <div class="delpi-ui-data-list-toolbar" id="toolbar">
      <div class="delpi-ui-data-list-toolbar__leading">
        <div class="delpi-ui-data-list-toolbar__layout">Tabela Cards Board</div>
        <p class="delpi-ui-data-list-toolbar__hint">10 coluna(s)</p>
      </div>
      <div class="delpi-ui-data-list-toolbar__actions">
        <button type="button">Excel</button>
        <span>±13px</span>
        <button type="button">Colunas</button>
      </div>
    </div>
    <article class="delpi-ui-interactive-data-card" id="card">
      <div class="delpi-ui-interactive-data-card__field">
        <span class="delpi-ui-interactive-data-card__field-label">Cliente</span>
        <div class="delpi-ui-interactive-data-card__title">WEG AUTOMACAO</div>
      </div>
      <div class="delpi-ui-interactive-data-card__field">
        <span class="delpi-ui-interactive-data-card__field-label">Pedido</span>
        <div class="delpi-ui-interactive-data-card__meta">103538</div>
      </div>
    </article>
  </div>
</div>
<div class="delpi-ui-filters-row" id="filters">
  <div class="delpi-ui-filter-box"><label>Entrega de</label><input type="date" /></div>
  <div class="delpi-ui-filter-box"><label>Entrega até</label><input type="date" /></div>
</div>
</body></html>`;

writeFileSync(join(outDir, "fixture.html"), html);

const budgets = {
  cardPadding: 12,
  headerMarginBottom: 10,
  interactivePadding: 10,
  fieldPaddingBlock: 8,
  filtersPadding: 10,
  toolbarMarginBottom: 8,
};

const nodeEval = `
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 375, height: 812 });
  await page.goto('file:///work/fixture.html');
  const metrics = await page.evaluate(() => {
    const cs = (el) => getComputedStyle(el);
    const px = (v) => Number.parseFloat(v);
    const section = document.getElementById('section');
    const card = document.getElementById('card');
    const field = card.querySelector('.delpi-ui-interactive-data-card__field');
    const filters = document.getElementById('filters');
    const toolbar = document.getElementById('toolbar');
    const header = section.querySelector('.delpi-ui-section-card__header');
    return {
      viewport: window.innerWidth,
      cardPadding: px(cs(section).paddingTop),
      headerMarginBottom: px(cs(header).marginBottom),
      interactivePadding: px(cs(card).paddingTop),
      fieldPaddingBlock: px(cs(field).paddingTop) + px(cs(field).paddingBottom),
      fieldFlexDirection: cs(field).flexDirection,
      filtersPadding: px(cs(filters).paddingTop),
      toolbarMarginBottom: px(cs(toolbar).marginBottom),
    };
  });
  console.log(JSON.stringify(metrics));
  await browser.close();
})().catch((err) => { console.error(String(err)); process.exit(1); });
`;

const result = spawnSync(
  "docker",
  [
    "run",
    "--rm",
    "-v",
    `${outDir}:/work`,
    "-w",
    "/usr/src/app",
    "zenika/alpine-chrome:with-puppeteer",
    "node",
    "-e",
    nodeEval,
  ],
  { encoding: "utf8" },
);

if (result.status !== 0) {
  console.error(result.stderr || result.stdout);
  process.exit(result.status ?? 1);
}

const lines = result.stdout.trim().split("\n").filter(Boolean);
const metrics = JSON.parse(lines.at(-1));
writeFileSync(join(outDir, "metrics.json"), JSON.stringify({ budgets, metrics }, null, 2));
console.log(JSON.stringify({ budgets, metrics }, null, 2));

const fails = [];
for (const [key, max] of Object.entries(budgets)) {
  if (metrics[key] > max) fails.push(`${key}=${metrics[key]} > ${max}`);
}
if (metrics.fieldFlexDirection !== "row") {
  fails.push(`fieldFlexDirection=${metrics.fieldFlexDirection}`);
}
if (fails.length) {
  console.error("FAIL mobile spacing budgets:", fails.join("; "));
  process.exit(1);
}
console.log("PASS mobile spacing budgets @375px");
