import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatCityState,
  formatCnpj,
  formatSharePct,
  mapRolByProductRows,
} from "./portfolioBillingTableMappers.ts";

describe("portfolioBillingTableMappers", () => {
  it("mapeia split interno/externo e linha Total", () => {
    const rows = mapRolByProductRows(
      [
        {
          product_code: "90A",
          product_group: "3019",
          product_name: "Trafo",
          domestic_rol: 70,
          export_rol: 30,
          rol: 100,
          domestic_gross_revenue: 80,
          export_gross_revenue: 40,
          gross_revenue: 120,
          share_pct: 50,
        },
      ],
      { nature: "net", market: "all", groupBy: "product" },
    );
    assert.equal(rows.length, 2);
    assert.equal(rows[0].domestic, 70);
    assert.equal(rows[0].export, 30);
    assert.equal(rows[0].total, 100);
    assert.equal(rows[1].id, "__total__");
    assert.equal(rows[1].total, 100);
  });

  it("com mercado filtrado usa só a coluna de valor", () => {
    const rows = mapRolByProductRows(
      [
        {
          product_code: "90A",
          product_group: "3019",
          product_name: "Trafo",
          domestic_rol: 70,
          export_rol: 30,
          rol: 100,
          share_pct: 100,
        },
      ],
      { nature: "net", market: "domestic", groupBy: "product" },
    );
    assert.equal(rows[0].total, 70);
    assert.equal(rows[0].export, 0);
  });

  it("formata CNPJ, praça e participação", () => {
    assert.equal(formatCnpj("00000000000191"), "00.000.000/0001-91");
    assert.equal(formatCityState("Joinville", "SC"), "Joinville/SC");
    assert.equal(formatSharePct(12.34), "12,3 %");
  });
});
