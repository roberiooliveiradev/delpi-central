import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { normalizeEditorFocusBlockIds } from "./editorFocusSelection";

describe("normalizeEditorFocusBlockIds", () => {
  it("preserva seleção de blocos do canvas (positive)", () => {
    expect(normalizeEditorFocusBlockIds(["rx_subtitle", "rx_title"])).toEqual([
      "rx_subtitle",
      "rx_title",
    ]);
  });

  it("dedupe e ignora vazios (sibling)", () => {
    expect(normalizeEditorFocusBlockIds(["a", "", "a", "  "])).toEqual(["a"]);
  });

  it("seleção vazia = foco só no slide (negative — não inventar ids)", () => {
    expect(normalizeEditorFocusBlockIds([])).toEqual([]);
  });
});

describe("editorFocus flush contract (PlaylistEditorPage)", () => {
  it("heartbeat reenvia seleção de canvas — não filmstrip selectedSlideIds", () => {
    const pageSrc = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../pages/PlaylistEditorPage.tsx"),
      "utf8",
    );
    expect(pageSrc).toMatch(/canvasSelectedIdsRef/);
    expect(pageSrc).toMatch(/normalizeEditorFocusBlockIds/);
    // Regressão: flush NÃO pode derivar blockIds do filmstrip.
    expect(pageSrc).not.toMatch(
      /selectedSlideIdsRef\.current\.filter\(\(id\)\s*=>\s*id\s*!==\s*slideId\)/,
    );
  });
});
