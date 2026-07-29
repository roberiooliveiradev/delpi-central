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

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    selected: tableBlock,
    selectedTablePart: null,
    updateSelected,
    updateSelectedStyle: vi.fn(),
    selectTablePart,
    openDataPanel: vi.fn(),
  }),
}));

afterEach(() => {
  cleanup();
  selectTablePart.mockClear();
  updateSelected.mockClear();
});

describe("TableStyleOptionsSection", () => {
  it("usa tiles com ícones (sem checkbox) e toggle não seleciona parte", () => {
    render(<TableStyleOptionsSection layout="pane" />);
    expect(screen.queryByRole("checkbox")).toBeNull();
    expect(screen.getByRole("group", { name: "Opções de estilo" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cabeçalho" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Cabeçalho" }).querySelector(".td-ribbon-tile__icon")!);
    expect(updateSelected).toHaveBeenCalled();
    expect(selectTablePart).not.toHaveBeenCalled();
  });

  it("clique no texto do rótulo seleciona a parte no palco", () => {
    render(<TableStyleOptionsSection layout="pane" />);
    const label = screen
      .getByRole("button", { name: "Cabeçalho" })
      .querySelector(".td-ribbon-tile__label");
    expect(label).toBeTruthy();
    fireEvent.click(label!);
    expect(selectTablePart).toHaveBeenCalledWith("t1", { kind: "header" });
    expect(updateSelected).not.toHaveBeenCalled();
  });
});
