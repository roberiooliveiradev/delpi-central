/** @vitest-environment node */
import { spawn } from "node:child_process";
import { existsSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { inflateRawSync, inflateSync } from "node:zlib";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const referenceCss = readFileSync(resolve(here, "reference-document.css"), "utf8");
const screenCss = readFileSync(resolve(here, "screen-theme.css"), "utf8");
const CHROME = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe";

const PORTAL_TOKENS = `
:root {
  --bg: #ffffff;
  --surface: #ffffff;
  --surface-2: #f7f7f7;
  --surface-3: #fafafa;
  --app-canvas: #ffffff;
  --text: #003866;
  --text-muted: rgba(17, 17, 17, 0.7);
  --border: #e6e6e6;
  --border-2: #d9d9d9;
  --primary: #089bdb;
  --secundary: #003866;
  --success: #067647;
  --danger: #b42318;
  --control-bg: #ffffff;
  --control-text: #003866;
  --control-border: #d9d9d9;
  --control-placeholder: rgba(17, 17, 17, 0.55);
  --focus-ring: 0 0 0 3px rgba(8, 155, 219, 0.25);
  --alert-success-bg: #e9f6ef;
  --alert-danger-bg: #fff0ee;
  --alert-danger-border: #f0cbc7;
}
:root[data-theme="dark"] {
  --bg: #0f1115;
  --surface: #0f1115;
  --surface-2: #1b2030;
  --surface-3: #111521;
  --app-canvas: #0f1115;
  --text: rgba(255, 255, 255, 0.85);
  --text-muted: rgba(255, 255, 255, 0.7);
  --border: rgba(255, 255, 255, 0.12);
  --border-2: rgba(255, 255, 255, 0.16);
  --danger: #ff6b6b;
  --success: #2ecc71;
  --control-bg: #243044;
  --control-text: rgba(255, 255, 255, 0.85);
  --control-border: rgba(255, 255, 255, 0.22);
  --control-placeholder: rgba(255, 255, 255, 0.55);
  --alert-success-bg: rgba(46, 204, 113, 0.15);
  --alert-danger-bg: rgba(255, 107, 107, 0.18);
  --alert-danger-border: rgba(255, 107, 107, 0.5);
}
#outside { background: #123456; color: #abcdef; }
`;

const FIXTURE = `
<div id="outside">FORA</div>
<div id="app-home" class="dashboard-metalography dashboard-page">
  <section class="home-screen">
    <header class="home-header"><h1>Análises metalográficas</h1></header>
    <section class="home-hero"><h2>Seus relatórios</h2><p>Abra uma análise</p><strong class="home-stat">7</strong></section>
    <section class="reports-panel">
      <h2>Relatórios salvos</h2>
      <section class="report-filter-box">
        <label class="filter-field">Terminal<input id="filter-terminal" placeholder="Código" /></label>
      </section>
      <article class="saved-report">
        <strong>MET-2026-000007</strong>
        <span class="result-badge is-conforme">Conforme</span>
        <button type="button" class="report-open">Abrir</button>
        <button type="button" class="report-delete">Excluir</button>
      </article>
      <div class="empty-state"><strong>Nenhum relatório</strong></div>
    </section>
    <button type="button" class="home-new">Novo Relatório</button>
  </section>
</div>
<div id="app-editor" class="dashboard-metalography dashboard-page editor-active">
  <div class="toolbar"><button type="button" class="secondary">Imprimir</button><button type="button" class="save-button">Salvar</button></div>
  <main class="sheet">
    <h1>ANÁLISE METALOGRÁFICA</h1>
    <div class="field-card"><input class="entry" placeholder="Terminal" /></div>
    <div class="image-frame"><span class="image-placeholder">Micrografia</span></div>
    <div class="measure-table"><div class="th">Parâmetro</div><div class="cell">CH</div></div>
    <figure class="diagram-card"></figure>
    <div class="logo-wrap"></div>
    <textarea>observação</textarea>
    <footer class="footer">DELPI</footer>
  </main>
  <div class="return-home-modal open"><div class="return-home-dialog" role="dialog"><h2>Excluir</h2><p>MET-2026-000007</p><button type="button" class="secondary">Cancelar</button><button type="button" class="delete-confirm-button">Confirmar</button></div></div>
  <div class="crop-modal open"><div class="crop-panel" role="dialog"><h3>Recortar</h3><div class="crop-stage"></div></div></div>
</div>
`;

type Sample = Record<string, { backgroundColor: string; color: string; borderTopColor: string }>;

function luminance(color: string): number {
  const rgb = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  const srgb = color.match(/color\(srgb\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)/);
  if (!rgb && !srgb) throw new Error(`cor não computada: ${color}`);
  const channels = rgb
    ? [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])]
    : [Number(srgb?.[1]) * 255, Number(srgb?.[2]) * 255, Number(srgb?.[3]) * 255];
  const [red, green, blue] = channels.map((channel) => {
    const value = channel / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

const PROBE = `
const nodes = {
  page: "#app-home",
  home: ".home-screen",
  hero: ".home-hero",
  panel: ".reports-panel",
  card: ".saved-report",
  filters: ".report-filter-box",
  field: "#filter-terminal",
  empty: ".empty-state",
  sheet: "#app-editor .sheet",
  fieldCard: "#app-editor .field-card",
  entry: "#app-editor .entry",
  frame: "#app-editor .image-frame",
  headerCell: "#app-editor .th",
  diagram: "#app-editor .diagram-card",
  logo: "#app-editor .logo-wrap",
  dialog: "#app-editor .return-home-dialog",
  crop: "#app-editor .crop-panel",
  stage: "#app-editor .crop-stage",
  outside: "#outside"
};
function sample() {
  const out = {};
  for (const [name, selector] of Object.entries(nodes)) {
    const node = document.querySelector(selector);
    const style = getComputedStyle(node);
    out[name] = { backgroundColor: style.backgroundColor, color: style.color, borderTopColor: style.borderTopColor };
  }
  return out;
}
document.documentElement.setAttribute("data-theme", "light");
const light = sample();
document.documentElement.setAttribute("data-theme", "dark");
const dark = sample();
document.documentElement.setAttribute("data-theme", "light");
const lightAgain = sample();
document.documentElement.setAttribute("data-theme", "dark");
const pre = document.createElement("pre");
pre.id = "theme-result";
pre.textContent = JSON.stringify({ light, dark, lightAgain });
document.body.append(pre);
`;

function runChrome(args: string[]): Promise<string> {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(CHROME, [
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "--allow-file-access-from-files",
      "--virtual-time-budget=4000",
      ...args,
    ], { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout?.on("data", (chunk: Buffer) => { stdout += chunk.toString("utf8"); });
    child.stderr?.on("data", (chunk: Buffer) => { stderr += chunk.toString("utf8"); });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code && code !== 0) reject(new Error(stderr || `Chrome encerrou com ${code}`));
      else resolvePromise(stdout);
    });
  });
}

function chromeThemeProbeReady(): boolean {
  if (!existsSync(CHROME)) return false;
  const probe = "/mnt/c/Users/analistaptd/AppData/Local/Temp/mg-theme-write-probe";
  try {
    writeFileSync(probe, "ok");
    unlinkSync(probe);
    return true;
  } catch {
    return false;
  }
}

describe("tema computado no Chrome", () => {
  it.skipIf(!chromeThemeProbeReady())("alterna claro e escuro na hora e mantém a impressão branca", async () => {
    const stamp = `${process.pid}-${Date.now()}`;
    const windowsTemp = "/mnt/c/Users/analistaptd/AppData/Local/Temp";
    const base = `C:/Users/analistaptd/AppData/Local/Temp/mg-theme-${stamp}`;
    const html = (name: string, body: string) => {
      const file = `${windowsTemp}/mg-theme-${stamp}-${name}.html`;
      writeFileSync(file, body);
      return `file:///${base}-${name}.html`;
    };
    const documentFor = (theme: string, script: string) => `<!DOCTYPE html><html data-theme="${theme}"><head><meta charset="utf-8"><style>${PORTAL_TOKENS}\n${referenceCss}\n${screenCss}</style></head><body>${FIXTURE}<script>${script}</script></body></html>`;
    const probeUrl = html("probe", documentFor("light", PROBE));
    const lightUrl = html("light", documentFor("light", 'document.documentElement.setAttribute("data-theme","light")'));
    const darkUrl = html("dark", documentFor("dark", 'document.documentElement.setAttribute("data-theme","dark")'));
    const dom = await runChrome(["--window-size=1280,900", "--dump-dom", probeUrl]);
    const match = dom.match(/<pre id="theme-result">([\s\S]*?)<\/pre>/);
    if (!match) throw new Error("Chrome não devolveu o resultado do tema");
    const parsed = JSON.parse(match[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&")) as {
      light: Sample;
      dark: Sample;
      lightAgain: Sample;
    };
    const { light, dark, lightAgain } = parsed;
    const narrowDom = await runChrome(["--window-size=390,800", "--dump-dom", probeUrl]);
    const narrowMatch = narrowDom.match(/<pre id="theme-result">([\s\S]*?)<\/pre>/);
    if (!narrowMatch) throw new Error("Chrome não devolveu o tema na viewport estreita");
    const narrow = JSON.parse(narrowMatch[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&")) as { dark: Sample };

    for (const name of ["page", "home", "panel", "card", "filters", "field", "empty", "sheet", "fieldCard", "frame", "dialog", "crop"] as const) {
      expect(luminance(light[name].backgroundColor), `claro ${name}`).toBeGreaterThan(0.7);
      expect(luminance(dark[name].backgroundColor), `escuro ${name}`).toBeLessThan(0.2);
      expect(luminance(lightAgain[name].backgroundColor), `retorno ${name}`).toBeGreaterThan(0.7);
    }
    expect(luminance(dark.card.color)).toBeGreaterThan(0.5);
    expect(luminance(dark.field.color)).toBeGreaterThan(0.5);
    expect(luminance(dark.entry.color)).toBeGreaterThan(0.5);
    expect(luminance(dark.dialog.color)).toBeGreaterThan(0.5);
    expect(luminance(light.hero.backgroundColor)).toBeLessThan(0.35);
    expect(luminance(dark.hero.backgroundColor)).toBeLessThan(0.2);
    expect(luminance(dark.headerCell.backgroundColor)).toBeLessThan(0.25);
    expect(luminance(dark.headerCell.color)).toBeGreaterThan(0.7);
    expect(luminance(dark.diagram.backgroundColor)).toBeGreaterThan(0.9);
    expect(luminance(dark.logo.backgroundColor)).toBeGreaterThan(0.9);
    expect(luminance(dark.stage.backgroundColor)).toBeLessThan(0.15);
    expect(light.outside.backgroundColor).toBe(dark.outside.backgroundColor);

    const lightPng = `${windowsTemp}/mg-theme-${stamp}-light.png`;
    const darkPng = `${windowsTemp}/mg-theme-${stamp}-dark.png`;
    const pdf = `${windowsTemp}/mg-theme-${stamp}-print.pdf`;
    const win = `C:\\Users\\analistaptd\\AppData\\Local\\Temp\\mg-theme-${stamp}`;
    await runChrome(["--window-size=1280,900", `--screenshot=${win}-light.png`, lightUrl]);
    await runChrome(["--window-size=390,800", `--screenshot=${win}-dark.png`, darkUrl]);
    await runChrome(["--no-pdf-header-footer", `--print-to-pdf=${win}-print.pdf`, darkUrl]);
    expect(luminance(narrow.dark.panel.backgroundColor)).toBeLessThan(0.2);
    expect(luminance(narrow.dark.field.backgroundColor)).toBeLessThan(0.2);
    expect(luminance(narrow.dark.sheet.backgroundColor)).toBeLessThan(0.2);
    writeFileSync(join(tmpdir(), "mg-theme-light.png"), readFileSync(lightPng));
    writeFileSync(join(tmpdir(), "mg-theme-dark.png"), readFileSync(darkPng));
    const printed = inflatePdf(readFileSync(pdf));
    expect(printed).toContain("1 1 1 rg");
    expect(printed).not.toContain("0.106 0.125 0.188");
    expect(printed).not.toContain("0.059 0.067 0.082");
  }, 90000);
});

function inflatePdf(bytes: Buffer): string {
  const raw = bytes.toString("latin1");
  const parts: string[] = [];
  for (const match of raw.matchAll(/stream\r?\n([\s\S]*?)endstream/g)) {
    const body = Buffer.from(match[1].replace(/\r?\n$/, ""), "latin1");
    try {
      parts.push(inflateSync(body).toString("latin1"));
      continue;
    } catch {
      // tenta o fluxo sem o wrapper zlib
    }
    try {
      parts.push(inflateRawSync(body).toString("latin1"));
    } catch {
      parts.push(match[1]);
    }
  }
  return parts.join("\n");
}
