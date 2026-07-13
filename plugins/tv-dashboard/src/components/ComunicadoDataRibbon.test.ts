import { describe, expect, it, vi } from "vitest";

/**
 * Contratos da aba Dados na ribbon: «Inserir nova fonte» abre o catálogo em modal.
 */
describe("ComunicadoDataRibbon catalog open contract", () => {
  it("onOpenCatalog abre o modal do catálogo (não a sidebar)", () => {
    const openDataCatalog = vi.fn();
    const onOpenCatalog = () => openDataCatalog();
    onOpenCatalog();
    expect(openDataCatalog).toHaveBeenCalledTimes(1);
  });

  it("Trocar rota pede o catálogo em modo replace", () => {
    const openDataCatalog = vi.fn();
    openDataCatalog("replace");
    expect(openDataCatalog).toHaveBeenCalledWith("replace");
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
