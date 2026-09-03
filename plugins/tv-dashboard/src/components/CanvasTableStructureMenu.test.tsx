import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CanvasTableStructureMenu } from "./CanvasTableStructureMenu";

afterEach(() => cleanup());

describe("CanvasTableStructureMenu", () => {
  it("renderiza chrome chart e 6+ ações sem updateBlock", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <CanvasTableStructureMenu onSelect={onSelect} canMerge canUnmerge />,
    );
    expect(container.querySelector(".td-chart-add-element")).toBeTruthy();
    expect(screen.getByRole("menu", { name: "Estrutura da Grade" })).toBeTruthy();
    const items = screen.getAllByRole("menuitem");
    expect(items.length).toBeGreaterThanOrEqual(6);
    fireEvent.click(screen.getByRole("menuitem", { name: /Inserir linha acima/i }));
    expect(onSelect).toHaveBeenCalledWith("insert-row-before");
    expect(container.innerHTML).not.toContain("updateBlock");
  });
});
