import { describe, expect, it } from "vitest";

import { resolveCanvasTableCellPointerAction } from "./canvasTableCellSelection";

describe("resolveCanvasTableCellPointerAction", () => {
  it("primeiro clique (bloco não selecionado) seleciona o container", () => {
    expect(resolveCanvasTableCellPointerAction({ blockSelected: false })).toBe(
      "select-block",
    );
  });

  it("bloco já selecionado seleciona a célula", () => {
    expect(resolveCanvasTableCellPointerAction({ blockSelected: true })).toBe(
      "select-cell",
    );
  });
});
