import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ComunicadoTableViewBlock } from "@delpi/tv-dashboard-presentation";

import { ComunicadoTableDesignRibbon } from "./ComunicadoTableDesignRibbon";

const tableBlock: ComunicadoTableViewBlock = {
  id: "t1",
  type: "table_view",
  frame: { x: 0, y: 0, w: 40, h: 30 },
  tablePreset: "grid",
  tableOptions: {
    showHeader: true,
    showBorders: true,
    headerBg: "#e2e8f0",
    cellBg: "#ffffff",
    borderColor: "#cbd5e1",
  },
};

const selectTablePart = vi.fn();
const updateSelected = vi.fn();
const openDataPanel = vi.fn();

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    selected: tableBlock,
    selectedIds: [tableBlock.id],
    selectedTablePart: null,
    blocks: [tableBlock],
    config: { blocks: [tableBlock], customFonts: [] },
    lastUngroupedIds: [],
    updateSelected,
    updateSelectedStyle: vi.fn(),
    selectTablePart,
    openDataPanel,
    requestRibbonTab: vi.fn(),
    groupSelected: vi.fn(),
    ungroupSelected: vi.fn(),
    regroupLastUngroup: vi.fn(),
    bringForward: vi.fn(),
    sendBackward: vi.fn(),
    bringToFront: vi.fn(),
    sendToBack: vi.fn(),
  }),
}));

describe("ComunicadoTableDesignRibbon", () => {
  it("oferece strip de estilos e seção Fonte global da tabela", () => {
    render(<ComunicadoTableDesignRibbon />);
    expect(screen.getByRole("list", { name: "Estilos de tabela" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Galeria de estilos de tabela" })).toBeTruthy();
    expect(screen.getByLabelText("Família da fonte da tabela")).toBeTruthy();
    expect(screen.getByRole("group", { name: "Tamanho da fonte da tabela" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Negrito" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Itálico" })).toBeTruthy();
  });
});
