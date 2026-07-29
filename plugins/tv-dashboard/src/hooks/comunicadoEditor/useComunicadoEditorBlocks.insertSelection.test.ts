import { act, renderHook } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditorBlocks } from "./useComunicadoEditorBlocks";

/**
 * Regressão: inserir texto/forma/componente deve deixar o bloco selecionado.
 * Causa raiz antiga: setSelectedId antes do updateBlocks — o id ainda não
 * existia em configRef e a seleção ficava vazia.
 */
describe("useComunicadoEditorBlocks insert selection", () => {
  function renderBlocksHook() {
    const selectedIdsRef = { current: [] as string[] };
    return renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks: [] });
      const removeSelectedRef = useRef(() => {});
      const updateBlockTextFieldsRef = useRef(() => {});
      return {
        configRef,
        selectedIdsRef,
        ...useComunicadoEditorBlocks({
          configRef,
          commitWithHistory: (next) => {
            configRef.current = next;
          },
          selectedIds: selectedIdsRef.current,
          getActionSelectedIds: () => selectedIdsRef.current,
          selectedId: selectedIdsRef.current[0] ?? null,
          selected: null,
          selectedBlocks: [],
          selectedChartPart: null,
          selectedTablePart: null,
          selectedKpiPart: null,
          selectedInputPart: null,
          editingChartPart: null,
          editingKpiPart: null,
          setSelectedId: (id) => {
            selectedIdsRef.current = id ? [id] : [];
          },
          selectBlocksByIds: (ids) => {
            const present = new Set((configRef.current.blocks ?? []).map((block) => block.id));
            selectedIdsRef.current = ids.filter((id) => present.has(id));
          },
          setSelectedChartPart: vi.fn(),
          setEditingChartPart: vi.fn(),
          setSelectedTablePart: vi.fn(),
          setSelectedKpiPart: vi.fn(),
          setEditingKpiPart: vi.fn(),
          setLastDataDisplayMode: vi.fn(),
          setDataPanelOpen: vi.fn(),
          setDataPanelIntent: vi.fn(),
          setDataCatalogModalOpen: vi.fn(),
          setDataCatalogAnchor: vi.fn(),
          setDataCatalogMode: vi.fn(),
          setShapeMenuOpen: vi.fn(),
          setRibbonTabRequest: vi.fn(),
          removeSelectedRef,
          updateBlockTextFieldsRef,
        }),
      };
    });
  }

  it("addBlock (texto) seleciona o bloco inserido", () => {
    const { result } = renderBlocksHook();
    act(() => {
      result.current.addBlock("text");
    });
    const inserted = result.current.configRef.current.blocks?.[0];
    expect(inserted?.type).toBe("text");
    expect(result.current.selectedIdsRef.current).toEqual([inserted!.id]);
  });

  it("addShape seleciona a forma inserida", () => {
    const { result } = renderBlocksHook();
    act(() => {
      result.current.addShape("rectangle");
    });
    const inserted = result.current.configRef.current.blocks?.[0];
    expect(inserted?.type).toBe("shape");
    expect(result.current.selectedIdsRef.current).toEqual([inserted!.id]);
  });

  it("addKpiViewBlock seleciona o componente inserido", () => {
    const { result } = renderBlocksHook();
    act(() => {
      result.current.addKpiViewBlock();
    });
    const inserted = result.current.configRef.current.blocks?.[0];
    expect(inserted?.type).toBe("kpi_view");
    expect(result.current.selectedIdsRef.current).toEqual([inserted!.id]);
  });

  it("addTableViewBlock e addIconBlock também selecionam", () => {
    const { result } = renderBlocksHook();
    act(() => {
      result.current.addTableViewBlock(3, 3, "grid");
    });
    const table = result.current.configRef.current.blocks?.[0];
    expect(table?.type).toBe("table_view");
    expect(result.current.selectedIdsRef.current).toEqual([table!.id]);

    act(() => {
      result.current.addIconBlock("Gauge");
    });
    const icon = result.current.configRef.current.blocks?.find((block) => block.type === "icon");
    expect(icon).toBeTruthy();
    expect(result.current.selectedIdsRef.current).toEqual([icon!.id]);
  });
});
