import { describe, expect, it, vi } from "vitest";

import type { OpenDataCatalogOptions } from "./comunicadoEditorContextCore";

describe("Trocar rota → catálogo popover", () => {
  it("openDataCatalog('replace') abre o popover Fontes com modo substituir", () => {
    const setDataCatalogMode = vi.fn();
    const setDataCatalogModalOpen = vi.fn();
    const setDataCatalogAnchor = vi.fn();
    const openDataCatalog = (
      mode: "insert" | "replace" = "insert",
      options?: OpenDataCatalogOptions,
    ) => {
      setDataCatalogMode(mode);
      setDataCatalogAnchor(options?.anchor ?? null);
      setDataCatalogModalOpen(true);
    };

    const anchor = document.createElement("button");
    openDataCatalog("replace", { anchor });

    expect(setDataCatalogMode).toHaveBeenCalledWith("replace");
    expect(setDataCatalogAnchor).toHaveBeenCalledWith(anchor);
    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(true);
  });

  it("modo insert permanece o padrão do catálogo", () => {
    const setDataCatalogMode = vi.fn();
    const setDataCatalogModalOpen = vi.fn();
    const setDataCatalogAnchor = vi.fn();
    const openDataCatalog = (
      mode: "insert" | "replace" = "insert",
      options?: OpenDataCatalogOptions,
    ) => {
      setDataCatalogMode(mode);
      setDataCatalogAnchor(options?.anchor ?? null);
      setDataCatalogModalOpen(true);
    };

    openDataCatalog();

    expect(setDataCatalogMode).toHaveBeenCalledWith("insert");
    expect(setDataCatalogAnchor).toHaveBeenCalledWith(null);
    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(true);
  });
});
