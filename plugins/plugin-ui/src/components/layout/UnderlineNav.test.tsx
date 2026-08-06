import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { UnderlineNav, underlineNavBemClasses } from "./UnderlineNav";

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
});
