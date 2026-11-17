import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { mergeComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import { ChartColorsStylesMenu } from "./ChartColorsStylesMenu";

describe("GLPI #1610 · opção visível em Alterar cores", () => {
  it("apresenta preset de sinal em colunas e aplica modo by_sign", () => {
    const onApplyOptions = vi.fn();
    const options = mergeComunicadoChartOptions({ seriesColor: "#123456" });
    render(
      <ChartColorsStylesMenu
        chartKind="bar"
        options={options}
        onApplyOptions={onApplyOptions}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Negativo / positivo" }));
    expect(onApplyOptions).toHaveBeenCalledWith(
      expect.objectContaining({
        seriesColor: "#123456",
        colorScale: expect.objectContaining({ mode: "by_sign" }),
      }),
    );
  });

  it("apresenta também em barras horizontais, não em linha ou velocímetro", () => {
    const options = mergeComunicadoChartOptions({});
    const onApplyOptions = vi.fn();
    const { rerender } = render(
      <ChartColorsStylesMenu
        chartKind="horizontal_bar"
        options={options}
        onApplyOptions={onApplyOptions}
      />,
    );
    expect(screen.getByRole("button", { name: "Negativo / positivo" })).toBeTruthy();
    rerender(<ChartColorsStylesMenu chartKind="line" options={options} onApplyOptions={onApplyOptions} />);
    expect(screen.queryByRole("button", { name: "Negativo / positivo" })).toBeNull();
    rerender(<ChartColorsStylesMenu chartKind="gauge" options={options} onApplyOptions={onApplyOptions} />);
    expect(screen.queryByRole("button", { name: "Negativo / positivo" })).toBeNull();
  });

  it("permite desligar regra pelo checkbox sem descartar as cores anteriores", () => {
    const onApplyOptions = vi.fn();
    const options = mergeComunicadoChartOptions({
      seriesColor: "#123456",
      colorScale: {
        mode: "by_sign",
        polarity: "high_is_good",
        paletteId: "sign-negative-positive",
      },
    });
    render(
      <ChartColorsStylesMenu
        chartKind="bar"
        options={options}
        onApplyOptions={onApplyOptions}
      />,
    );
    fireEvent.click(screen.getByRole("checkbox", { name: /Colorir pelo sinal/ }));
    expect(onApplyOptions).toHaveBeenCalledWith(
      expect.objectContaining({
        seriesColor: "#123456",
        colorScale: expect.objectContaining({ mode: "off" }),
      }),
    );
  });
});
