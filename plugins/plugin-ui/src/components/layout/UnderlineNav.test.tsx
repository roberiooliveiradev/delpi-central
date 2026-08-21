import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import { UnderlineNav, underlineNavBemClasses } from "./UnderlineNav";

afterEach(cleanup);

describe("UnderlineNav", () => {
  it("emite dual-class BEM", () => {
    const cn = underlineNavBemClasses("cm");
    expect(cn.root).toContain("cm-underline-nav");
    expect(cn.root).toContain("delpi-ui-underline-nav");
    expect(cn.item).toContain("delpi-ui-underline-nav__item");
  });

  it("marca ativo com aria-current e renderiza badge", () => {
    const onSelect = vi.fn();
    const cn = underlineNavBemClasses("cm");
    render(
      <UnderlineNav
        classNames={cn}
        activeId="my_day"
        items={[
          { id: "home", label: "Início", onSelect },
          { id: "my_day", label: "Meu dia", count: 3, onSelect },
        ]}
      />,
    );
    const myDay = screen.getByRole("button", { name: /Meu dia/ });
    expect(myDay.getAttribute("aria-current")).toBe("page");
    expect(myDay.textContent).toContain("3");

    fireEvent.click(screen.getByRole("button", { name: "Início" }));
    expect(onSelect).toHaveBeenCalled();
  });

  it("preserva semântica de navegação por padrão", () => {
    const cn = underlineNavBemClasses("cm");
    render(
      <UnderlineNav
        classNames={cn}
        activeId="home"
        items={[
          { id: "home", label: "Início" },
          { id: "reports", label: "Relatórios" },
        ]}
      />,
    );

    expect(screen.getByRole("navigation")).toBeTruthy();
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.getByRole("button", { name: "Início" }).getAttribute("aria-current")).toBe(
      "page",
    );
  });

  it("expõe layout wrap e densidade compacta via data-attrs", () => {
    const cn = underlineNavBemClasses("ppc");
    const { container } = render(
      <UnderlineNav
        mode="tabs"
        layout="wrap"
        density="compact"
        classNames={cn}
        activeId="ct-01"
        aria-label="Centros de trabalho"
        items={[
          { id: "ct-01", label: "CT-01", controlId: "panel" },
          { id: "ct-02", label: "CT-02", controlId: "panel" },
        ]}
      />,
    );

    const root = container.querySelector(".delpi-ui-underline-nav");
    expect(root?.getAttribute("data-layout")).toBe("wrap");
    expect(root?.getAttribute("data-density")).toBe("compact");
  });

  it("oferece tabs com roving tabindex e teclado", () => {
    const first = vi.fn();
    const second = vi.fn();
    const cn = underlineNavBemClasses("cm");
    render(
      <UnderlineNav
        mode="tabs"
        classNames={cn}
        activeId="overview"
        aria-label="Seções do registro"
        items={[
          {
            id: "overview",
            label: "Visão geral",
            controlId: "panel-overview",
            onSelect: first,
          },
          {
            id: "history",
            label: "Histórico",
            controlId: "panel-history",
            onSelect: second,
          },
        ]}
      />,
    );

    expect(screen.getByRole("tablist", { name: "Seções do registro" })).toBeTruthy();
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0]?.getAttribute("aria-selected")).toBe("true");
    expect(tabs[0]?.getAttribute("aria-controls")).toBe("panel-overview");
    expect(tabs[0]?.getAttribute("id")).toBe("overview-tab");
    expect(tabs[0]?.tabIndex).toBe(0);
    expect(tabs[1]?.tabIndex).toBe(-1);

    fireEvent.keyDown(tabs[0]!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(tabs[1]);
    expect(second).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(tabs[1]!, { key: "Home" });
    expect(document.activeElement).toBe(tabs[0]);
    expect(first).toHaveBeenCalledTimes(1);
  });
});
