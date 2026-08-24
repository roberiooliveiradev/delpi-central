import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen, within, act } from "@testing-library/react";

import { TopBar, topBarBemClasses } from "./TopBar";
import { underlineNavBemClasses } from "./UnderlineNav";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("TopBar", () => {
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    });
  });

  it("emite dual-class BEM com modifiers", () => {
    const cn = topBarBemClasses("cm");
    expect(cn.root).toContain("cm-topbar");
    expect(cn.root).toContain("delpi-ui-topbar");
    expect(cn.row).toContain("delpi-ui-topbar__row");
    expect(cn.collapseToggle).toContain("delpi-ui-topbar__collapse-toggle");
  });

  it("compõe UnderlineNav e slot de actions", () => {
    const onSelect = vi.fn();
    render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="home"
        items={[
          { id: "home", label: "Início", onSelect },
          { id: "orders", label: "Pedidos", onSelect },
        ]}
        actions={<span>Escopo</span>}
      />,
    );
    expect(screen.getByRole("navigation", { name: "Navegação" })).toBeTruthy();
    expect(screen.getByText("Escopo")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Pedidos" }));
    expect(onSelect).toHaveBeenCalled();
  });

  it("renderiza slot secondary entre nav e actions", () => {
    render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="home"
        items={[{ id: "home", label: "Início", onSelect: vi.fn() }]}
        secondary={<span>Favoritos</span>}
        actions={<span>Usuário</span>}
      />,
    );
    expect(screen.getByText("Favoritos")).toBeTruthy();
    expect(screen.getByText("Usuário")).toBeTruthy();
    const cn = topBarBemClasses("cm");
    expect(cn.secondary).toContain("delpi-ui-topbar__secondary");
  });

  it("aplica modifier surface sob demanda", () => {
    const { container } = render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="home"
        surface
        items={[{ id: "home", label: "Início", onSelect: vi.fn() }]}
      />,
    );
    expect(container.firstElementChild?.className).toContain("delpi-ui-topbar--surface");
  });

  it("rail: recolhe para título + expand e persiste", () => {
    render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="rooms"
        collapsible
        collapseMode="rail"
        storageKey="test:topbar"
        collapseLabel="Recolher navegação"
        expandLabel="Expandir navegação"
        items={[
          { id: "home", label: "Início", onSelect: vi.fn() },
          { id: "rooms", label: "Sala de interação", onSelect: vi.fn() },
        ]}
        secondary={<span>Favoritos</span>}
        actions={<span>Usuário</span>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Recolher navegação" }));
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByText("Favoritos")).toBeNull();
    expect(screen.getByText("Sala de interação")).toBeTruthy();
    expect(storage.get("test:topbar")).toBe("1");

    fireEvent.click(screen.getByRole("button", { name: "Expandir navegação" }));
    expect(screen.getByRole("navigation")).toBeTruthy();
    expect(storage.get("test:topbar")).toBe("0");
  });

  it("hamburger manual: mantém secondary/actions e abre menu no portal", () => {
    const onRooms = vi.fn();
    render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="home"
        collapsible
        collapseMode="hamburger"
        collapseTrigger="manual"
        defaultCollapsed
        menuLabel="Menu de navegação"
        expandLabel="Expandir navegação"
        items={[
          { id: "home", label: "Início", onSelect: vi.fn() },
          { id: "rooms", label: "Sala", onSelect: onRooms, count: 3 },
        ]}
        secondary={<span>Favoritos</span>}
        actions={<span>Usuário</span>}
      />,
    );

    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.getByText("Favoritos")).toBeTruthy();
    expect(screen.getByText("Usuário")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Menu de navegação" }));
    const menu = screen.getByRole("menu", { name: "Menu de navegação" });
    expect(within(menu).getByRole("menuitem", { name: /Sala/ })).toBeTruthy();
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Sala/ }));
    expect(onRooms).toHaveBeenCalled();
  });

  it("hamburger overflow: colapsa quando measure excede host", async () => {
    let callback: ResizeObserverCallback | null = null;
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn(function ResizeObserverStub(this: ResizeObserver, cb: ResizeObserverCallback) {
        callback = cb;
        this.observe = vi.fn();
        this.disconnect = vi.fn();
        this.unobserve = vi.fn();
      }),
    );

    const { container } = render(
      <TopBar
        classNames={topBarBemClasses("cm")}
        navClassNames={underlineNavBemClasses("cm")}
        activeId="home"
        collapsible
        collapseMode="hamburger"
        collapseTrigger="overflow"
        menuLabel="Menu de navegação"
        items={[
          { id: "home", label: "Início", onSelect: vi.fn() },
          { id: "rooms", label: "Sala de interação", onSelect: vi.fn() },
        ]}
        secondary={<span>Favoritos</span>}
        actions={<span>Usuário</span>}
      />,
    );

    const root = container.firstElementChild as HTMLElement;
    const measure = container.querySelector(".delpi-ui-topbar__measure") as HTMLElement;
    expect(measure).toBeTruthy();

    Object.defineProperty(root, "clientWidth", { value: 400, configurable: true });
    Object.defineProperty(measure, "scrollWidth", { value: 640, configurable: true });
    await act(async () => {
      callback?.([], {} as ResizeObserver);
    });

    expect(root.className).toContain("delpi-ui-topbar--collapsed");
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.getByRole("button", { name: "Menu de navegação" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Recolher navegação" })).toBeNull();
  });
});
