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

  it("barra: só permite 1 série — marcar outra substitui a atual", () => {
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

    expect(screen.getByText(/uma série de valor/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("checkbox", { name: /Incluir Valor · Filial/i }));
    expect(onChange).toHaveBeenCalled();
    const next = onChange.mock.calls.at(-1)?.[0];
    expect(next.series).toHaveLength(1);
    expect(next.series[0].field).toBe("filial");
  });
});
