import { fireEvent, render, screen } from "@testing-library/react";
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
    updateSelected,
    selectTablePart,
    openDataPanel,
    requestRibbonTab: vi.fn(),
  }),
}));

describe("ComunicadoTableDesignRibbon", () => {
  it("oferece strip de estilos com Mais e Forma seleciona moldura", () => {
    render(<ComunicadoTableDesignRibbon />);
    expect(screen.getByRole("list", { name: "Estilos de tabela" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Galeria de estilos de tabela" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /^Forma$/i }));
    expect(selectTablePart).toHaveBeenCalledWith("t1", { kind: "frame" });
  });
});
