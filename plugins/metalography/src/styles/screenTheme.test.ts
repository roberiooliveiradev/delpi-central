/** @vitest-environment jsdom */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildMetallographicPrintHtml } from "../domain/metallographicPrint";

const here = dirname(fileURLToPath(import.meta.url));
const referenceCss = readFileSync(resolve(here, "reference-document.css"), "utf8");
const screenCss = readFileSync(resolve(here, "screen-theme.css"), "utf8");
const DOCUMENT_PALETTE = ["#0b3a5d", "#00a4ce", "#25465f", "#71899d", "#cbdbe5", "#fff", "#f5f8fa", "#d6e2e9"];

function block(source: string, start: string, end: string): string {
  const from = source.indexOf(start);
  const to = source.indexOf(end);
  if (from < 0 || to < from) throw new Error(`bloco ausente: ${start}`);
  return source.slice(from, to);
}

describe("tokens de tema do metalografia", () => {
  it("preserva geometria e paleta documental no CSS de referência", () => {
    expect(referenceCss).toContain("--navy:#0b3a5d");
    expect(referenceCss).toContain(".sheet{width:210mm;height:297mm");
    expect(referenceCss).toContain("@page{size:A4 portrait;margin:0}");
    expect(referenceCss).not.toContain("data-theme");
    expect(referenceCss).not.toContain("--mg-");
  });

  it("centraliza o tema em tokens do escopo do MFE, sem vazar para o Portal", () => {
    expect(screenCss).toContain("--mg-bg:");
    expect(screenCss).toContain("--mg-surface:");
    expect(screenCss).toContain("--mg-paper:");
    expect(screenCss).toContain("--mg-heading:");
    expect(screenCss).toContain("--mg-control-bg:");
    expect(screenCss).toContain(':root[data-theme="dark"] .dashboard-metalography');
    expect(screenCss).toContain("var(--surface,");
    expect(screenCss).toContain("var(--surface-2,");
    expect(screenCss).toContain("var(--primary,");
    expect(screenCss).toContain("var(--text,");
    expect(screenCss).not.toMatch(/(^|\n)\s*:root\s*\{/);
    expect(screenCss).not.toMatch(/\bbody\s*\{/);
    expect(screenCss).not.toContain("prefers-color-scheme");
    expect(screenCss).not.toMatch(/\b(width|height|padding|margin|position|display|grid-template|flex-direction|font-size|gap|transform|inset|z-index)\s*:/);
    expect(screenCss).not.toMatch(/\.return-home-modal[^{]*\{[^}]*\b(display|position|inset)\s*:/);
    expect(screenCss).not.toMatch(/\.crop-modal[^{]*\{[^}]*\b(display|position|inset)\s*:/);
  });

  it("restaura a paleta impressa por token, mesmo com data-theme escuro", () => {
    const print = block(screenCss, "/* print-palette:start */", "/* print-palette:end */");
    for (const color of DOCUMENT_PALETTE) expect(print).toContain(color);
    expect(print).toContain("--mg-paper: #fff");
    expect(print).toContain("--mg-heading: #0b3a5d");
    expect(print).toContain("--mg-navy: #0b3a5d");
    expect(print).toContain("background: #fff !important");
    expect(print).toContain("color: #25465f !important");

    const html = buildMetallographicPrintHtml("<main class=\"sheet\">FOLHA-TEMA</main>", `${referenceCss}\n${screenCss}`);
    expect(html).toMatch(/<html lang="pt-BR">/);
    expect(html).not.toMatch(/<html[^>]*data-theme/);
    expect(html).toContain("--navy:#0b3a5d");
    expect(html).toContain("--mg-paper: #fff");
    expect(html).toContain("@page{size:A4 portrait;margin:0}");
  });
});
