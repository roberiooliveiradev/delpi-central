import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoTableViewBlock } from "@delpi/tv-dashboard-presentation";

import { TableStyleOptionsSection } from "./selectionSections/TableDesignSections";

const tableBlock: ComunicadoTableViewBlock = {
  id: "t1",
  type: "table_view",
  frame: { x: 0, y: 0, w: 40, h: 30 },
  tablePreset: "grid",
  tableOptions: {
    showHeader: true,
    showBorders: true,
    showTitle: true,
  },
};

const selectTablePart = vi.fn();
const updateSelected = vi.fn();
const setSelectionPanelTab = vi.fn();

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    selected: tableBlock,
    selectedTablePart: null,
    selectedTableParts: [],
    updateSelected,
    updateSelectedStyle: vi.fn(),
    selectTablePart,
    openDataPanel: vi.fn(),
    setSelectionPanelTab,
  }),
}));

afterEach(() => {
  cleanup();
  selectTablePart.mockClear();
  updateSelected.mockClear();
  setSelectionPanelTab.mockClear();
});

describe("TableStyleOptionsSection", () => {
  it("ribbon oferece Adicionar elemento com menu cascata (ícone + subopções)", () => {
    render(<TableStyleOptionsSection layout="ribbon" />);
    fireEvent.click(screen.getByRole("button", { name: /Adicionar\s*elemento/i }));
    expect(document.querySelector(".td-chart-add-element")).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Título da tabela/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Linha de cabeçalho/i })).toBeTruthy();
  });

  it("flyout Mostrar/Ocultar aplica opções sem selecionar parte", () => {
    render(<TableStyleOptionsSection layout="ribbon" />);
    fireEvent.click(screen.getByRole("button", { name: /Adicionar\s*elemento/i }));
    fireEvent.mouseEnter(screen.getByRole("menuitem", { name: /Linha de cabeçalho/i }).closest("li")!);
    fireEvent.click(screen.getByRole("menuitemcheckbox", { name: /Ocultar/i }));
    expect(updateSelected).toHaveBeenCalled();
    expect(selectTablePart).not.toHaveBeenCalled();
  });

  it("painel oferece o mesmo botão Adicionar elemento", () => {
    render(<TableStyleOptionsSection layout="pane" />);
    fireEvent.click(screen.getByRole("button", { name: /Adicionar\s*elemento/i }));
    expect(document.querySelector(".td-chart-add-element")).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Bordas/i })).toBeTruthy();
  });
});
