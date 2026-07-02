import { describe, expect, it } from "vitest";

import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getDefaultLast12MonthsRange,
} from "./dateRange";

describe("getDefaultLast12MonthsRange", () => {
  it("calcula os últimos 12 meses com fim na data atual", () => {
    const range = getDefaultLast12MonthsRange(new Date(2026, 5, 30));

    expect(range).toEqual({
      startDate: "2025-07-01",
      endDate: "2026-06-30",
    });
  });

  it("usa o primeiro dia do mês ao voltar 11 meses", () => {
    const range = getDefaultLast12MonthsRange(new Date(2026, 0, 15));

    expect(range).toEqual({
      startDate: "2025-02-01",
      endDate: "2026-01-15",
    });
  });
});

describe("filtersFromFormState", () => {
  it("monta supplier_code e supplier_store a partir da chave composta", () => {
    const filters = filtersFromFormState({
      startDate: "2025-07-01",
      endDate: "2026-06-30",
      branch: "01",
      costCenter: "0101",
      supplierKey: "003287|01",
    });

    expect(filters).toEqual({
      startDate: "2025-07-01",
      endDate: "2026-06-30",
      branch: "01",
      costCenter: "0101",
      supplierCode: "003287",
      supplierStore: "01",
    });
  });

  it("omite filtros vazios", () => {
    const filters = filtersFromFormState(createDefaultFilterFormState(new Date(2026, 5, 30)));

    expect(filters.branch).toBeUndefined();
    expect(filters.costCenter).toBeUndefined();
    expect(filters.supplierCode).toBeUndefined();
    expect(filters.supplierStore).toBeUndefined();
  });
});
