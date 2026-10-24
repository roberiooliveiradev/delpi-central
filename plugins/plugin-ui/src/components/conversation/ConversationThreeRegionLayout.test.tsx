import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
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
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(true);
      expect(screen.getByRole("button", { name: "Recolher conversas" })).toBe(document.activeElement);
      expect(screen.getByRole("button", { name: "Categorias" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeTruthy();
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect(document.activeElement).toBe(screen.getByRole("button", { name: "Expandir conversas" }));
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      fireEvent.click(screen.getByRole("button", { name: "Fechar navegação" }));
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect(container.contains(input)).toBe(true);
      expect((input as HTMLInputElement).value).toBe("Texto intacto");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("E05 keeps one floating context beside the rail without replacing the compact workspace", () => {
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
        left={<p>Navegação</p>}
        right={<p>Detalhes do contexto</p>}
        center={({ rightToggle }) => <div>{rightToggle}<input aria-label="Rascunho E05" defaultValue="Preservado E05" /></div>}
      />);
      const draft = screen.getByRole("textbox", { name: "Rascunho E05" });
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact.delpi-ui-conversation-three-region--with-rail")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
      expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
      expect(screen.getByText("Detalhes do contexto")).toBeTruthy();
      expect(container.querySelectorAll(".delpi-ui-conversation-three-region__context-popover")).toHaveLength(1);
      expect(container.querySelector(".delpi-ui-conversation-three-region__right")).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__category-rail")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Fechar painel de contexto" }));
      expect(screen.queryByRole("dialog", { name: "Contexto da conversa" })).toBeNull();
      expect(container.contains(draft)).toBe(true);
      expect((draft as HTMLInputElement).value).toBe("Preservado E05");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("E06 keeps only one compact overlay open, restores focus and preserves draft", () => {
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
        rail={<button type="button">Categorias E06</button>}
        left={<p>Painel E06</p>}
        right={<p>Contexto E06</p>}
        center={({ rightToggle }) => <div>{rightToggle}<input aria-label="Draft E06" defaultValue="sem perder" /></div>}
      />);
      const draft = screen.getByRole("textbox", { name: "Draft E06" });
      const trigger = screen.getByRole("button", { name: "Abrir contexto" });
      fireEvent.click(trigger);
      expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
      expect(document.activeElement).toBe(screen.getByRole("button", { name: "Fechar painel de contexto" }));
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(screen.queryByRole("dialog", { name: "Contexto da conversa" })).toBeNull();
      expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeTruthy();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(true);
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect(container.contains(draft)).toBe(true);
      expect((draft as HTMLInputElement).value).toBe("sem perder");
      fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("dialog", { name: "Contexto da conversa" })).toBeNull();
      expect(document.activeElement).toBe(trigger);
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("T05 closes the compact drawer via backdrop and restores an interactive center", () => {
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
        rail={<button type="button">Rail T05</button>}
        left={<p>Painel T05</p>}
        center={<input aria-label="Draft T05" defaultValue="backdrop-ok" />}
      />);
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(container.querySelector('[data-drawer="true"]')).toBeTruthy();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(true);
      fireEvent.click(screen.getByRole("button", { name: "Fechar navegação" }));
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector('[data-drawer="true"]')).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect((screen.getByRole("textbox", { name: "Draft T05" }) as HTMLInputElement).value).toBe("backdrop-ok");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("T07 keeps Tab and Shift+Tab inside the compact drawer focus cycle", () => {
    const rect = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(
      () => ({ width: 375, height: 667, top: 0, left: 0, right: 375, bottom: 667, x: 0, y: 0, toJSON: () => ({}) } as DOMRect),
    );
    const previousRects = HTMLElement.prototype.getClientRects;
    HTMLElement.prototype.getClientRects = function getClientRects() {
      const box = { width: 40, height: 40, top: 0, left: 0, right: 40, bottom: 40, x: 0, y: 0, toJSON: () => ({}) } as DOMRect;
      return {
        length: 1,
        item: () => box,
        0: box,
        [Symbol.iterator]: function* () { yield box; },
      } as unknown as DOMRectList;
    };
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
        rail={<button type="button">Rail T07</button>}
        left={<button type="button">Item painel</button>}
        center={<input aria-label="Draft T07" defaultValue="fora do ciclo" />}
      />);
      const draft = screen.getByRole("textbox", { name: "Draft T07" });
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(true);
      const railItem = screen.getByRole("button", { name: "Rail T07" });
      const panelItem = screen.getByRole("button", { name: "Item painel" });
      panelItem.focus();
      fireEvent.keyDown(document, { key: "Tab" });
      expect(document.activeElement).toBe(railItem);
      expect(document.activeElement).not.toBe(draft);
      railItem.focus();
      fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
      expect(document.activeElement).toBe(panelItem);
      expect(document.activeElement).not.toBe(draft);
    } finally {
      HTMLElement.prototype.getClientRects = previousRects;
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("T09 opening Context while the drawer is open closes the drawer", () => {
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
        rail={<button type="button">Rail T09</button>}
        left={<p>Painel T09</p>}
        right={<p>Contexto T09</p>}
        center={({ rightToggle }) => <div>{rightToggle}<input aria-label="Draft T09" defaultValue="ok" /></div>}
      />);
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeTruthy();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(true);
      fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
      expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector('[data-drawer="true"]')).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect((screen.getByRole("textbox", { name: "Draft T09" }) as HTMLInputElement).value).toBe("ok");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

  it("T12 reconciles compact overlays when the host container resizes", () => {
    let hostWidth = 375;
    let observerCallback: ResizeObserverCallback | null = null;
    const rect = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(
      () => ({ width: hostWidth, height: 667, top: 0, left: 0, right: hostWidth, bottom: 667, x: 0, y: 0, toJSON: () => ({}) } as DOMRect),
    );
    const previousObserver = globalThis.ResizeObserver;
    class ControllableObserver {
      constructor(callback: ResizeObserverCallback) { observerCallback = callback; }
      observe() { observerCallback?.([], this as unknown as ResizeObserver); }
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("ResizeObserver", ControllableObserver);
    try {
      const { container } = render(<ConversationThreeRegionLayout
        rail={<button type="button">Rail T12</button>}
        left={<p>Painel T12</p>}
        right={<p>Contexto T12</p>}
        center={({ rightToggle }) => <div>{rightToggle}<input aria-label="Draft T12" defaultValue="resize-ok" /></div>}
      />);
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
      expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeTruthy();
      hostWidth = 1280;
      act(() => { observerCallback?.([], {} as ResizeObserver); });
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact")).toBeNull();
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector(".delpi-ui-conversation-three-region__left")).toBeTruthy();
      expect(container.querySelector(".delpi-ui-conversation-three-region__center")?.hasAttribute("inert")).toBe(false);
      expect((screen.getByRole("textbox", { name: "Draft T12" }) as HTMLInputElement).value).toBe("resize-ok");
      hostWidth = 375;
      act(() => { observerCallback?.([], {} as ResizeObserver); });
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact")).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Fechar navegação" })).toBeNull();
      expect(container.querySelector('[data-drawer="true"]')).toBeNull();
      expect((screen.getByRole("textbox", { name: "Draft T12" }) as HTMLInputElement).value).toBe("resize-ok");
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });

});

describe("ConversationThreeRegionLayout RIGHTRAIL", () => {
  it("RR-01 renders an integrated complementary region, not a floating popover", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        rightVariant="rail"
        rightOpen={true}
        right={<p>Conteúdo global</p>}
        center={<p>Conversa</p>}
      />);
    const rail = container.querySelector(".delpi-ui-conversation-three-region__right-rail");
    expect(rail).toBeTruthy();
    expect(rail?.getAttribute("role")).toBe("complementary");
    expect(rail?.getAttribute("data-open")).toBe("true");
    expect(rail?.getAttribute("aria-label")).toBe("Contexto da conversa");
    expect(container.querySelector(".delpi-ui-conversation-three-region__context-popover")).toBeNull();
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
  });

  it("RR-02 has no light-dismiss — clicking the center keeps the rail open", () => {
    const onRightOpenChange = vi.fn();
    const { container } = render(
      <ConversationThreeRegionLayout
        rightVariant="rail"
        right={<p>Conteúdo global</p>}
        center={(controls) => <>{controls.rightToggle}<p>Conversa</p></>}
        onRightOpenChange={onRightOpenChange}
      />);
    const toggle = screen.getByRole("button", { name: "Abrir contexto" });
    fireEvent.click(toggle);
    expect(onRightOpenChange).toHaveBeenLastCalledWith(true);
    expect(container.querySelector('.delpi-ui-conversation-three-region__right-rail[data-open="true"]')).toBeTruthy();
    fireEvent.pointerDown(container.querySelector(".delpi-ui-conversation-three-region__center")!);
    expect(container.querySelector('.delpi-ui-conversation-three-region__right-rail[data-open="true"]')).toBeTruthy();
    expect(onRightOpenChange).toHaveBeenLastCalledWith(true);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onRightOpenChange).toHaveBeenLastCalledWith(false);
  });

  it("RR-10 toggle, close button and ARIA wiring stay correct", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        rightVariant="rail"
        right={<p>Conteúdo global</p>}
        center={(controls) => <>{controls.rightToggle}<p>Conversa</p></>}
      />);
    const toggle = screen.getByRole("button", { name: "Abrir contexto" });
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    const rail = container.querySelector(".delpi-ui-conversation-three-region__right-rail");
    expect(toggle.getAttribute("aria-controls")).toBe(rail?.id);
    fireEvent.click(screen.getByRole("button", { name: "Fechar painel de contexto" }));
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(rail?.getAttribute("data-open")).toBe("false");
    expect(rail?.getAttribute("aria-hidden")).toBe("true");
  });

  it("RR-11 compact host falls back to the floating surface even with rail variant", () => {
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
      const { container } = render(
        <ConversationThreeRegionLayout
          rightVariant="rail"
          rightOpen={true}
          right={<p>Conteúdo global</p>}
          center={<p>Conversa</p>}
        />);
      expect(container.querySelector(".delpi-ui-conversation-three-region--compact")).toBeTruthy();
      expect(container.querySelector(".delpi-ui-conversation-three-region__right-rail")).toBeNull();
      expect(container.querySelector('.delpi-ui-conversation-three-region__context-popover[data-open="true"]')).toBeTruthy();
    } finally {
      rect.mockRestore();
      vi.stubGlobal("ResizeObserver", previousObserver);
    }
  });
});
