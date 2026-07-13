import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartAddElementMenu } from "./ChartAddElementMenu";

afterEach(() => {
  cleanup();
});

describe("ChartAddElementMenu", () => {
  it("abre flyout e aplica choice / Mais opções", () => {
    const onApplyChoice = vi.fn();
    const onMoreOptions = vi.fn();
    render(
      <ChartAddElementMenu
        options={{ showLegend: true, legendPosition: "bottom" }}
        chartKind="line"
        onApplyChoice={onApplyChoice}
        onMoreOptions={onMoreOptions}
      />,
    );

    fireEvent.mouseEnter(screen.getByRole("menuitem", { name: /Legenda/i }).closest("li")!);
    expect(
      screen.getByRole("menuitemcheckbox", { name: /Inferior/i }).getAttribute("aria-checked"),
    ).toBe("true");

    fireEvent.click(screen.getByRole("menuitemcheckbox", { name: /Esquerda/i }));
    expect(onApplyChoice).toHaveBeenCalledWith("legend:left");

    fireEvent.click(screen.getByRole("menuitem", { name: /Mais opções de legenda/i }));
    expect(onMoreOptions).toHaveBeenCalledWith("legend");
  });

  it("omite marcadores em gráfico de barras", () => {
    render(
      <ChartAddElementMenu
        options={{}}
        chartKind="bar"
        onApplyChoice={() => undefined}
        onMoreOptions={() => undefined}
      />,
    );
    expect(screen.queryByRole("menuitem", { name: "Marcadores" })).toBeNull();
    expect(screen.getByRole("menuitem", { name: "Eixos" })).toBeTruthy();
  });
});
