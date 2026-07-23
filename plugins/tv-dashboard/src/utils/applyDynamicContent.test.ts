import { describe, expect, it, vi } from "vitest";

import { applyDynamicContent, canOpenDynamicContentPicker } from "./applyDynamicContent";

describe("applyDynamicContent", () => {
  it("insere data_field via bridge na edição inline", () => {
    const insert = vi.fn();
    const result = applyDynamicContent(
      { kind: "data_field", dataRef: { field: "oee", format: "percent" } },
      {
        blocks: [
          {
            id: "t1",
            type: "text",
            content: "Meta ",
            frame: { x: 0, y: 0, w: 10, h: 10 },
          } as never,
        ],
        editingTextId: "t1",
        selectedCanvasTableCell: null,
        getTextEditorBridge: () => ({ insertDataRefAtSelection: insert }) as never,
        updateBlock: vi.fn(),
      },
    );
    expect(result).toEqual({ ok: true, target: "text_run" });
    expect(insert).toHaveBeenCalledWith({ field: "oee", format: "percent" });
  });

  it("aplica data_field na célula da Grade", () => {
    const updateBlock = vi.fn();
    const table = {
      id: "g1",
      type: "canvas_table",
      frame: { x: 0, y: 0, w: 40, h: 20 },
      rows: 1,
      cols: 1,
      cells: [[{ kind: "text", text: "" }]],
    };
    const result = applyDynamicContent(
      { kind: "data_field", dataRef: { field: "ppm" } },
      {
        blocks: [table as never],
        editingTextId: null,
        selectedCanvasTableCell: { blockId: "g1", row: 0, col: 0 },
        getTextEditorBridge: () => null,
        updateBlock,
      },
    );
    expect(result.ok).toBe(true);
    expect(updateBlock).toHaveBeenCalled();
    const patch = updateBlock.mock.calls[0][1];
    expect(patch.cells[0][0].dataRef?.field).toBe("ppm");
  });

  it("recusa kind scaffold", () => {
    expect(
      applyDynamicContent(
        { kind: "conditional_text", label: "x" },
        {
          blocks: [],
          editingTextId: "t1",
          selectedCanvasTableCell: null,
          getTextEditorBridge: () => null,
          updateBlock: vi.fn(),
        },
      ),
    ).toEqual({ ok: false, reason: "unsupported_kind" });
  });
});

describe("canOpenDynamicContentPicker", () => {
  it("abre em edição de visual box ou célula de Grade", () => {
    expect(
      canOpenDynamicContentPicker({
        editingTextId: "t1",
        selected: { id: "t1", type: "shape" } as never,
        selectedCanvasTableCell: null,
      }),
    ).toBe(true);
    expect(
      canOpenDynamicContentPicker({
        editingTextId: null,
        selected: { id: "g1", type: "canvas_table" } as never,
        selectedCanvasTableCell: { blockId: "g1", row: 0, col: 0 },
      }),
    ).toBe(true);
    expect(
      canOpenDynamicContentPicker({
        editingTextId: null,
        selected: { id: "g1", type: "canvas_table" } as never,
        selectedCanvasTableCell: null,
      }),
    ).toBe(false);
  });
});
