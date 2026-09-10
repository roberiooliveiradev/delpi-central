import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SectionRouteCard, sectionRouteCardBemClasses } from "./SectionRouteCard";

afterEach(() => {
  cleanup();
});

describe("SectionRouteCard", () => {
  it("renderiza título e dispara onClick da rota", () => {
    const onClick = vi.fn();
    const { container } = render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Documentos"
        routes={[{ id: "proposals", label: "Propostas comerciais", onClick }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Propostas comerciais" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-section-route-card")).toBeTruthy();
    expect(container.querySelector(".cm-section-route-card__title")?.textContent).toBe(
      "Documentos",
    );
  });

  it("mostra badge na rota e inclui na aria-label", () => {
    render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Operação"
        routes={[
          {
            id: "overdue",
            label: "Atrasadas",
            badge: 3,
            onClick: () => undefined,
          },
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: "Atrasadas, 3" })).toBeTruthy();
  });

  it("dispara onPinClick sem navegar", () => {
    const onClick = vi.fn();
    const onPinClick = vi.fn();
    render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Documentos"
        routes={[
          {
            id: "proposals",
            label: "Propostas",
            onClick,
            onPinClick,
            pinLabel: "Favoritar",
          },
        ]}
      />,
    );
    const pin = screen.getByRole("button", { name: "Favoritar" });
    expect(pin.querySelector("svg")).toBeTruthy();
    expect(pin.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(pin);
    expect(onPinClick).toHaveBeenCalledTimes(1);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("marca pin pressed com fill quando pinned", () => {
    render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Documentos"
        routes={[
          {
            id: "proposals",
            label: "Propostas",
            onClick: () => undefined,
            onPinClick: () => undefined,
            pinned: true,
            unpinLabel: "Desfavoritar",
          },
        ]}
      />,
    );
    const pin = screen.getByRole("button", { name: "Desfavoritar" });
    expect(pin.getAttribute("aria-pressed")).toBe("true");
    expect(pin.className).toMatch(/route-pin--pressed/);
    const svg = pin.querySelector("svg");
    expect(svg?.getAttribute("fill")).toBe("currentColor");
  });

  it("anexa HelpTooltip wrap ao título quando hint é informado", () => {
    const { container } = render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Operações"
        hint="Pedidos, entregas e estoques autorizados."
        routes={[{ id: "inventory", label: "Estoque", onClick: () => undefined }]}
      />,
    );
    const wrap = container.querySelector(".delpi-ui-help-tooltip--wrap");
    expect(wrap).toBeTruthy();
    expect(wrap?.textContent).toContain("Operações");
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    fireEvent.mouseEnter(wrap!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Pedidos, entregas e estoques autorizados.",
    );
  });

  it("sem hint o título permanece texto normal", () => {
    const { container } = render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Análises"
        routes={[{ id: "otd", label: "OTD", onClick: () => undefined }]}
      />,
    );
    expect(container.querySelector(".delpi-ui-help-tooltip--wrap")).toBeNull();
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    expect(screen.getByText("Análises")).toBeTruthy();
  });

  it("mostra pin em rota kind create quando onPinClick existe", () => {
    const onPinClick = vi.fn();
    render(
      <SectionRouteCard
        classNames={sectionRouteCardBemClasses("cm")}
        title="Operação"
        routes={[
          {
            id: "create_task",
            label: "Nova tarefa",
            kind: "create",
            onClick: () => undefined,
            onPinClick,
            pinLabel: "Favoritar",
          },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Favoritar" }));
    expect(onPinClick).toHaveBeenCalledTimes(1);
  });
});
