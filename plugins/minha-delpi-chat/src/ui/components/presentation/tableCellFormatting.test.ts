import { describe, expect, it } from "vitest";

import { formatCellValue } from "./tableCellFormatting";

describe("tableCellFormatting", () => {
  it("formats billing documents as count, not currency", () => {
    expect(
      formatCellValue(15, "valor", undefined, { campo: "Documentos" }),
    ).toBe("15");
  });

  it("formats COUNT(*) AS TOTAL as quantity, not currency", () => {
    expect(formatCellValue(1898, "TOTAL")).toBe("1.898");
    expect(formatCellValue(1898, "total")).toBe("1.898");
    expect(formatCellValue(42, "count")).toBe("42");
  });

  it("keeps monetary compound totals as currency", () => {
    expect(formatCellValue(1898, "total_revenue")).toBe("R$\u00a01.898,00");
    expect(formatCellValue(1898, "valor_total")).toBe("R$\u00a01.898,00");
  });

  it("formats billing value as currency", () => {
    expect(
      formatCellValue(2519.81, "valor", undefined, {
        campo: "Valor faturado",
      }),
    ).toBe("R$\u00a02.519,81");
  });

  it("respects explicit row valorType", () => {
    expect(
      formatCellValue(15, "valor", undefined, {
        campo: "Outro",
        valorType: "quantity",
      }),
    ).toBe("15");
  });

  it("formats nested parent objects without [object Object]", () => {
    expect(
      formatCellValue(
        [
          { code: "90260148", description: "CHICOTE" },
          { code: "90260200", description: "OUTRO PA" },
        ],
        "parents",
      ),
    ).toBe("90260148 — CHICOTE, 90260200 — OUTRO PA");
  });
});
