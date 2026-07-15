import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useTableColumnVisibility } from "./useTableColumnVisibility";
import {
  createDefaultColumnVisibility,
  sanitizeColumnVisibility,
} from "../utils/tableColumnVisibilityPreferences";

const COLUMNS = [
  { key: "data", label: "Data" },
  { key: "op", label: "OP" },
  { key: "valor", label: "Valor" },
] as const;

describe("tableColumnVisibilityPreferences", () => {
  it("cria defaults todas true", () => {
    expect(createDefaultColumnVisibility(COLUMNS)).toEqual({
      data: true,
      op: true,
      valor: true,
    });
  });

  it("sanitiza ignorando chaves desconhecidas e restaura se todas ocultas", () => {
    const visibility = sanitizeColumnVisibility(
      { visibility: { data: false, op: false, valor: false, ghost: true } },
      COLUMNS,
    );
    expect(visibility.ghost).toBeUndefined();
    expect(visibility.data).toBe(true);
    expect(visibility.op).toBe(false);
    expect(visibility.valor).toBe(false);
  });

  it("usa emptyFallbackKeys quando nenhuma coluna fica visível", () => {
    const visibility = sanitizeColumnVisibility(
      { visibility: { data: false, op: false, valor: false } },
      COLUMNS,
      { emptyFallbackKeys: ["op", "valor"] },
    );
    expect(visibility.op).toBe(true);
    expect(visibility.valor).toBe(true);
    expect(visibility.data).toBe(false);
  });
});

describe("useTableColumnVisibility", () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.useRealTimers();
  });

  it("persiste toggles em localStorage", () => {
    vi.useFakeTimers();
    const storageKey = "test:table:v1";
    const { result } = renderHook(() =>
      useTableColumnVisibility({ storageKey, columns: COLUMNS }),
    );

    act(() => {
      result.current.setColumnVisible("op", false);
    });

    expect(result.current.visibleKeys).toEqual(["data", "valor"]);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    const raw = JSON.parse(window.localStorage.getItem(storageKey) ?? "{}");
    expect(raw.visibility.op).toBe(false);
  });

  it("impede ocultar a última coluna quando keepAtLeastOne", () => {
    const { result } = renderHook(() =>
      useTableColumnVisibility({
        storageKey: "test:keep:v1",
        columns: COLUMNS,
      }),
    );

    act(() => {
      result.current.setColumnVisible("data", false);
      result.current.setColumnVisible("op", false);
    });
    expect(result.current.visibleColumnCount).toBe(1);

    act(() => {
      result.current.setColumnVisible("valor", false);
    });
    expect(result.current.visibleColumnCount).toBe(1);
    expect(result.current.visibility.valor).toBe(true);
  });

  it("filterColumns remove colunas ocultas", () => {
    const { result } = renderHook(() =>
      useTableColumnVisibility({
        storageKey: "test:filter:v1",
        columns: COLUMNS,
      }),
    );

    act(() => {
      result.current.setColumnVisible("data", false);
    });

    const filtered = result.current.filterColumns([
      { key: "data", header: "Data" },
      { key: "op", header: "OP" },
      { key: "valor", header: "Valor" },
    ]);
    expect(filtered.map((c) => c.key)).toEqual(["op", "valor"]);
  });

  it("enabled=false não grava localStorage", () => {
    vi.useFakeTimers();
    const storageKey = "test:disabled:v1";
    const { result } = renderHook(() =>
      useTableColumnVisibility({
        storageKey,
        columns: COLUMNS,
        enabled: false,
      }),
    );

    act(() => {
      result.current.setColumnVisible("op", false);
      vi.advanceTimersByTime(200);
    });

    expect(window.localStorage.getItem(storageKey)).toBeNull();
  });
});
