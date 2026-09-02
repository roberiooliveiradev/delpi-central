import { describe, expect, it } from "vitest";

import {
  clearCanvasTableCellFormats,
  clearCanvasTableCellsFormats,
} from "./canvasTableClipboard";
import { centerCanvasTableMergeAnchor } from "./canvasTableMerge";
import {
  nextCanvasTableWhiteSpaceToggle,
  normalizeCanvasTableCell,
  resolveCanvasTableCellBoxStyle,
  resolveCanvasTableWrapActive,
} from "./comunicadoCanvasTable";

describe("resolveCanvasTableCellBoxStyle defaults", () => {
  it("número alinha à direita e texto à esquerda sem textAlign", () => {
    expect(
      resolveCanvasTableCellBoxStyle(normalizeCanvasTableCell({ kind: "number", value: 10 }))
        .textAlign,
    ).toBe("right");
    expect(
      resolveCanvasTableCellBoxStyle(normalizeCanvasTableCell({ kind: "text", text: "A" }))
        .textAlign,
    ).toBe("left");
  });

  it("wrap default pre-wrap; nowrap usa ellipsis", () => {
    const wrapped = resolveCanvasTableCellBoxStyle(
      normalizeCanvasTableCell({ kind: "text", text: "FATURADO MÊS" }),
    );
    expect(wrapped.whiteSpace).toBe("pre-wrap");
    expect(wrapped.textOverflow).toBe("clip");
    const nowrap = resolveCanvasTableCellBoxStyle(
      normalizeCanvasTableCell({
        kind: "text",
        text: "x",
        style: { whiteSpace: "nowrap" },
      }),
    );
    expect(nowrap.whiteSpace).toBe("nowrap");
    expect(nowrap.textOverflow).toBe("ellipsis");
  });

  it("toggle Quebrar alterna wrap ↔ nowrap e nowrap é visível no box style", () => {
    expect(resolveCanvasTableWrapActive(undefined)).toBe(true);
    expect(resolveCanvasTableWrapActive("pre-wrap")).toBe(true);
    expect(resolveCanvasTableWrapActive("nowrap")).toBe(false);
    expect(nextCanvasTableWhiteSpaceToggle(undefined)).toBe("nowrap");
    expect(nextCanvasTableWhiteSpaceToggle("nowrap")).toBe("pre-wrap");
    const toggled = resolveCanvasTableCellBoxStyle(
      normalizeCanvasTableCell({
        kind: "text",
        text: "x",
        style: { whiteSpace: nextCanvasTableWhiteSpaceToggle("pre-wrap") },
      }),
    );
    expect(toggled.whiteSpace).toBe("nowrap");
  });

  it("verticalAlign middle por default", () => {
    expect(
      resolveCanvasTableCellBoxStyle(normalizeCanvasTableCell("A")).verticalAlign,
    ).toBe("middle");
  });
});

describe("clearCanvasTableCellFormats", () => {
  it("remove style e mantém texto", () => {
    const cleared = clearCanvasTableCellFormats(
      normalizeCanvasTableCell({
        kind: "text",
        text: "ok",
        style: { backgroundColor: "#f00", textAlign: "center" },
      }),
    );
    expect(cleared.text).toBe("ok");
    expect(cleared.style).toBeUndefined();
  });

  it("aplica em seleção", () => {
    const grid = [
      [
        normalizeCanvasTableCell({ kind: "text", text: "A", style: { color: "#000" } }),
        normalizeCanvasTableCell("B"),
      ],
    ];
    const next = clearCanvasTableCellsFormats(grid, [{ row: 0, col: 0 }]);
    expect(next[0]![0]!.style).toBeUndefined();
    expect(next[0]![0]!.text).toBe("A");
  });
});

describe("centerCanvasTableMergeAnchor", () => {
  it("centraliza a âncora do retângulo", () => {
    const next = centerCanvasTableMergeAnchor(
      [
        [normalizeCanvasTableCell("A"), normalizeCanvasTableCell("B")],
        [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
      ],
      [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 1, col: 0 },
        { row: 1, col: 1 },
      ],
    );
    expect(next[0]![0]!.style?.textAlign).toBe("center");
  });
});
