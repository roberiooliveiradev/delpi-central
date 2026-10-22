/** @vitest-environment jsdom */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildMetallographicPrintHtml } from "../domain/metallographicPrint";

const here = dirname(fileURLToPath(import.meta.url));
const referenceCss = readFileSync(resolve(here, "reference-document.css"), "utf8");
const screenCss = readFileSync(resolve(here, "screen-theme.css"), "utf8");

const DOCUMENT_PALETTE = ["#0b3a5d", "#00527e", "#00a4ce", "#25465f", "#71899d", "#cbdbe5", "#f3f7f9", "#fff", "#d83232"];

function block(source: string, start: string, end: string): string {
  const from = source.indexOf(start);
  const to = source.indexOf(end);
  if (from < 0 || to < from) throw new Error(`bloco ausente: ${start}`);
  return source.slice(from, to);
}

describe("tema de tela do metalografia", () => {
  it("mantém a geometria e a paleta documental no CSS de referência", () => {
    expect(referenceCss).toContain("--navy:#0b3a5d");
    expect(referenceCss).toContain(".sheet{width:210mm;height:297mm");
    expect(referenceCss).toContain("@page{size:A4 portrait;margin:0}");
    expect(referenceCss).toContain("background:#fff");
    expect(referenceCss).not.toContain("data-theme");
    expect(referenceCss).not.toContain("prefers-color-scheme");
  });

  it("acompanha o data-theme do Portal sem seletor próprio nem vazamento global", () => {
    expect(screenCss).toContain(':root[data-theme="dark"] .dashboard-metalography');
    expect(screenCss).toContain("var(--surface,");
    expect(screenCss).toContain("var(--text,");
    expect(screenCss).toContain("var(--primary,");
    expect(screenCss).not.toMatch(/(^|\n)\s*:root\s*\{/);
    expect(screenCss).not.toMatch(/\bbody\s*\{/);
    expect(screenCss).not.toContain("prefers-color-scheme");
    expect(screenCss).not.toContain(".return-home-modal");
    expect(screenCss).not.toContain(".crop-modal");
    expect(screenCss).not.toMatch(/\b(width|height|padding|margin|position|display|grid-template|flex-direction|font-size|gap|transform|inset|z-index)\s*:/);
  });

  it("restaura a paleta impressa mesmo com o tema escuro no seletor", () => {
    const print = block(screenCss, "/* print-palette:start */", "/* print-palette:end */");
    for (const color of DOCUMENT_PALETTE) expect(print).toContain(color);
    expect(print).toContain(':root[data-theme="dark"] .dashboard-metalography');
    expect(print).toContain("background: #fff !important");
    expect(print).toContain("color: #25465f !important");
    expect(print).not.toContain("@media screen");

    const screen = block(screenCss, "@media screen {", "/* print-palette:start */");
    expect(screen).toContain(".sheet");
    expect(screen).toContain(".logo-wrap");
    expect(screen).toContain(".diagram-card");
    expect(screen).toContain("background: var(--white, #fff)");
  });

  it("monta a impressão isolada sem data-theme e com a folha branca", () => {
    const html = buildMetallographicPrintHtml("<main class=\"sheet\">FOLHA-TEMA</main>", `${referenceCss}\n${screenCss}`);

    expect(html).toMatch(/<html lang="pt-BR">/);
    expect(html).not.toMatch(/<html[^>]*data-theme/);
    expect(html).toContain("FOLHA-TEMA");
    expect(html).toContain("--navy:#0b3a5d");
    expect(html).toContain("--navy: #0b3a5d");
    expect(html).toContain("background:#fff");
    expect(html).toContain("background: #fff !important");
    expect(html).toContain("@page{size:A4 portrait;margin:0}");
    expect(html).not.toContain("portal-sidebar");
  });
});
