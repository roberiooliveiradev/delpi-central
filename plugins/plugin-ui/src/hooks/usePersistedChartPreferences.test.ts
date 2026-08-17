import { cleanup, renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePersistedChartPreferences } from "./usePersistedChartPreferences";

afterEach(cleanup);

describe("usePersistedChartPreferences", () => {
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("usa defaults e persiste patch", () => {
    const defaults = { chartType: "column" as const, showTrend: false };
    const { result } = renderHook(() =>
      usePersistedChartPreferences({
        storageKey: "demo:chart",
        defaults,
        allowedChartTypes: ["column", "line", "area"],
      }),
    );
    expect(result.current.preferences.chartType).toBe("column");
    expect(result.current.preferences.showTrend).toBe(false);

    act(() => {
      result.current.setChartType("line");
      result.current.setPreferences({ showTrend: true });
    });
    expect(result.current.preferences.chartType).toBe("line");
    expect(result.current.preferences.showTrend).toBe(true);
    const stored = JSON.parse(storage.get("demo:chart") ?? "{}");
    expect(stored.chartType).toBe("line");
    expect(stored.showTrend).toBe(true);
  });

  it("respeita valor já persistido", () => {
    storage.set(
      "demo:chart",
      JSON.stringify({ chartType: "area", comparePriorYear: true }),
    );
    const { result } = renderHook(() =>
      usePersistedChartPreferences({
        storageKey: "demo:chart",
        defaults: { chartType: "column", comparePriorYear: false },
        allowedChartTypes: ["column", "line", "area"],
      }),
    );
    expect(result.current.preferences.chartType).toBe("area");
    expect(result.current.preferences.comparePriorYear).toBe(true);
  });

  it("rejeita chartType fora da família permitida", () => {
    storage.set("demo:chart", JSON.stringify({ chartType: "pie" }));
    const { result } = renderHook(() =>
      usePersistedChartPreferences({
        storageKey: "demo:chart",
        defaults: { chartType: "column" },
        allowedChartTypes: ["column", "line", "area"],
      }),
    );
    expect(result.current.preferences.chartType).toBe("column");
  });

  it("limita compareYears a 0..3", () => {
    const { result } = renderHook(() =>
      usePersistedChartPreferences({
        storageKey: "demo:chart",
        defaults: { chartType: "column", compareYears: 0 },
      }),
    );
    act(() => {
      result.current.setPreferences({ compareYears: 9 });
    });
    expect(result.current.preferences.compareYears).toBe(3);
  });
});
