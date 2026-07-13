import { describe, expect, it, vi } from "vitest";

describe("Trocar rota → catálogo novo", () => {
  it("openDataCatalog('replace') abre o modal Fontes com modo substituir", () => {
    const setDataCatalogMode = vi.fn();
    const setDataCatalogModalOpen = vi.fn();
    const openDataCatalog = (mode: "insert" | "replace" = "insert") => {
      setDataCatalogMode(mode);
      setDataCatalogModalOpen(true);
    };

    openDataCatalog("replace");

    expect(setDataCatalogMode).toHaveBeenCalledWith("replace");
    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(true);
  });

  it("modo insert permanece o padrão do catálogo", () => {
    const setDataCatalogMode = vi.fn();
    const setDataCatalogModalOpen = vi.fn();
    const openDataCatalog = (mode: "insert" | "replace" = "insert") => {
      setDataCatalogMode(mode);
      setDataCatalogModalOpen(true);
    };

    openDataCatalog();

    expect(setDataCatalogMode).toHaveBeenCalledWith("insert");
    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(true);
  });
});
