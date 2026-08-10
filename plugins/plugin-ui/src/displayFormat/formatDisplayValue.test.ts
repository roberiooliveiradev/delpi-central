import { describe, expect, it } from "vitest";

import { specFromPresetId } from "./catalog";
import { formatCustomPattern } from "./formatCustomPattern";
import { formatDisplayValue } from "./formatDisplayValue";
import {
  categoryLabelFormatFromSpec,
  chartValueFormatFromSpec,
  specFromCanvasNumberFormat,
  specFromCategoryLabelFormat,
  specFromChartValueFormat,
} from "./legacy";
import { parseDisplayDate } from "./parseDisplayDate";
import { bumpDisplayFormatDecimalPlaces, toggleThousandsDisplayFormat } from "./shortcuts";

describe("formatDisplayValue", () => {
  it("percentual canônico não multiplica por 100", () => {
    expect(formatDisplayValue(41.7, specFromPresetId("percent"))).toBe("41,7%");
    expect(formatDisplayValue(41.7, { category: "percent", decimalPlaces: 0 })).toBe("42%");
  });

  it("ISO date-only usa calendário UTC (não vira dia anterior no BR)", () => {
    expect(formatDisplayValue("2026-08-03", specFromPresetId("date-short"))).toBe("03/08/2026");
    const parsed = parseDisplayDate("2026-08-03");
    expect(parsed).toMatchObject({ year: 2026, month: 7, day: 3, dateOnly: true });
  });

  it("rótulo mensal PT da API não passa por Date.parse (Jan. de 26 ≠ 2001)", () => {
    expect(parseDisplayDate("Jan. de 26")).toMatchObject({
      year: 2026,
      month: 0,
      day: 1,
      dateOnly: true,
    });
    expect(parseDisplayDate("Fev. de 26")).toMatchObject({ year: 2026, month: 1, day: 1 });
    expect(formatDisplayValue("Jan. de 26", specFromPresetId("date-short"))).toBe("Jan. de 26");
    expect(formatDisplayValue("Fev. de 26", specFromPresetId("date-short"))).toBe("Fev. de 26");
  });

  it("máscara mm é mês sem HH e minuto com HH", () => {
    expect(formatCustomPattern("2026-08-03", "dd/mm/yyyy")).toBe("03/08/2026");
    expect(formatCustomPattern("2026-08-03T14:05:00", "HH:mm")).toBe("14:05");
    expect(formatCustomPattern("2026-08-03T14:05:00", "dd/mm/yyyy HH:mm")).toBe(
      "03/08/2026 14:05",
    );
  });

  it("custom número com literal R$", () => {
    expect(formatCustomPattern(30, '"R$" #.##0,00')).toMatch(/R\$\s*30,00/);
  });

  it("custom inválido cai em general via formatDisplayValue", () => {
    expect(formatDisplayValue(12, { category: "custom", pattern: "" })).toBe("12");
  });

  it("spec > enum na leitura via mapeamento legado", () => {
    const fromEnum = specFromChartValueFormat("auto");
    expect(fromEnum.category).toBe("general");
    expect(specFromCategoryLabelFormat("raw").category).toBe("text");
    expect(specFromCategoryLabelFormat("day").presetId).toBe("date-short");
  });

  it("número sem casas explícitas não preenche zeros à direita", () => {
    expect(formatDisplayValue(12.5, { category: "number" })).toBe("12,5");
    expect(formatDisplayValue(12.5, specFromChartValueFormat("number"))).toBe("12,5");
    expect(formatDisplayValue(12.5, specFromCanvasNumberFormat("decimal"))).toBe("12,5");
    expect(formatDisplayValue(12.5, specFromCanvasNumberFormat("integer"))).toBe("13");
    expect(formatDisplayValue(12.5, specFromPresetId("number-2"))).toBe("12,50");
  });

  it("atalho de casas atualiza o valor sem precisar do separador de milhar", () => {
    const base = specFromPresetId("number-2");
    expect(formatDisplayValue(16, base)).toBe("16,00");

    const fewer = bumpDisplayFormatDecimalPlaces(base, -1);
    expect(fewer.decimalPlaces).toBe(1);
    expect(fewer.presetId).toBe("number-2");
    expect(formatDisplayValue(16, fewer)).toBe("16,0");

    const none = bumpDisplayFormatDecimalPlaces(fewer, -1);
    expect(formatDisplayValue(16, none)).toBe("16");

    const more = bumpDisplayFormatDecimalPlaces(base, 1);
    expect(formatDisplayValue(16, more)).toBe("16,000");

    /* milhar só muda grouping; casas já aplicadas pelo bump continuam válidas */
    const withThousands = toggleThousandsDisplayFormat(more);
    expect(formatDisplayValue(16000, withThousands)).toBe("16.000,000");
  });

  it("gravação só espelha spec → enum", () => {
    expect(chartValueFormatFromSpec({ category: "percent", decimalPlaces: 1 })).toEqual({
      valueFormat: "percent",
      decimalPlaces: 1,
    });
    expect(categoryLabelFormatFromSpec({ category: "date", presetId: "date-short" })).toBe("day");
    expect(categoryLabelFormatFromSpec({ category: "text", presetId: "text" })).toBe("raw");
  });
});
