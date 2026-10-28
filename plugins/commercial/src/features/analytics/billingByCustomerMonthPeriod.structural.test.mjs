#!/usr/bin/env node
/**
 * Período canônico = dateStart/dateEnd do AnalyticsFilters.
 * Ano/Mês são atalhos one-way (não há sync que sobrescreva o range livre).
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));

describe("BillingByCustomerMonth period ownership", () => {
  it("consulta usa dateStart/dateEnd e expõe controles de período", async () => {
    const page = await readFile(
      path.join(dir, "BillingByCustomerMonthPage.tsx"),
      "utf8",
    );
    assert.match(page, /start_date:\s*dateStart/);
    assert.match(page, /end_date:\s*dateEnd/);
    assert.match(page, /showPeriodControls/);
    assert.match(page, /onPeriodPreset=\{filters\.setPeriodPreset\}/);
    assert.match(page, /applyYearMonthShortcut/);
    assert.equal(
      /replaceDateFilters\(\{[\s\S]*filters\.dateStart === period\.start/.test(page),
      false,
      "não deve haver sync bidirecional que trave o período",
    );
  });

  it("AnalyticsFilters permite ocultar período quando necessário", async () => {
    const source = await readFile(
      path.join(dir, "components/AnalyticsFilters.tsx"),
      "utf8",
    );
    assert.match(source, /showPeriodControls\s*=\s*true/);
    assert.match(source, /showPeriodControls && onPeriodPreset/);
  });
});
