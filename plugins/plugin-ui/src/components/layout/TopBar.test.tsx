import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { TopBar, topBarBemClasses } from "./TopBar";
import { underlineNavBemClasses } from "./UnderlineNav";

describe("TopBar", () => {
  it("emite dual-class BEM com modifiers", () => {
    const cn = topBarBemClasses("cm");
    expect(cn.root).toContain("cm-topbar");
    expect(cn.root).toContain("delpi-ui-topbar");
    expect(cn.row).toContain("delpi-ui-topbar__row");
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
});
