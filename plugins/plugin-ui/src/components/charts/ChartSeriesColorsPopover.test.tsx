import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartSeriesColorsPopover } from "./ChartSeriesColorsPopover";

afterEach(() => cleanup());

const SERIES = [
  {
    dataKey: "faturamento",
    name: "Faturamento · Bruto",
    fill: "#089bdb",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "quantidade",
    name: "Quantidade fornecida",
    fill: "#ea580c",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "faturamento_prior",
    name: "Ano ant.",
    fill: "#94a3b8",
    visible: true,
    trendCapable: false,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
];

describe("ChartSeriesColorsPopover", () => {
  it("lista séries e seleciona por dataKey, não pelo índice", () => {
    const onChange = vi.fn();
    render(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={SERIES}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
    const select = screen.getByLabelText("Série") as HTMLSelectElement;
    expect([...select.options].map((option) => option.value)).toEqual([
      "faturamento",
      "quantidade",
      "faturamento_prior",
    ]);
    fireEvent.change(select, { target: { value: "quantidade" } });
    expect(select.value).toBe("quantidade");
    expect(
      screen.getByRole("button", { name: "Cor da série Quantidade fornecida" }),
    ).toBeTruthy();
  });

  it("oculta, reativa e não remove a série da lista", () => {
    const onVisibleChange = vi.fn();
    const hidden = SERIES.map((entry) =>
      entry.dataKey === "quantidade" ? { ...entry, visible: false } : entry,
    );
    const { rerender } = render(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={SERIES}
        onChange={() => undefined}
        onVisibleChange={onVisibleChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "quantidade" } });
    fireEvent.click(screen.getByLabelText("Visível"));
    expect(onVisibleChange).toHaveBeenCalledWith("quantidade", false);

    rerender(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={hidden}
        onChange={() => undefined}
        onVisibleChange={onVisibleChange}
      />,
    );
    expect(screen.getByLabelText("Série")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "quantidade" } });
    fireEvent.click(screen.getByLabelText("Visível"));
    expect(onVisibleChange).toHaveBeenCalledWith("quantidade", true);
  });

  it("ativa tendência só da série selecionada", () => {
    const onTrendChange = vi.fn();
    render(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={SERIES}
        onChange={() => undefined}
        onTrendChange={onTrendChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
    fireEvent.click(screen.getByLabelText("Ativar"));
    expect(onTrendChange).toHaveBeenCalledWith("faturamento", true);
    fireEvent.change(screen.getByLabelText("Série"), {
      target: { value: "faturamento_prior" },
    });
    expect(screen.queryByLabelText("Ativar")).toBeNull();
  });

  it("altera a cor só da série selecionada, por dataKey", () => {
    const onChange = vi.fn();
    render(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={SERIES}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "quantidade" } });
    fireEvent.click(
      screen.getByRole("button", { name: "Cor da série Quantidade fornecida" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "#c00000" }));
    expect(onChange).toHaveBeenCalledWith("quantidade", "#c00000");
    expect(onChange).not.toHaveBeenCalledWith("faturamento", expect.anything());
  });

  it("reset restaura a série selecionada", () => {
    const onResetSeries = vi.fn();
    render(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={SERIES}
        onChange={() => undefined}
        onResetSeries={onResetSeries}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "quantidade" } });
    fireEvent.click(screen.getByRole("button", { name: "Restaurar padrão" }));
    expect(onResetSeries).toHaveBeenCalledWith("quantidade");
  });
});
