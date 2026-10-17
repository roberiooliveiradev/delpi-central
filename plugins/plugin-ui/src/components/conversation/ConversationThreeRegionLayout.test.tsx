import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationThreeRegionLayout } from "./ConversationThreeRegionLayout";
afterEach(cleanup);
describe("ConversationThreeRegionLayout R2", () => {
  it("retains the left navigation as a rail while the center remains mounted", () => {
    const { container } = render(
      <ConversationThreeRegionLayout left={({ collapsed }) => <span>{collapsed ? "Rail" : "Menu"}</span>}
        right={<span>Projeções</span>}
        center={(controls) => <header>{controls.leftToggle} <span>Conversa estável</span> {controls.rightToggle}</header>} />,
    );
    const center = screen.getByText("Conversa estável");
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    const collapse = screen.getByRole("button", { name: "Recolher conversas" });
    expect(collapse.className).toContain("delpi-ui-conversation-three-region__rail-toggle");
    expect(collapse.className).toContain("delpi-ui-conversation-three-region__chrome-icon");
    expect(collapse.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(collapse);
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByText("Rail")).toBeTruthy();
    const expand = screen.getByRole("button", { name: "Expandir conversas" });
    expect(expand.className).toContain("delpi-ui-conversation-three-region__rail-toggle");
    expect(expand.className).toContain("delpi-ui-conversation-three-region__chrome-icon");
    expect(expand.getAttribute("aria-expanded")).toBe("false");
    expect(container.contains(center)).toBe(true);
  });
  it("opens a floating context dialog without adding a right-hand column", () => {
    const { container } = render(<ConversationThreeRegionLayout
      left={<span>Menu</span>} right={<span>Contexto real</span>}
      center={({ rightToggle }) => <header>{rightToggle}</header>} />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
    expect(screen.getByText("Contexto real")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-conversation-three-region__right")).toBeNull();
    const close = screen.getByRole("button", { name: "Fechar painel de contexto" });
    expect(close.className).toContain("delpi-ui-conversation-three-region__context-close");
    expect(close.className).toContain("delpi-ui-conversation-three-region__chrome-icon");
    fireEvent.click(close);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("hides context control when unavailable", () => {
    render(<ConversationThreeRegionLayout rightAvailable={false} right={<span>Hidden</span>}
      center={({ rightToggle }) => <header>{rightToggle}</header>} />);
    expect(screen.queryByRole("button", { name: "Abrir contexto" })).toBeNull();
  });
  it("keeps floating surface mounted for exit motion but inaccessible while closed", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        left={({ collapsed }) => <span>{collapsed ? "Rail" : "Sidebar"}</span>}
        right={<span>Detalhes autorizados</span>}
        center={({ rightToggle }) => <header>{rightToggle}</header>}
      />,
    );
    const surface = container.querySelector(".delpi-ui-conversation-three-region__context-popover");
    expect(surface).toBeTruthy();
    expect(surface?.getAttribute("data-open")).toBe("false");
    expect(surface?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(surface?.getAttribute("data-open")).toBe("true");
    expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Fechar painel de contexto" }));
    expect(surface?.getAttribute("data-open")).toBe("false");
    expect(surface?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("Detalhes autorizados")).toBeNull();
  });

  it("E02 keeps a persistent category rail beside the panel while retaining legacy no-rail behavior", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        rail={<button type="button">Categorias persistentes</button>}
        left={<span>Painel existente</span>}
        center={<input aria-label="Draft" defaultValue="Preservado" />}
      />,
    );
    const draft = screen.getByRole("textbox", { name: "Draft" });
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__category-rail")).toHaveLength(1);
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Categorias persistentes" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Categorias persistentes" })).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Expandir conversas" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(1);
    expect(container.contains(draft)).toBe(true);
    expect((draft as HTMLInputElement).value).toBe("Preservado");
  });

  it("E04 opens a compact drawer with backdrop, Escape dismissal and focus return", () => {
    const rect = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(
      () => ({ width: 375, height: 667, top: 0, left: 0, right: 375, bottom: 667, x: 0, y: 0, toJSON: () => ({}) } as DOMRect),
    );
    const previousObserver = globalThis.ResizeObserver;
    class SizedObserver {
      private callback: ResizeObserverCallback;
      constructor(callback: ResizeObserverCallback) { this.callback = callback; }
      observe() { this.callback([], this as unknown as ResizeObserver); }
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("ResizeObserver", SizedObserver);
    try {
      const { container } = render(<ConversationThreeRegionLayout
        rail={<button type="button">Categorias</button>}
        left={<p>Conteúdo da navegação</p>}
        center={<input aria-label="Rascunho mobile" defaultValue="Texto intacto" />}
      />);
      const input = screen.getByRole("textbox", { name: "Rascunho mobile" });
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact")).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeTruthy();
      expect(container.querySelector('[data-drawer="true"]')).toBeTruthy();
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(document.activeElement).toBe(screen.getByRole("button", { name: "Expandir conversas" }));
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      fireEvent.click(screen.getByRole("button", { name: "Fechar navegação" }));
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.contains(input)).toBe(true);
      expect((input as HTMLInputElement).value).toBe("Texto intacto");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

});
