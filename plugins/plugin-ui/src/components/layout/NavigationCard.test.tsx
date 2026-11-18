import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NavigationCard, navigationCardBemClasses } from "./NavigationCard";

afterEach(() => {
  cleanup();
});

describe("NavigationCard", () => {
  it("renderiza título/meta e dispara onClick", () => {
    const onClick = vi.fn();
    const { container } = render(
      <NavigationCard
        classNames={navigationCardBemClasses("cipa")}
        title="Santa Catarina"
        meta="Filial 01"
        onClick={onClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Santa Catarina" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-nav-card")).toBeTruthy();
    expect(container.querySelector(".cipa-nav-card__meta")?.textContent).toBe("Filial 01");
    expect(container.querySelector("[data-density='default']")).toBeTruthy();
  });

  it("aplica density featured (classes dual + data-density)", () => {
    const { container } = render(
      <NavigationCard
        classNames={navigationCardBemClasses("cm")}
        title="Minhas tarefas"
        density="featured"
        onClick={() => undefined}
      />,
    );

    const button = container.querySelector("button");
    expect(button?.getAttribute("data-density")).toBe("featured");
    expect(button?.className).toContain("delpi-ui-nav-card--featured");
    expect(button?.className).toContain("cm-nav-card--featured");
    expect(button?.className).not.toContain("--horizontal");
  });

  it("expõe seleção acessível sem alterar a API dos consumidores antigos", () => {
    const { rerender } = render(<NavigationCard classNames={navigationCardBemClasses("t")} title="Origem oficial" density="featured" selected onClick={() => undefined} />);
    expect(screen.getByRole("button", { name: "Origem oficial" }).getAttribute("aria-pressed")).toBe("true");
    rerender(<NavigationCard classNames={navigationCardBemClasses("t")} title="Origem oficial" density="featured" selected={false} onClick={() => undefined} />);
    expect(screen.getByRole("button", { name: "Origem oficial" }).getAttribute("aria-pressed")).toBe("false");
  });

  it("combina featured com orientation horizontal", () => {
    const { container } = render(
      <NavigationCard
        classNames={navigationCardBemClasses("cm")}
        title="OTD"
        density="featured"
        orientation="horizontal"
        onClick={() => undefined}
      />,
    );

    const button = container.querySelector("button");
    expect(button?.className).toContain("delpi-ui-nav-card--featured");
    expect(button?.className).toContain("delpi-ui-nav-card--horizontal");
  });
});
