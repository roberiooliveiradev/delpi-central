import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useChartGranularitySelection } from "./useChartGranularitySelection";
import { suggestChartGranularity } from "../utils/suggestChartGranularity";

describe("suggestChartGranularity", () => {
  it("sugere day para períodos de até 1 mês", () => {
    expect(suggestChartGranularity("2026-07-01", "2026-07-10")).toBe("day");
    expect(suggestChartGranularity("2026-07-01", "2026-07-31")).toBe("day");
  });

  it("sugere month para períodos maiores que 1 mês", () => {
    expect(suggestChartGranularity("2026-07-01", "2026-08-01")).toBe("month");
    expect(suggestChartGranularity("2026-01-01", "2026-03-31")).toBe("month");
  });

  it("sugere month como padrão sem datas", () => {
    expect(suggestChartGranularity()).toBe("month");
  });
});

describe("useChartGranularitySelection", () => {
  it("inicia com granularidade derivada do período", () => {
    const { result } = renderHook(() =>
      useChartGranularitySelection("2026-07-01", "2026-07-10"),
    );

    expect(result.current.granularity).toBe("day");
  });

  it("preserva override manual até mudar as datas", () => {
    const { result, rerender } = renderHook(
      ({ start, end }: { start: string; end: string }) =>
        useChartGranularitySelection(start, end),
      { initialProps: { start: "2026-07-01", end: "2026-07-10" } },
    );

    act(() => {
      result.current.setGranularity("month");
    });

    expect(result.current.granularity).toBe("month");

    rerender({ start: "2026-07-01", end: "2026-07-10" });
    expect(result.current.granularity).toBe("month");

    rerender({ start: "2026-01-01", end: "2026-03-31" });
    expect(result.current.granularity).toBe("month");
  });

  it("aplica resolveAutoGranularity na sugestão automática", () => {
    const { result } = renderHook(() =>
      useChartGranularitySelection("2026-07-01", "2026-07-10", {
        resolveAutoGranularity: (suggested) =>
          suggested === "year" ? "year" : "month",
      }),
    );

    expect(result.current.granularity).toBe("month");
  });
});
