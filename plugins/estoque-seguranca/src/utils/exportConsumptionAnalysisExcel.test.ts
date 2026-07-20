import { describe, expect, it } from "vitest";

import type { ConsumptionAnalysisItem } from "../types/consumptionAnalysis";
import {
  buildConsumptionAnalysisExportPayload,
  consumptionAnalysisItemToExportRow,
} from "./exportConsumptionAnalysisExcel";

function sampleItem(
  overrides: Partial<ConsumptionAnalysisItem> = {},
): ConsumptionAnalysisItem {
  return {
    product_code: "10020113",
    product_description: "MP EXEMPLO",
    product_type: "MP",
    unit: "PC",
    product_group: "10",
    branch: "01",
    blocked: false,
    safety_stock: 80,
    suggested_safety_stock: 100,
    difference_quantity: -20,
    difference_percent: -20,
    available_stock: 50,
    primary_stock: 40,
    warehouse_98_stock: 5,
    warehouse_99_stock: 5,
    period_consumption: 1000,
    average_daily_consumption: 4,
    lead_time_days: 30,
    lead_time_business_days: 22,
    coverage_business_days: 12.5,
    movement_count: 10,
    first_movement_date: "2025-08-01",
    last_movement_date: "2026-07-01",
    analysis_status: "below_suggested",
    quality_warnings: [],
    has_inconsistent_data: false,
    period_start: "2025-07-21",
    period_end: "2026-07-20",
    period_calendar_days: 365,
    period_business_days: 261,
    ...overrides,
  };
}

describe("exportConsumptionAnalysisExcel", () => {
  it("monta linha com situação em português", () => {
    const row = consumptionAnalysisItemToExportRow(sampleItem());
    expect(row.suggested_safety_stock).toBe(100);
    expect(row.analysis_status).toContain("Abaixo");
    expect(row.blocked).toBe("Não");
  });

  it("monta payload com colunas da simulação", () => {
    const payload = buildConsumptionAnalysisExportPayload([sampleItem()]);
    expect(payload.columns.map((column) => column.key)).toContain(
      "suggested_safety_stock",
    );
    expect(payload.rows).toHaveLength(1);
  });
});
