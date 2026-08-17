import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RouteChip, routeChipBemClasses } from "./RouteChip";

afterEach(() => {
  cleanup();
});

describe("RouteChip", () => {
  it("navega no clique do corpo e remove sem propagar (pinned)", () => {
    const onNavigate = vi.fn();
    const onRemove = vi.fn();
    render(
      <RouteChip
        classNames={routeChipBemClasses("cm")}
        label="Minhas tarefas"
        tone="pinned"
        onNavigate={onNavigate}
        onRemove={onRemove}
        removeLabel="Remover dos favoritos"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Minhas tarefas/ }));
    expect(onNavigate).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Remover dos favoritos" }));
    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(onNavigate).toHaveBeenCalledTimes(1);
  });

  it("pinned usa Star e classes dual-class; recent sem remove", () => {
    const { container, rerender } = render(
      <RouteChip
        classNames={routeChipBemClasses("cm")}
        label="Favorito"
        tone="pinned"
        onNavigate={() => undefined}
        onRemove={() => undefined}
      />,
    );
    expect(container.querySelector(".delpi-ui-route-chip--pinned")).toBeTruthy();
    expect(container.querySelector("svg")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Remover dos favoritos" })).toBeTruthy();

    rerender(
      <RouteChip
        classNames={routeChipBemClasses("cm")}
        label="Recente"
        tone="recent"
        leadingIcon={<span data-testid="recent-icon">R</span>}
        onNavigate={() => undefined}
      />,
    );
    expect(container.querySelector(".delpi-ui-route-chip--recent")).toBeTruthy();
    expect(container.querySelector('[data-testid="recent-icon"]')).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Remover dos favoritos" })).toBeNull();
  });
});
