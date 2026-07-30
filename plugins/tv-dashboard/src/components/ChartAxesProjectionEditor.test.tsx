import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartAxesProjectionEditor } from "./ChartAxesProjectionEditor";

afterEach(() => cleanup());

describe("ChartAxesProjectionEditor", () => {
  it("não cola o texto «Selecionar» ao rótulo (padrão colunas da tabela)", () => {
    const onSeriesActivate = vi.fn();
    const onChange = vi.fn();

    render(
      <ChartAxesProjectionEditor
        idPrefix="test"
        chartType="stacked_bar"
        options={[
          { field: "materialCodigo", label: "Material código" },
          { field: "quantidade", label: "Quantidade" },
          { field: "filial", label: "Filial" },
          { field: "branch", label: "Filial" },
        ]}
        chartProjection={{
          categoryField: "materialCodigo",
          series: [
            { field: "quantidade", label: "Quantidade", aggregation: "sum" },
            { field: "filial", label: "Filial", aggregation: "sum" },
            { field: "branch", label: "Filial", aggregation: "sum" },
          ],
        }}
        onChange={onChange}
        onSeriesActivate={onSeriesActivate}
      />,
    );

    expect(screen.queryByRole("button", { name: "Selecionar" })).toBeNull();
    expect(screen.queryByText(/^Selecionar$/)).toBeNull();

    const labelBtn = screen.getByRole("button", { name: "Séries (Y) · Quantidade" });
    expect(labelBtn.textContent).toBe("Séries (Y) · Quantidade");
    expect(labelBtn.textContent).not.toMatch(/Selecionar/);

    fireEvent.click(labelBtn);
    expect(onSeriesActivate).toHaveBeenCalledWith("quantidade", 0);
  });

  it("colunas: aceita múltiplas séries (até 6)", () => {
    const onChange = vi.fn();

    render(
      <ChartAxesProjectionEditor
        idPrefix="bar"
        chartType="bar"
        options={[
          { field: "materialCodigo", label: "Material código" },
          { field: "quantidade", label: "Quantidade" },
          { field: "filial", label: "Filial" },
        ]}
        chartProjection={{
          categoryField: "materialCodigo",
          series: [{ field: "quantidade", label: "Quantidade", aggregation: "sum" }],
        }}
        onChange={onChange}
      />,
    );

    expect(screen.getByText(/Até 6 séries/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("checkbox", { name: /Incluir Séries \(Y\) · Filial/i }));
    expect(onChange).toHaveBeenCalled();
    const next = onChange.mock.calls.at(-1)?.[0];
    expect(next.series).toHaveLength(2);
    expect(next.series.map((s: { field: string }) => s.field)).toEqual([
      "quantidade",
      "filial",
    ]);
  });

  it("rosca: ao trocar série numérica usa Soma (não Contagem de linhas)", () => {
    const onChange = vi.fn();

    render(
      <ChartAxesProjectionEditor
        idPrefix="donut"
        chartType="doughnut"
        options={[
          { field: "codigo", label: "Código", fieldType: "string" },
          { field: "value", label: "Valor", fieldType: "number" },
          { field: "quantidade", label: "Quantidade", fieldType: "number" },
        ]}
        chartProjection={{
          categoryField: "codigo",
          series: [{ field: "value", label: "Valor", aggregation: "sum" }],
        }}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("checkbox", { name: /Incluir Valor · Quantidade/i }));
    const next = onChange.mock.calls.at(-1)?.[0];
    expect(next.series).toHaveLength(1);
    expect(next.series[0]).toMatchObject({
      field: "quantidade",
      aggregation: "sum",
    });
  });
});
