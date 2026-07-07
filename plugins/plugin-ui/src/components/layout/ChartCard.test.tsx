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

  it("layout titleRow coloca hint abaixo da linha título+ações", () => {
    const classNames = chartCardBemClasses("cr", { headerLayout: "titleRow" });

    render(
      <ChartCard
        title="Ranking"
        hint="Top 10"
        classNames={classNames}
        headerActions={<button type="button">Expandir</button>}
      >
        <span>chart</span>
      </ChartCard>,
    );

    const headerRow = document.querySelector(`.${classNames.headerRow}`);
    expect(headerRow?.querySelector(`.${classNames.title}`)?.textContent).toBe("Ranking");
    expect(headerRow?.querySelector("button")?.textContent).toBe("Expandir");
    expect(headerRow?.querySelector(`.${classNames.hint}`)).toBeNull();

    const header = document.querySelector(`.${classNames.header}`);
    expect(header?.querySelector(`.${classNames.hint}`)?.textContent).toBe("Top 10");
  });
});
