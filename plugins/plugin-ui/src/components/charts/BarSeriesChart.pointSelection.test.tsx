import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BarSeriesChart } from "./BarSeriesChart";
import type { SeriesChartPoint } from "./seriesChartOptions";

const POINTS: SeriesChartPoint[] = [
  { label: "07/11", value: 2 },
  { label: "08/11", value: 5 },
  { label: "09/11", value: 0 },
];

afterEach(() => cleanup());

describe("BarSeriesChart point selection (U14R2 K1)", () => {
  it("without onPointSelect: no role=button and structure is inert", () => {
    const { container } = render(
      <BarSeriesChart points={POINTS} emptyMessage="vazio" options={{ showLegend: false }} />,
    );
    expect(container.querySelectorAll('[role="button"]')).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
  });

  it("with onPointSelect: bars are keyboard buttons with aria-label", () => {
    const onPointSelect = vi.fn();
    render(
      <BarSeriesChart
        points={POINTS}
        onPointSelect={onPointSelect}
        options={{ showLegend: false }}
      />,
    );
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(3);
    expect(buttons[0]?.getAttribute("aria-label")).toBe("07/11: 2");
    expect(buttons[1]?.getAttribute("aria-pressed")).toBe("false");
  });

  it("click selects; second click clears with null", () => {
    const onPointSelect = vi.fn();
    const { rerender } = render(
      <BarSeriesChart
        points={POINTS}
        onPointSelect={onPointSelect}
        options={{ showLegend: false }}
      />,
    );
    fireEvent.click(screen.getAllByRole("button")[1]!);
    expect(onPointSelect).toHaveBeenLastCalledWith(
      expect.objectContaining({ label: "08/11", value: 5 }),
      1,
    );

    rerender(
      <BarSeriesChart
        points={POINTS}
        onPointSelect={onPointSelect}
        selectedPointKey="08/11"
        options={{ showLegend: false }}
      />,
    );
    const selected = screen.getAllByRole("button")[1]!;
    expect(selected.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(selected);
    expect(onPointSelect).toHaveBeenLastCalledWith(null, null);
  });

  it("Enter/Space activate the focused bar", () => {
    const onPointSelect = vi.fn();
    render(
      <BarSeriesChart
        points={POINTS}
        onPointSelect={onPointSelect}
        options={{ showLegend: false }}
      />,
    );
    const btn = screen.getAllByRole("button")[0]!;
    fireEvent.keyDown(btn, { key: "Enter" });
    expect(onPointSelect).toHaveBeenCalledWith(
      expect.objectContaining({ label: "07/11", value: 2 }),
      0,
    );
    fireEvent.keyDown(btn, { key: " " });
    expect(onPointSelect).toHaveBeenCalledTimes(2);
  });

  it("selected dims siblings", () => {
    const { container } = render(
      <BarSeriesChart
        points={POINTS}
        onPointSelect={() => undefined}
        selectedPointKey="07/11"
        options={{ showLegend: false }}
      />,
    );
    const dimmed = container.querySelectorAll(
      ".delpi-ui-series-chart__series-bar--dimmed",
    );
    expect(dimmed.length).toBeGreaterThanOrEqual(2);
    const selected = container.querySelectorAll(
      ".delpi-ui-series-chart__series-bar--selected",
    );
    expect(selected.length).toBeGreaterThanOrEqual(1);
  });
});
