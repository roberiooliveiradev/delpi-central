/**
 * Garante que a regra base `.sidebar` (desktop) não anima propriedades de
 * layout — evita React #185 nos MFEs ao recolher a sidebar do portal.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const cssPath = join(__dirname, "Sidebar.css");

/** Bloco da regra `.sidebar` antes do primeiro `@media` (desktop). */
function desktopSidebarRule(css) {
  const start = css.indexOf(".sidebar {");
  assert.ok(start >= 0, "regra .sidebar não encontrada");
  const media = css.indexOf("@media", start);
  const end = media >= 0 ? media : css.length;
  return css.slice(start, end);
}

describe("sidebarTransition (structural)", () => {
  const css = readFileSync(cssPath, "utf8");
  const desktop = desktopSidebarRule(css);

  it("regra .sidebar desktop não usa transition: all", () => {
    assert.doesNotMatch(desktop, /transition\s*:\s*all\b/);
  });

  it("regra .sidebar desktop não anima width na transition", () => {
    const transitions = [...desktop.matchAll(/transition\s*:\s*([^;]+);/g)].map(
      (m) => m[1],
    );
    assert.ok(transitions.length >= 1, "deve haver transition explícita");
    for (const value of transitions) {
      assert.doesNotMatch(
        value,
        /\b(width|min-width|max-width|padding|border)\b/,
        `transition não deve animar layout: ${value}`,
      );
    }
  });

  it("irmão: .collapse-btn pode continuar com transition: all", () => {
    assert.match(css, /\.collapse-btn\s*\{[^}]*transition\s*:\s*all\b/s);
  });

  it("mobile drawer ainda pode usar transform", () => {
    assert.match(css, /@media\s*\(max-width:\s*1024px\)/);
    assert.match(css, /transform:\s*translateX/);
  });
});
