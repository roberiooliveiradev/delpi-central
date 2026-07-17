import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FixedPanelPortal } from "./FixedPanelPortal";

afterEach(cleanup);

describe("FixedPanelPortal", () => {
  it("não renderiza quando fechado ou sem posição", () => {
    const { rerender } = render(
      <FixedPanelPortal open={false} position={{ x: 10, y: 10 }} role="menu" aria-label="Painel">
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    expect(screen.queryByRole("menu", { name: "Painel" })).toBeNull();

    rerender(
      <FixedPanelPortal open position={null} role="menu" aria-label="Painel">
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    expect(screen.queryByRole("menu", { name: "Painel" })).toBeNull();
  });

  it("renderiza no body posicionado por ponto com role/aria", () => {
    render(
      <FixedPanelPortal open position={{ x: 24, y: 48 }} role="menu" aria-label="Painel">
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    const panel = screen.getByRole("menu", { name: "Painel" });
    expect(panel).toBeTruthy();
    expect(panel.parentElement?.parentElement).toBe(document.body);
    expect(panel.style.position).toBe("fixed");
  });

  it("aplica className do painel e o escopo do plugin no wrapper", () => {
    render(
      <FixedPanelPortal
        open
        position={{ x: 0, y: 0 }}
        role="menu"
        aria-label="Painel"
        className="delpi-ui-context-menu"
        portalScopeClassName="dashboard-tv-dashboard"
      >
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    const panel = screen.getByRole("menu", { name: "Painel" });
    expect(panel.classList.contains("delpi-ui-context-menu")).toBe(true);
    expect(panel.parentElement?.classList.contains("dashboard-tv-dashboard")).toBe(true);
  });

  it("fecha ao clicar fora (pointerdown em captura)", () => {
    const onDismiss = vi.fn();
    render(
      <FixedPanelPortal open position={{ x: 0, y: 0 }} role="menu" aria-label="Painel" onDismiss={onDismiss}>
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    fireEvent.pointerDown(document.body);
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("não fecha ao clicar dentro do painel", () => {
    const onDismiss = vi.fn();
    render(
      <FixedPanelPortal open position={{ x: 0, y: 0 }} role="menu" aria-label="Painel" onDismiss={onDismiss}>
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    fireEvent.pointerDown(screen.getByRole("button", { name: "Ação" }));
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it("fecha ao pressionar Escape", () => {
    const onDismiss = vi.fn();
    render(
      <FixedPanelPortal open position={{ x: 0, y: 0 }} role="menu" aria-label="Painel" onDismiss={onDismiss}>
        <button type="button">Ação</button>
      </FixedPanelPortal>,
    );
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
