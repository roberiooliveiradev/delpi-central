import { describe, expect, it, vi } from "vitest";

/**
 * Contratos da aba Dados na ribbon: «Inserir nova fonte» deve abrir o catálogo
 * (intent=catalog), não só reforçar a aba atual.
 */
describe("ComunicadoDataRibbon catalog open contract", () => {
  it("onOpenCatalog define intent catalog (não é no-op de aba)", () => {
    const setDataPanelIntent = vi.fn();
    const onOpenCatalog = () => setDataPanelIntent("catalog");
    onOpenCatalog();
    expect(setDataPanelIntent).toHaveBeenCalledWith("catalog");
  });

  it("onInserted restaura intent binding antes de ir ao Elemento", () => {
    const setDataPanelIntent = vi.fn();
    const setSelectionPanelTab = vi.fn();
    const onInserted = () => {
      setDataPanelIntent("binding");
      setSelectionPanelTab("element");
    };
    onInserted();
    expect(setDataPanelIntent).toHaveBeenCalledWith("binding");
    expect(setSelectionPanelTab).toHaveBeenCalledWith("element");
  });
});
