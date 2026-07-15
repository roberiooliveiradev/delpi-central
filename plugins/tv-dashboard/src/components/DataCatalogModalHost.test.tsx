import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("./DataRoutesSidePanel", () => ({
  DataRoutesSidePanel: () => <div data-testid="data-routes-panel">painel</div>,
}));

const setDataCatalogModalOpen = vi.fn();
const setDataCatalogMode = vi.fn();
const setDataCatalogAnchor = vi.fn();
const setDataPanelIntent = vi.fn();

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    dataCatalogModalOpen: true,
    setDataCatalogModalOpen,
    dataCatalogMode: "insert" as const,
    setDataCatalogMode,
    dataCatalogAnchor: null,
    setDataCatalogAnchor,
    setDataPanelIntent,
  }),
}));

import { DataCatalogModalHost } from "./DataCatalogModalHost";

describe("DataCatalogModalHost (popover)", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renderiza popover do catálogo com o painel de rotas", () => {
    render(<DataCatalogModalHost />);

    const dialog = document.querySelector(".td-data-catalog-popover");
    expect(dialog).toBeTruthy();
    expect(dialog?.getAttribute("role")).toBe("dialog");
    expect(dialog?.getAttribute("aria-label")).toBe("Fontes de dados");
    expect(screen.getByTestId("data-routes-panel")).toBeTruthy();
  });

  it("fecha pelo botão Fechar e limpa âncora/modo", () => {
    render(<DataCatalogModalHost />);

    fireEvent.click(screen.getByLabelText("Fechar catálogo"));

    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(false);
    expect(setDataCatalogMode).toHaveBeenCalledWith("insert");
    expect(setDataCatalogAnchor).toHaveBeenCalledWith(null);
  });

  it("fecha com Escape", () => {
    render(<DataCatalogModalHost />);

    fireEvent.keyDown(window, { key: "Escape" });

    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(false);
  });
});
