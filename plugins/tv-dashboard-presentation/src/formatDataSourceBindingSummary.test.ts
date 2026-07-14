import { describe, expect, it } from "vitest";

import {
  createDataSourceBlock,
  isDataSourceInheritedChromeColor,
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import type { ComunicadoDataSourceBlock } from "./comunicadoTypes";
import {
  formatDataSourceBindingSummary,
  formatDataSourceFilterLines,
} from "./formatDataSourceBindingSummary";

describe("formatDataSourceFilterLines", () => {
  it("mostra período relativo e omite datas cruas", () => {
    const lines = formatDataSourceFilterLines(
      {
        params: {
          dateRangePreset: "this_month",
          date_start: "2026-07-01",
          date_end: "2026-07-14",
          branch: "01",
        },
      },
      { labelForKey: (key) => (key === "branch" ? "Filial" : key) },
    );
    expect(lines.some((line) => line.startsWith("Período:"))).toBe(true);
    expect(lines.some((line) => line.includes("Este mês"))).toBe(true);
    expect(lines.some((line) => line.includes("2026-07"))).toBe(false);
    expect(lines).toContain("Filial: 01");
  });

  it("marca filtros herdados do slide", () => {
    const lines = formatDataSourceFilterLines(
      { params: { work_center: "CT01" } },
      {
        slideFilters: { branch: "02", work_center: "" },
        labelForKey: (key) => (key === "branch" ? "Filial" : key),
      },
    );
    expect(lines.some((line) => line.includes("Filial: 02 (slide)"))).toBe(true);
    expect(lines.some((line) => line.includes("CT01") && !line.includes("(slide)"))).toBe(true);
  });
});

describe("formatDataSourceBindingSummary", () => {
  it("monta label, operationId e filtros para distinguir fontes", () => {
    const block = createDataSourceBlock("getProductionConsumo", {
      label: "Consumo por centro",
      defaultParams: { dateRangePreset: "last_7_days", branch: "01" },
    }) as ComunicadoDataSourceBlock;
    const summary = formatDataSourceBindingSummary(block);
    expect(summary.label).toBe("Consumo por centro");
    expect(summary.operationId).toBe("getProductionConsumo");
    expect(summary.filterLines.length).toBeGreaterThanOrEqual(2);
    expect(summary.title).toContain("Consumo por centro");
    expect(summary.title).toContain("getProductionConsumo");
  });

  it("novas fontes não gravam cor automática (chrome usa accent no CSS)", () => {
    const block = createDataSourceBlock("op") as ComunicadoDataSourceBlock;
    expect(block.style?.color).toBeUndefined();
  });
});

describe("sanitize / parse data_source color", () => {
  it("remove TEXT_STRONG legado no roundtrip (causa do texto ilegível ao voltar)", () => {
    expect(isDataSourceInheritedChromeColor("#0f172a")).toBe(true);
    expect(isDataSourceInheritedChromeColor("#089bdb")).toBe(false);

    const parsed = parseComunicadoConfig({
      version: 3,
      blocks: [
        {
          id: "ds1",
          type: "data_source",
          frame: { x: 8, y: 30, w: 18, h: 18 },
          style: { zIndex: 2, color: "#0f172a" },
          dataBinding: { operationId: "op", params: {}, displayMode: "auto" },
        },
      ],
    });
    const block = parsed.blocks?.[0] as ComunicadoDataSourceBlock;
    expect(block.style?.color).toBeUndefined();

    const saved = serializeComunicadoConfig(parsed);
    const savedBlock = (saved.blocks as Array<Record<string, unknown>>)[0];
    const savedStyle = savedBlock?.style as Record<string, unknown>;
    expect(savedStyle?.color).toBeUndefined();
  });
});
