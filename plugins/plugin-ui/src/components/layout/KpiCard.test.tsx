import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { KpiCard, kpiCardBemClasses } from "./KpiCard";

const LABELS = {
  goalPrefix: "Goal",
  iddScorePrefix: "IDD",
  badgesStatus: "Goal performance",
};

afterEach(() => {
  cleanup();
});

describe("KpiCard", () => {
  it("renderiza título, valor e ícone", () => {
    render(
      <KpiCard
        title="OEE"
        value="82%"
        icon={<span data-testid="icon" />}
        classNames={kpiCardBemClasses("dp")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("OEE")).toBeTruthy();
    expect(screen.getByText("82%")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
  });

  it("exibe meta e badges quando informados", () => {
    render(
      <KpiCard
        title="OTD"
        value="95%"
        goalLabel="90%"
        goalScopeBadge={{ label: "Consolidated" }}
        goalPerformanceBadge={{
          tone: "success",
          statusLabel: "On track",
          directionLabel: "Higher is better",
        }}
        icon={<span />}
        classNames={kpiCardBemClasses("ds")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("Goal")).toBeTruthy();
    expect(screen.getByText("90%")).toBeTruthy();
    expect(screen.getByText("Consolidated")).toBeTruthy();
    expect(screen.getByText("On track")).toBeTruthy();
  });

  it("exibe segunda linha Meta mês com ajuda no próprio prefixo (wrap)", () => {
    const { container } = render(
      <KpiCard
        title="ROL"
        value="100"
        goalLabel="50"
        goalPrefix="Meta parcial"
        goalHint="Meta calculada do período"
        monthlyGoalLabel="100"
        monthlyGoalPrefix="Meta mês"
        monthlyGoalHint="Valor cadastrado"
        icon={<span />}
        classNames={kpiCardBemClasses("dc")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("Meta parcial")).toBeTruthy();
    expect(screen.getByText("Meta mês")).toBeTruthy();
    expect(container.querySelectorAll(".delpi-ui-help-tooltip--wrap").length).toBe(2);
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();

    const wraps = container.querySelectorAll(".delpi-ui-help-tooltip--wrap");
    fireEvent.mouseEnter(wraps[0]!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Meta calculada do período",
    );
    fireEvent.mouseLeave(wraps[0]!);
    fireEvent.mouseEnter(wraps[1]!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe("Valor cadastrado");
  });

  it("titleHint usa wrap no título sem botão ?", () => {
    const { container } = render(
      <KpiCard
        title="OTD compras"
        titleHint="Percentual de entregas no prazo"
        value="95%"
        icon={<span />}
        classNames={kpiCardBemClasses("ds")}
        labels={LABELS}
      />,
    );
    const wrap = container.querySelector(".delpi-ui-help-tooltip--wrap");
    expect(wrap).toBeTruthy();
    expect(wrap?.textContent).toContain("OTD compras");
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    fireEvent.mouseEnter(wrap!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Percentual de entregas no prazo",
    );
  });

  it("sem hints permanece texto normal sem tooltip wrap", () => {
    const { container } = render(
      <KpiCard
        title="OEE"
        value="82%"
        goalLabel="80%"
        icon={<span />}
        classNames={kpiCardBemClasses("dp")}
        labels={LABELS}
      />,
    );
    expect(container.querySelector(".delpi-ui-help-tooltip--wrap")).toBeNull();
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
  });

  it("mostra goalScopeHint sem Meta mês numérica (matriz D)", () => {
    render(
      <KpiCard
        title="ROL"
        value="—"
        goalLabel={null}
        monthlyGoalLabel={null}
        goalScopeHint="Metas cadastradas apenas por unidade. Selecione uma unidade no filtro."
        icon={<span />}
        classNames={kpiCardBemClasses("dc")}
        labels={LABELS}
      />,
    );
    expect(
      screen.getByText(/Selecione uma unidade/i),
    ).toBeTruthy();
    expect(screen.queryByText("Meta mês")).toBeNull();
    expect(screen.queryByText("Goal")).toBeNull();
  });

  it("aplica tom comparativo no card", () => {
    const { container } = render(
      <KpiCard
        title="ROL"
        value="R$ 10"
        goalLabel="R$ 20"
        comparisonTone="negative"
        icon={<span />}
        classNames={kpiCardBemClasses("fin")}
        labels={LABELS}
      />,
    );
    expect(container.querySelector(".delpi-ui-kpi-card--negative")).toBeTruthy();
  });

  it("dispara onClick no card interativo inclusive ao clicar no título com help wrap", () => {
    const onClick = vi.fn();
    render(
      <KpiCard
        title="ROL"
        titleHint="Receita operacional líquida"
        value="R$ 10"
        icon={<span />}
        classNames={kpiCardBemClasses("fin")}
        labels={LABELS}
        onClick={onClick}
      />,
    );
    const card = screen.getByRole("button", { name: /Abrir detalhes: ROL/i });
    expect(card.tagName).toBe("ARTICLE");
    expect(card.className).toContain("delpi-ui-kpi-card--interactive");
    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledTimes(1);

    expect(card.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    onClick.mockClear();
    fireEvent.click(screen.getByText("ROL"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("mostra placeholder quando loading", () => {
    render(
      <KpiCard
        title="OEE"
        value="82%"
        loading={true}
        icon={<span />}
        classNames={kpiCardBemClasses("dc")}
        labels={LABELS}
      />,
    );
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("…");
  });
});
