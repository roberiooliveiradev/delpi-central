import { act, renderHook } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it } from "vitest";
import type { ComunicadoBlock, ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditorSelection } from "./useComunicadoEditorSelection";

const blocks: ComunicadoBlock[] = [
  { id: "a", type: "text", content: "A", frame: { x: 0, y: 0, w: 10, h: 10 } },
  { id: "b", type: "text", content: "B", frame: { x: 0, y: 0, w: 10, h: 10 } },
];

function renderSelectionHook() {
  return renderHook(() => {
    const configRef = useRef<ComunicadoConfig>({ version: 2, blocks });
    const updateBlockTextFieldsRef = useRef(() => {});
    const updateBlocksRef = useRef(() => {});
    return useComunicadoEditorSelection({
      configRef,
      blocks,
      updateBlockTextFieldsRef,
      updateBlocksRef,
    });
  });
}

describe("useComunicadoEditorSelection", () => {
  it("seleciona e limpa blocos", () => {
    const { result } = renderSelectionHook();

    expect(result.current.selectedIds).toEqual([]);

    act(() => {
      result.current.selectBlock("b");
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.clearSelection();
    });
    expect(result.current.selectedIds).toEqual([]);
  });

  it("troca de slide limpa seleção sem auto-selecionar bloco", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectBlock("b");
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.resetSelectionForSlide();
    });
    expect(result.current.selectedIds).toEqual([]);
  });

  it("additive (Shift) alterna ids na multi-seleção", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectBlock("a");
    });
    act(() => {
      result.current.selectBlock("b", { additive: true });
    });
    expect(result.current.selectedIds).toEqual(["a", "b"]);

    act(() => {
      result.current.selectBlock("a", { additive: true });
    });
    expect(result.current.selectedIds).toEqual(["b"]);
  });

  it("selectBlocksByIds substitui a seleção (marquee)", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectBlock("a");
    });
    act(() => {
      result.current.selectBlocksByIds(["a", "b"]);
    });
    expect(result.current.selectedIds).toEqual(["a", "b"]);
  });

  it("multi-seleção de colunas: additive alterna e range estende o intervalo", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectTablePart("a", { kind: "headerCell", colIndex: 0 });
    });
    expect(result.current.selectedTableParts).toEqual([{ kind: "headerCell", colIndex: 0 }]);

    act(() => {
      result.current.selectTablePart("a", { kind: "headerCell", colIndex: 2 }, { additive: true });
    });
    expect(result.current.selectedTableParts).toEqual([
      { kind: "headerCell", colIndex: 0 },
      { kind: "headerCell", colIndex: 2 },
    ]);
    expect(result.current.selectedTablePart).toEqual({ kind: "headerCell", colIndex: 2 });

    /* Additive na coluna já selecionada remove só ela. */
    act(() => {
      result.current.selectTablePart("a", { kind: "headerCell", colIndex: 0 }, { additive: true });
    });
    expect(result.current.selectedTableParts).toEqual([{ kind: "headerCell", colIndex: 2 }]);

    /* Range (Shift) estende da âncora até a coluna clicada. */
    act(() => {
      result.current.selectTablePart("a", { kind: "headerCell", colIndex: 0 }, { range: true });
    });
    expect(result.current.selectedTableParts).toEqual([
      { kind: "headerCell", colIndex: 1 },
      { kind: "headerCell", colIndex: 2 },
      { kind: "headerCell", colIndex: 0 },
    ]);

    /* Clique simples volta à seleção única. */
    act(() => {
      result.current.selectTablePart("a", { kind: "headerCell", colIndex: 1 });
    });
    expect(result.current.selectedTableParts).toEqual([{ kind: "headerCell", colIndex: 1 }]);

    act(() => {
      result.current.clearTablePartSelection();
    });
    expect(result.current.selectedTableParts).toEqual([]);
    expect(result.current.selectedTablePart).toBeNull();
  });
});
