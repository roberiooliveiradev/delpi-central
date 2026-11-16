/**
 * U15R R1 — ChartViewShell + preferência de tipo + clique de categoria.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

import { EntryAuditDailyEvolutionChart } from "./EntryAuditDailyEvolutionChart";

afterEach(() => cleanup());

const points = [
  { name: "07/11", day: "2026-11-07", current: 1, previous: 0 },
  { name: "08/11", day: "2026-11-08", current: 2, previous: 1 },
  { name: "09/11", day: "2026-11-09", current: 0, previous: 0 },
];

describe("EntryAuditDailyEvolutionChart", () => {
  it("troca o tipo de gráfico e persiste o valor no toggle", async () => {
    render(
      <EntryAuditDailyEvolutionChart
        points={points}
        includePrevious
        previousPeriodLegend="31/10–02/11"
        selectedDay=""
        onSelectDay={() => undefined}
      />,
    );
    expect(
      screen.getByTestId("multi-type-series-chart").getAttribute("data-chart-type"),
    ).toBe("column");
    fireEvent.click(screen.getByRole("button", { name: /^line$/i }));
    await waitFor(() => {
      expect(
        screen.getByTestId("chart-type-segment-toggle").getAttribute("data-value"),
      ).toBe("line");
      expect(
        screen.getByTestId("multi-type-series-chart").getAttribute("data-chart-type"),
      ).toBe("line");
    });
  });

  it("clique na categoria chama onSelectDay com ISO; reclique limpa", async () => {
    const onSelectDay = vi.fn();
    const { rerender } = render(
      <EntryAuditDailyEvolutionChart
        points={points}
        includePrevious={false}
        previousPeriodLegend={null}
        selectedDay=""
        onSelectDay={onSelectDay}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /08\/11:\s*2/i }));
    expect(onSelectDay).toHaveBeenCalledWith("2026-11-08");

    rerender(
      <EntryAuditDailyEvolutionChart
        points={points}
        includePrevious={false}
        previousPeriodLegend={null}
        selectedDay="2026-11-08"
        onSelectDay={onSelectDay}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /08\/11:\s*2/i }));
    expect(onSelectDay).toHaveBeenCalledWith("");
  });
});
