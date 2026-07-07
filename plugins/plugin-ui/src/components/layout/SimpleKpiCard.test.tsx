import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SimpleKpiCard, simpleKpiCardBemClasses } from "./SimpleKpiCard";

afterEach(() => {
  cleanup();
});

describe("SimpleKpiCard", () => {
  it("renderiza título, valor e ícone", () => {
    render(
      <SimpleKpiCard
        title="Despesas"
        value="R$ 1.000"
        icon={<span data-testid="icon">$</span>}
        classNames={simpleKpiCardBemClasses("fcc")}
      />,
    );

    expect(screen.getByText("Despesas")).toBeTruthy();
    expect(screen.getByText("R$ 1.000")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
  });

  it("mostra reticências quando loading", () => {
    render(
      <SimpleKpiCard
        title="Total"
        value="R$ 0"
        loading
        icon={null}
        classNames={simpleKpiCardBemClasses("cr")}
      />,
    );

    expect(screen.getByText("…")).toBeTruthy();
  });

  it("suporta body, subtitle e variant", () => {
    const classNames = simpleKpiCardBemClasses("ie", "kpi-card", {
      withBody: true,
      withSubtitle: true,
    });

    render(
      <SimpleKpiCard
        title="Aprovadas"
        value="12"
        subtitle="No período"
        icon={<span data-testid="icon">✓</span>}
        valueTag="p"
        classNames={classNames}
        className="ie-kpi-card--success"
      />,
    );

    expect(document.querySelector(".ie-kpi-card__body")).toBeTruthy();
    expect(screen.getByText("No período")).toBeTruthy();
    expect(document.querySelector(".ie-kpi-card--success")).toBeTruthy();
  });

  it("layout iconEnd posiciona ícone após o corpo", () => {
    const classNames = simpleKpiCardBemClasses("pva", "kpi-card", {
      withBody: true,
      layout: "iconEnd",
    });

    render(
      <SimpleKpiCard
        title="Pedidos"
        value="42"
        icon={<span data-testid="icon">#</span>}
        layout="iconEnd"
        classNames={classNames}
      />,
    );

    const header = document.querySelector(".pva-kpi-card__header");
    expect(header).toBeTruthy();
    expect(header?.querySelector(".pva-kpi-card__body")).toBeTruthy();
    expect(header?.querySelector(".pva-kpi-card__icon")).toBeTruthy();
  });
});
