import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CanvasTableDataMenu } from "./CanvasTableDataMenu";

afterEach(() => cleanup());

describe("CanvasTableDataMenu", () => {
  it("bloco usa chrome add-element e labels de fonte/colunas", () => {
    const onSelect = vi.fn();
    const { container } = render(<CanvasTableDataMenu onSelect={onSelect} />);
    expect(container.querySelector(".td-chart-add-element")).toBeTruthy();
    expect(screen.getByRole("menu", { name: "Dados da Grade" })).toBeTruthy();
    fireEvent.click(screen.getByRole("menuitem", { name: /Selecionar fonte/i }));
    expect(onSelect).toHaveBeenCalledWith("source");
  });

  it("célula expõe vínculo da célula", () => {
    render(<CanvasTableDataMenu variant="cell" onSelect={vi.fn()} />);
    expect(screen.getByRole("menu", { name: "Dados da célula da Grade" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Vínculo da célula/i })).toBeTruthy();
  });
});
