import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  costCenterPageDashboardKey,
  costCenterPageEntriesKey,
} from "./costCenterPageKeys.ts";

const base = {
  branch: "01",
  startDate: "2026-01-01",
  endDate: "2026-08-31",
  costCenter: null,
  supplierCode: null,
  supplierStore: null,
  excludeMp: true,
  search: null,
  page: 1,
  sortBy: "data_emissao",
  sortDir: "desc",
};

describe("costCenterPageKeys", () => {
  it("dashboard key ignora página, ordenação e busca da tabela", () => {
    const a = costCenterPageDashboardKey(base);
    const b = costCenterPageDashboardKey({
      ...base,
      page: 4,
      sortBy: "valor_total",
      sortDir: "asc",
      search: "frete",
    });

    assert.equal(a, b);
    assert.equal(a, "01|2026-01-01|2026-08-31||||true");
  });

  it("entries key muda com página, ordenação e busca", () => {
    const page1 = costCenterPageEntriesKey(base);
    assert.notEqual(page1, costCenterPageEntriesKey({ ...base, page: 2 }));
    assert.notEqual(page1, costCenterPageEntriesKey({ ...base, sortBy: "valor_total" }));
    assert.notEqual(page1, costCenterPageEntriesKey({ ...base, search: "nf" }));
  });

  it("dashboard e entries mudam juntos quando o escopo do período muda", () => {
    assert.notEqual(
      costCenterPageDashboardKey(base),
      costCenterPageDashboardKey({ ...base, excludeMp: false }),
    );
    assert.notEqual(
      costCenterPageEntriesKey(base),
      costCenterPageEntriesKey({ ...base, excludeMp: false }),
    );
  });
});
