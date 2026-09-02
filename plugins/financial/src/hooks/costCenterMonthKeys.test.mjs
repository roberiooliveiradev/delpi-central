import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  costCenterMonthDashboardKey,
  costCenterMonthEntriesKey,
} from "./costCenterMonthKeys.ts";

const base = {
  branch: "01",
  month: "2026-08",
  costCenter: null,
  supplierCode: null,
  supplierStore: null,
  excludeMp: true,
  search: null,
  page: 1,
  sortBy: "data_emissao",
  sortDir: "desc",
};

describe("costCenterMonthKeys", () => {
  it("dashboard key ignora página, ordenação e busca da tabela", () => {
    const a = costCenterMonthDashboardKey(base);
    const b = costCenterMonthDashboardKey({
      ...base,
      page: 4,
      sortBy: "valor_total",
      sortDir: "asc",
      search: "frete",
    });

    assert.equal(a, b);
    assert.equal(a, "01|2026-08||||true");
  });

  it("entries key muda com página, ordenação e busca", () => {
    const page1 = costCenterMonthEntriesKey(base);
    assert.notEqual(page1, costCenterMonthEntriesKey({ ...base, page: 2 }));
    assert.notEqual(page1, costCenterMonthEntriesKey({ ...base, sortBy: "valor_total" }));
    assert.notEqual(page1, costCenterMonthEntriesKey({ ...base, search: "nf" }));
  });

  it("dashboard e entries mudam juntos quando o escopo do mês muda", () => {
    assert.notEqual(
      costCenterMonthDashboardKey(base),
      costCenterMonthDashboardKey({ ...base, excludeMp: false }),
    );
    assert.notEqual(
      costCenterMonthEntriesKey(base),
      costCenterMonthEntriesKey({ ...base, excludeMp: false }),
    );
  });
});
