import { useMemo } from "react";
import { cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as safetyStockApi from "../api/safetyStockApi";
import { DEFAULT_QUERY_PARAMS, type SafetyStockItemsData } from "../types/safetyStock";
import { useSafetyStockItems } from "./useSafetyStockItems";

const params = {
  ...DEFAULT_QUERY_PARAMS,
  branch: "01",
};

const baseItem = {
  product_code: "X",
  product_description: "X",
  product_type: "MP" as const,
  unit: "PC",
  product_group: "G",
  branch: "01",
  blocked: false,
  safety_stock: 1,
  primary_stock: 1,
  work_in_process_stock: 0,
  warehouse_50_stock: 0,
  warehouse_98_stock: 0,
  warehouse_99_stock: 0,
  work_in_process_committed: 0,
  work_in_process_available: 0,
  deficit_quantity: 0,
  status: "at_safety_stock" as const,
};

const emptyPayload: SafetyStockItemsData = {
  items: [],
  page: 1,
  page_size: 50,
  total: 0,
  total_pages: 0,
  sort_by: "product_code",
  sort_direction: "asc",
};

function useItemsForSearch(search: string) {
  const appliedParams = useMemo(() => ({ ...params, search }), [search]);
  return useSafetyStockItems(appliedParams, 1, 50);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("useSafetyStockItems", () => {
  it("ignora resposta antiga quando filtros mudam rapidamente", async () => {
    let resolveFirst: ((value: SafetyStockItemsData) => void) | undefined;
    let resolveSecond: ((value: SafetyStockItemsData) => void) | undefined;

    vi.spyOn(safetyStockApi, "fetchSafetyStockItems")
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveSecond = resolve;
          }),
      );

    const { result, rerender } = renderHook(({ search }) => useItemsForSearch(search), {
      initialProps: { search: "a" },
    });

    rerender({ search: "b" });

    resolveSecond?.({
      ...emptyPayload,
      items: [{ ...baseItem, product_code: "NOVO" }],
      total: 1,
    });

    await waitFor(() => {
      expect(result.current.data?.items[0]?.product_code).toBe("NOVO");
    });

    resolveFirst?.({
      ...emptyPayload,
      items: [{ ...baseItem, product_code: "ANTIGO" }],
      total: 1,
    });

    await new Promise((resolve) => window.setTimeout(resolve, 30));
    expect(result.current.data?.items[0]?.product_code).toBe("NOVO");
  });

  it("não atualiza estado após desmontagem", async () => {
    let resolveItems: ((value: SafetyStockItemsData) => void) | undefined;
    vi.spyOn(safetyStockApi, "fetchSafetyStockItems").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveItems = resolve;
        }),
    );

    const { result, unmount } = renderHook(() => useItemsForSearch(""));
    unmount();

    resolveItems?.({
      ...emptyPayload,
      items: [{ ...baseItem, product_code: "TARDIO" }],
      total: 1,
    });

    await new Promise((resolve) => window.setTimeout(resolve, 30));
    expect(result.current.data).toBeNull();
  });
});
