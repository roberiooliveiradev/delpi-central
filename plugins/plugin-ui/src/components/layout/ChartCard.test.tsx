import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChartCard, chartCardBemClasses } from "./ChartCard";

describe("ChartCard", () => {
  const classNames = chartCardBemClasses("dp", { withHeading: false, withActions: false });

  it("renderiza título e conteúdo", () => {
    render(
      <ChartCard title="Série temporal" classNames={classNames}>
        <div>Gráfico</div>
      </ChartCard>,
    );
    expect(screen.getByRole("region", { name: "Série temporal" })).toBeTruthy();
    expect(screen.getByText("Gráfico")).toBeTruthy();
  });

  it("exibe hint e titleHint quando informados", () => {
    render(
      <ChartCard
        title="OEE"
        titleHint="Eficiência global."
        hint="Últimos 30 dias."
        classNames={chartCardBemClasses("ds")}
      >
        <span>chart</span>
      </ChartCard>,
    );
    expect(screen.getByText("Últimos 30 dias.")).toBeTruthy();
    expect(screen.getByLabelText("Ajuda: OEE")).toBeTruthy();
  });

  it("renderiza ações no header quando classNames.actions existe", () => {
    render(
      <ChartCard
        title="Painel"
        classNames={chartCardBemClasses("dc")}
        headerActions={<button type="button">Exportar</button>}
      >
        <span>body</span>
      </ChartCard>,
    );
    expect(screen.getByRole("button", { name: "Exportar" })).toBeTruthy();
  });
});
