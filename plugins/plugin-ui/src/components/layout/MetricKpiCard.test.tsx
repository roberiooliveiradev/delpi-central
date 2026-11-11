import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { MetricKpiCard, metricKpiCardBemClasses } from "./MetricKpiCard";

afterEach(() => {
  cleanup();
});

describe("MetricKpiCard", () => {
  it("emite dual-class delpi-ui e body separado", () => {
    const classNames = metricKpiCardBemClasses("pac");
    render(
      <MetricKpiCard
        label="Planos abertos"
        value="12"
        icon={<span data-testid="icon">!</span>}
        classNames={classNames}
        tone="warning"
      />,
    );

    const article = document.querySelector("article");
    expect(article?.className).toContain("delpi-ui-card");
    expect(article?.className).toContain("delpi-ui-kpi-card");
    expect(article?.className).toContain("delpi-ui-kpi-card--warning");
    expect(document.querySelector(".delpi-ui-kpi-header")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-card__body")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-icon")).toBeTruthy();
    expect(screen.getByText("Planos abertos")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
  });

  it("titleHint usa wrap no label sem botão ?", () => {
    const classNames = metricKpiCardBemClasses("cm");
    const { container } = render(
      <MetricKpiCard
        label="Atrasado"
        titleHint="Valor em aberto por horizonte."
        value="R$ 1,00"
        classNames={classNames}
      />,
    );

    expect(screen.getByText("Atrasado")).toBeTruthy();
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Valor em aberto por horizonte.",
    );
  });

  it("status pill e chevron aparecem com onSelect; Enter aciona", () => {
    const classNames = metricKpiCardBemClasses("itp");
    let selected = 0;
    render(
      <MetricKpiCard
        label="Ações atrasadas"
        value="0"
        status={{ label: "Dentro do prazo", tone: "positive", trend: "up" }}
        onSelect={() => {
          selected += 1;
        }}
        aria-label="Ver planos de ação"
        classNames={classNames}
      />,
    );
    expect(screen.getByText("Dentro do prazo")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-status--positive")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-card__chevron")).toBeTruthy();
    const card = screen.getByRole("button", { name: "Ver planos de ação" });
    fireEvent.keyDown(card, { key: "Enter" });
    expect(selected).toBe(1);
    fireEvent.click(card);
    expect(selected).toBe(2);
  });

  it("sem onSelect o card continua inerte e sem chevron", () => {
    const classNames = metricKpiCardBemClasses("itp");
    render(
      <MetricKpiCard
        label="Servidores ativos"
        value="3"
        status={{ label: "Operacionais", tone: "neutral" }}
        classNames={classNames}
      />,
    );
    expect(screen.queryByRole("button")).toBeNull();
    expect(document.querySelector(".delpi-ui-kpi-card__chevron")).toBeNull();
    expect(screen.getByText("Operacionais")).toBeTruthy();
  });

  it("sem titleHint não monta HelpTooltip", () => {
    const classNames = metricKpiCardBemClasses("cm");
    const { container } = render(
      <MetricKpiCard label="Este mês" value="R$ 0,00" classNames={classNames} />,
    );
    expect(container.querySelector(".delpi-ui-help-tooltip")).toBeNull();
    expect(screen.getByText("Este mês")).toBeTruthy();
  });
});
