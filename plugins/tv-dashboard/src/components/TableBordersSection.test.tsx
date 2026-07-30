import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoTableViewBlock } from "@delpi/tv-dashboard-presentation";

import { TableBordersSection } from "./selectionSections/TableDesignSections";

const tableBlock: ComunicadoTableViewBlock = {
  id: "t1",
  type: "table_view",
  frame: { x: 0, y: 0, w: 40, h: 30 },
  tableOptions: { showHeader: true, showBorders: true },
  style: { borderRadius: 8, opacity: 1 },
};

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    selected: tableBlock,
    selectedIds: [tableBlock.id],
    selectedBlocks: [tableBlock],
    selectedTablePart: null,
    selectedKpiPart: null,
    selectedChartPart: null,
    selectedInputPart: null,
    updateSelected: vi.fn(),
    updateSelectedStyle: vi.fn(),
    selectTablePart: vi.fn(),
    openDataPanel: vi.fn(),
    setSelectionPanelTab: vi.fn(),
  }),
}));

afterEach(() => cleanup());

describe("TableBordersSection Forma", () => {
  it("expõe Forma na band e Raio/Opacidade no popover Ajuste", () => {
    render(<TableBordersSection layout="ribbon" />);
    expect(screen.getByRole("button", { name: "Forma" })).toBeTruthy();
    const adjust = screen.getByRole("button", { name: "Ajuste" });
    expect(adjust).toBeTruthy();
    expect(screen.queryByLabelText("Cantos arredondados em pixels")).toBeNull();

    fireEvent.click(adjust);
    expect(screen.getByLabelText("Cantos arredondados em pixels")).toBeTruthy();
    expect(screen.getByLabelText("Opacidade")).toBeTruthy();
  });
});
