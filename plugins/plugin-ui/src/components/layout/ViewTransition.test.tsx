import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ViewTransition, viewTransitionBemClasses } from "./ViewTransition";

describe("ViewTransition", () => {
  it("emite dual-class BEM com tone", () => {
    const cn = viewTransitionBemClasses("cm");
    expect(cn.root).toContain("cm-view-transition");
    expect(cn.root).toContain("delpi-ui-view-transition");
  });

  it("renderiza children e aplica modifier de tone", () => {
    const cn = viewTransitionBemClasses("cm");
    const { container, rerender } = render(
      <ViewTransition classNames={cn} transitionKey="home" tone="page">
        <p>Conteúdo A</p>
      </ViewTransition>,
    );
    expect(screen.getByText("Conteúdo A")).toBeTruthy();
    expect(container.firstElementChild?.className).toContain("delpi-ui-view-transition--page");

    rerender(
      <ViewTransition classNames={cn} transitionKey="orders" tone="panel">
        <p>Conteúdo B</p>
      </ViewTransition>,
    );
    expect(screen.getByText("Conteúdo B")).toBeTruthy();
    expect(container.firstElementChild?.className).toContain("delpi-ui-view-transition--panel");
  });
});
