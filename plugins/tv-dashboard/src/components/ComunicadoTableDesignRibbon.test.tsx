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
    selectedBlocks: [tableBlock],
    selectedTablePart: null,
    selectedKpiPart: null,
    selectedChartPart: null,
    selectedInputPart: null,
    blocks: [tableBlock],
    config: { blocks: [tableBlock], customFonts: [] },
    lastUngroupedIds: [],
    updateSelected,
    updateSelectedStyle: vi.fn(),
    updateSelectedTextFormatStyle: vi.fn(),
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
    editingTextId: null,
    textEditSelection: null,
    lastPartialTextEditSelection: null,
    textEditSelectionStyle: null,
    toggleEditingTextRunStyle: vi.fn(),
    applyEditingTextRunStylePatch: vi.fn(),
    textEditListSelection: null,
    toggleSelectedTextListType: vi.fn(),
    textEditNamedStyleSelection: null,
    applySelectedNamedTextStyle: vi.fn(),
    uploadCustomFont: vi.fn(),
    uploading: false,
    background: "#ffffff",
  }),
}));

describe("ComunicadoTableDesignRibbon", () => {
  it("oferece galeria de estilos colapsada e seção Fonte global da tabela", () => {
    render(<ComunicadoTableDesignRibbon />);
    expect(screen.getByRole("button", { name: "Galeria de estilos de tabela" })).toBeTruthy();
    expect(screen.getByText("Estilos")).toBeTruthy();
    expect(screen.queryByRole("list", { name: "Estilos de tabela" })).toBeNull();
    expect(screen.getByLabelText("Família da fonte")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Negrito" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Itálico" })).toBeTruthy();
  });
});
