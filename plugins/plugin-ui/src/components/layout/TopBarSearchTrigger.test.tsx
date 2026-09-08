import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  TopBarSearchTrigger,
  createDashboardTopBarSearchTrigger,
  topBarSearchTriggerBemClasses,
} from "./TopBarSearchTrigger";

afterEach(() => {
  cleanup();
});

describe("TopBarSearchTrigger", () => {
  it("chama onOpen ao clicar", () => {
    const onOpen = vi.fn();
    render(
      <TopBarSearchTrigger
        classNames={topBarSearchTriggerBemClasses("cm")}
        onOpen={onOpen}
        label="Buscar"
        shortcutLabel="Ctrl+K"
        aria-label="Abrir busca"
        title="Buscar (Ctrl+K)"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Abrir busca" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("emite dual-class root/label/kbd e encaminha ref", () => {
    const ref = createRef<HTMLButtonElement>();
    const { container } = render(
      <TopBarSearchTrigger
        ref={ref}
        classNames={topBarSearchTriggerBemClasses("cm")}
        onOpen={() => undefined}
        label="Buscar"
        shortcutLabel="Ctrl+K"
        aria-label="Abrir busca"
        expanded
      />,
    );
    expect(container.querySelector(".delpi-ui-topbar-search")).toBeTruthy();
    expect(container.querySelector(".cm-topbar-search")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-search__label")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-collapse-label")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-search__kbd")).toBeTruthy();
    expect(screen.getByText("Ctrl+K").tagName).toBe("KBD");
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    expect(ref.current?.getAttribute("aria-expanded")).toBe("true");
  });

  it("factory createDashboardTopBarSearchTrigger injeta classNames", () => {
    const Trigger = createDashboardTopBarSearchTrigger({ prefix: "sp" });
    const onOpen = vi.fn();
    const { container } = render(
      <Trigger
        onOpen={onOpen}
        label="Buscar"
        shortcutLabel="Ctrl+K"
        aria-label="Abrir busca"
      />,
    );
    expect(container.querySelector(".sp-topbar-search")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir busca" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});
