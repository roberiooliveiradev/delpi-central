import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Seleção não deve reflowar o palco (piscar / deslocar o desenho):
 * - ribbon Elemento em densidade `band` (altura fixa)
 * - inspetor sem auto-expand na seleção
 * - painel aberto em overlay com slot in-flow de 36px
 */
describe("selection chrome viewport stability", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const sidePanel = readFileSync(
    join(base, "../components/deck/DeckElementSidePanel.tsx"),
    "utf8",
  );
  const deckChrome = readFileSync(
    join(base, "../components/DeckEditorChrome.tsx"),
    "utf8",
  );
  const embeddedChrome = readFileSync(
    join(base, "../components/ComunicadoEmbeddedEditorChrome.tsx"),
    "utf8",
  );
  const workspace = readFileSync(
    join(base, "../components/DeckWorkspace.tsx"),
    "utf8",
  );

  it("não auto-expande o inspetor só porque há seleção", () => {
    expect(sidePanel).toMatch(/Não auto-expandir na seleção/);
    expect(sidePanel).not.toMatch(
      /if \(selectedIds\.length > 0\) setCollapsed\(false\)/,
    );
  });

  it("ribbon contextual usa densidade band (altura estável)", () => {
    expect(deckChrome).toMatch(/function ribbonDensityFor[\s\S]*return "band"/);
    expect(embeddedChrome).toMatch(/function ribbonDensityFor[\s\S]*return "band"/);
  });

  it("reserva slot de 36px e abre o inspetor em overlay", () => {
    expect(workspace).toMatch(/td-deck-stage__aside-slot/);
    expect(css).toMatch(/\.td-deck-stage__aside-slot\s*\{[^}]*width:\s*36px/s);
    expect(css).toMatch(
      /\.td-deck-right-stack:has\(\.td-deck-side-panel--open\)\s*\{[^}]*position:\s*absolute/s,
    );
  });
});
