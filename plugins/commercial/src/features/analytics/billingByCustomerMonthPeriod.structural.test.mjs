#!/usr/bin/env node
/**
 * Período canônico = Ano/Mês. AnalyticsFilters não deve expor range/preset
 * (evita UI dupla e sync que “trava” a troca de período).
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));

describe("BillingByCustomerMonth period ownership", () => {
  it("esconde controles de período do AnalyticsFilters", async () => {
    const page = await readFile(
      path.join(dir, "BillingByCustomerMonthPage.tsx"),
      "utf8",
    );
    assert.match(page, /showPeriodControls=\{false\}/);
    assert.equal(
      /onPeriodPreset=\{filters\.setPeriodPreset\}/.test(page),
      false,
      "não deve ligar preset de período nesta página",
    );
    assert.equal(
      /replaceDateFilters/.test(page),
      false,
      "não deve espelhar ano/mês de volta nos filtros de data",
    );
  });

  it("AnalyticsFilters respeita showPeriodControls", async () => {
    const source = await readFile(
      path.join(dir, "components/AnalyticsFilters.tsx"),
      "utf8",
    );
    assert.match(source, /showPeriodControls\s*=\s*true/);
    assert.match(source, /showPeriodControls && onPeriodPreset/);
    assert.match(source, /\{showPeriodControls \? \(/);
  });
});
