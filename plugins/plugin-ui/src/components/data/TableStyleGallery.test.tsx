import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TableStyleRibbonStrip, type TableStylePreset } from "./TableStyleGallery";

afterEach(() => {
  cleanup();
});

const PRESETS: TableStylePreset[] = [
  {
    id: "light-a",
    label: "Clara A",
    category: "light",
    headerBg: "#e2e8f0",
    cellBg: "#ffffff",
    borderColor: "#cbd5e1",
  },
  {
    id: "medium-a",
    label: "Média A",
    category: "medium",
    headerBg: "#089bdb",
    cellBg: "#ffffff",
    borderColor: "#e2e8f0",
  },
  {
    id: "dark-a",
    label: "Escura A",
    category: "dark",
    headerBg: "#003866",
    cellBg: "#0b1220",
    borderColor: "#1e3a5f",
  },
];

describe("TableStyleRibbonStrip", () => {
  it("mostra thumbs e aplica preset ao clicar", () => {
    const onSelect = vi.fn();
    render(
      <TableStyleRibbonStrip maxVisible={2} presets={PRESETS} onSelect={onSelect} />,
    );
    const thumbs = screen.getAllByRole("listitem");
    expect(thumbs.length).toBeGreaterThanOrEqual(2);
    fireEvent.click(thumbs[1]!);
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "medium-a" }));
    expect(within(screen.getByRole("list")).getByText("Mais")).toBeTruthy();
  });

  it("abre galeria Mais em portal e limpa", () => {
    const onSelect = vi.fn();
    const onClear = vi.fn();
    render(
      <TableStyleRibbonStrip presets={PRESETS} onSelect={onSelect} onClear={onClear} />,
    );
    const strip = screen.getByRole("list", { name: "Estilos de tabela" });
    const more = within(strip).getByText("Mais");
    fireEvent.click(more);
    const gallery = screen.getByRole("menu", { name: "Galeria de estilos de tabela" });
    expect(within(gallery).getByText("Escuros")).toBeTruthy();
    fireEvent.click(within(gallery).getByLabelText("Escura A"));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "dark-a" }));

    fireEvent.click(more);
    fireEvent.click(
      within(screen.getByRole("menu", { name: "Galeria de estilos de tabela" })).getByRole(
        "button",
        { name: "Limpar tabela" },
      ),
    );
    expect(onClear).toHaveBeenCalled();
  });
});
