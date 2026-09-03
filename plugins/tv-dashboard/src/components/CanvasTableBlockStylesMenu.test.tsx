import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CanvasTableBlockStylesMenu } from "./CanvasTableBlockStylesMenu";

afterEach(() => cleanup());

describe("CanvasTableBlockStylesMenu", () => {
  it("usa chrome td-chart-style-menu e dispara callback de preset", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <CanvasTableBlockStylesMenu
        options={{ bandedRows: true, borderStyle: "all", headerStyle: "subtle" }}
        onSelect={onSelect}
      />,
    );
    expect(container.querySelector(".td-chart-style-menu")).toBeTruthy();
    expect(container.innerHTML).not.toContain("td-deck-ribbon__float-panel");
    fireEvent.click(screen.getByRole("menuitemradio", { name: /^Grade$/i }));
    expect(onSelect).toHaveBeenCalledWith("preset-grid");
  });
});
