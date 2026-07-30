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

  it("additive com grupo expande/remove todos os membros", () => {
    const grouped: ComunicadoBlock[] = [
      { id: "a", type: "text", content: "A", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g1" },
      { id: "b", type: "text", content: "B", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g1" },
      { id: "c", type: "text", content: "C", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g2" },
      { id: "d", type: "text", content: "D", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g2" },
    ];
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks: grouped });
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: grouped,
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    act(() => {
      result.current.selectBlock("a");
    });
    expect(result.current.selectedIds.sort()).toEqual(["a", "b"]);

    act(() => {
      result.current.selectBlock("c", { additive: true, expandGroup: true });
    });
    expect(result.current.selectedIds.sort()).toEqual(["a", "b", "c", "d"]);

    act(() => {
      result.current.selectBlock("b", { additive: true, expandGroup: true });
    });
    expect(result.current.selectedIds.sort()).toEqual(["c", "d"]);
  });

  it("expandGroup false mantém preferGroupChildrenSelection com todos os irmãos", () => {
    const grouped: ComunicadoBlock[] = [
      { id: "a", type: "text", content: "A", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g1" },
      { id: "b", type: "text", content: "B", frame: { x: 0, y: 0, w: 10, h: 10 }, groupId: "g1" },
    ];
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks: grouped });
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: grouped,
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    act(() => {
      result.current.selectBlock("a", { expandGroup: false });
    });
    expect(result.current.preferGroupChildrenSelection).toBe(true);
    expect(result.current.selectedIds).toEqual(["a"]);

    act(() => {
      result.current.selectBlock("b", { additive: true, expandGroup: false });
    });
    expect(result.current.selectedIds.sort()).toEqual(["a", "b"]);
    expect(result.current.preferGroupChildrenSelection).toBe(true);

    act(() => {
      result.current.selectBlocksByIds(["a", "b"]);
    });
    expect(result.current.preferGroupChildrenSelection).toBe(false);
  });

  it("subtract (Ctrl) remove da seleção sem alternar para incluir", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectBlock("a");
    });
    act(() => {
      result.current.selectBlock("b", { additive: true });
    });
    act(() => {
      result.current.selectBlock("a", { subtract: true });
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.selectBlock("a", { subtract: true });
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

  it("selectBlocksByIds ignora ids ainda ausentes no configRef", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectBlocksByIds(["novo"]);
    });
    expect(result.current.selectedIds).toEqual([]);
  });

  it("selectBlocksByIds aceita ids após configRef ser atualizado (paste/duplicate)", () => {
    const configRef = { current: { version: 2 as const, blocks: [...blocks] } };
    const { result } = renderHook(() => {
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: configRef.current.blocks,
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    const novo: ComunicadoBlock = {
      id: "novo",
      type: "text",
      content: "N",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    };

    act(() => {
      result.current.selectBlocksByIds(["novo"]);
    });
    expect(result.current.selectedIds).toEqual([]);

    configRef.current = { version: 2, blocks: [...blocks, novo] };

    act(() => {
      result.current.selectBlocksByIds(["novo"]);
    });
    expect(result.current.selectedIds).toEqual(["novo"]);
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

  it("multi-seleção de linhas: additive e range", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectTablePart("a", { kind: "row", rowIndex: 0 });
    });
    act(() => {
      result.current.selectTablePart("a", { kind: "row", rowIndex: 2 }, { additive: true });
    });
    expect(result.current.selectedTableParts).toEqual([
      { kind: "row", rowIndex: 0 },
      { kind: "row", rowIndex: 2 },
    ]);

    act(() => {
      result.current.selectTablePart("a", { kind: "row", rowIndex: 0 }, { range: true });
    });
    expect(result.current.selectedTableParts).toEqual([
      { kind: "row", rowIndex: 1 },
      { kind: "row", rowIndex: 2 },
      { kind: "row", rowIndex: 0 },
    ]);
  });

  it("selectTablePart em table_view pede Design da Tabela (não aba Elemento fantasma)", () => {
    const tableBlock: ComunicadoBlock = {
      id: "tbl",
      type: "table_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tablePreset: "grid",
    };
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks: [tableBlock] });
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: [tableBlock],
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    act(() => {
      result.current.setSelectionPanelTab("tableDesign");
    });
    act(() => {
      result.current.selectTablePart("tbl", { kind: "headerCell", colIndex: 1 });
    });
    expect(result.current.selectedTablePart).toEqual({ kind: "headerCell", colIndex: 1 });
    expect(result.current.selectionPanelTab).toBe("tableDesign");
    expect(result.current.ribbonTabRequest).toBe("tableDesign");

    act(() => {
      result.current.setSelectionPanelTab("tableLayout");
    });
    act(() => {
      result.current.selectTablePart("tbl", { kind: "frame" });
    });
    expect(result.current.selectedTablePart).toEqual({ kind: "frame" });
    expect(result.current.selectionPanelTab).toBe("tableLayout");
  });

  it("após tabela, gráfico/KPI ficam em Elemento mesmo com requestRibbonTab legado no mesmo tick", () => {
    const tableBlock: ComunicadoBlock = {
      id: "tbl",
      type: "table_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tablePreset: "grid",
    };
    const chartBlock: ComunicadoBlock = {
      id: "cht",
      type: "chart_view",
      frame: { x: 0, y: 40, w: 40, h: 30 },
      chartType: "line",
    };
    const kpiBlock: ComunicadoBlock = {
      id: "kpi",
      type: "kpi_view",
      frame: { x: 0, y: 80, w: 20, h: 20 },
    };
    const blocksLocal = [tableBlock, chartBlock, kpiBlock];
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks: blocksLocal });
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: blocksLocal,
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    act(() => {
      result.current.selectBlock("tbl");
    });
    expect(result.current.selectionPanelTab).toBe("tableDesign");

    /* Simula BlockView: selectChartPart + requestRibbonTab("shape") sem blockId no mesmo tick. */
    act(() => {
      result.current.selectChartPart("cht", { kind: "plotArea" });
      result.current.requestRibbonTab("shape");
    });
    expect(result.current.selectedIds).toEqual(["cht"]);
    expect(result.current.selectionPanelTab).toBe("element");
    expect(result.current.ribbonTabRequest).toBe("element");

    act(() => {
      result.current.selectBlock("tbl");
    });
    act(() => {
      result.current.selectKpiPart("kpi", { kind: "title" });
      result.current.requestRibbonTab("kpi");
    });
    expect(result.current.selectedIds).toEqual(["kpi"]);
    expect(result.current.selectionPanelTab).toBe("element");

    act(() => {
      result.current.selectBlocksByIds(["cht"]);
    });
    expect(result.current.selectionPanelTab).toBe("element");
  });

  it("multi-seleção de partes KPI (filhos do complexo)", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.selectKpiPart("a", { kind: "title" });
    });
    expect(result.current.selectedKpiParts).toEqual([{ kind: "title" }]);
    expect(result.current.selectedKpiPart).toEqual({ kind: "title" });

    act(() => {
      result.current.selectKpiPart("a", { kind: "value" }, { additive: true });
    });
    expect(result.current.selectedKpiParts).toEqual([{ kind: "title" }, { kind: "value" }]);
    expect(result.current.selectedKpiPart).toEqual({ kind: "value" });

    act(() => {
      result.current.selectKpiPart("a", { kind: "card" }, { additive: true });
    });
    expect(result.current.selectedKpiParts).toEqual([{ kind: "card" }]);
  });

  it("enterTextEdit isola membro de grupo e ativa edição sem reexpandir", () => {
    const grouped: ComunicadoBlock[] = [
      {
        id: "t1",
        type: "text",
        content: "Texto",
        frame: { x: 0, y: 0, w: 10, h: 10 },
        groupId: "g1",
      },
      {
        id: "t2",
        type: "heading",
        content: "Titulo",
        frame: { x: 10, y: 0, w: 10, h: 10 },
        groupId: "g1",
      },
    ];
    const configRef = { current: { version: 2 as const, blocks: grouped } };
    const { result } = renderHook(() => {
      const updateBlockTextFieldsRef = useRef(() => {});
      const updateBlocksRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks: grouped,
        updateBlockTextFieldsRef,
        updateBlocksRef,
      });
    });

    act(() => {
      result.current.selectBlock("t1");
    });
    expect(result.current.selectedIds).toEqual(["t1", "t2"]);

    act(() => {
      result.current.enterTextEdit("t1");
    });
    expect(result.current.selectedIds).toEqual(["t1"]);
    expect(result.current.editingTextId).toBe("t1");
  });

  it("enterTextEdit em bloco simples só ativa edição", () => {
    const { result } = renderSelectionHook();

    act(() => {
      result.current.enterTextEdit("a");
    });
    expect(result.current.selectedIds).toEqual(["a"]);
    expect(result.current.editingTextId).toBe("a");
  });
});
