/**
 * U12 W3 — catálogo de campos: todo código canônico da vocabulary da API
 * tem rótulo PT e tipo; formatadores cobrem money/percent/date/text.
 */
import { describe, expect, it } from "vitest";

import {
  ENTRY_AUDIT_FIELD_CATALOG,
  ENTRY_AUDIT_UNKNOWN_FIELD_LABEL,
  entryAuditFieldLabel,
  formatEntryAuditFieldValue,
  formatOccurrenceValue,
  resolveEntryAuditField,
} from "./entryAuditPresentation";

/** Códigos de `FIELD_CODES` em controllership-finance-api vocabulary.py. */
const API_FIELD_CODES = [
  "total",
  "goods",
  "st",
  "discount",
  "series",
  "icms",
  "base",
  "ipi",
  "simple_rate",
  "amount",
  "cfop",
  "taker",
  "rate",
  "cst",
  "key",
  "species",
  "number",
  "supplier",
  "origin",
  "freight",
  "expense",
  "insurance",
  "book_icms",
] as const;

describe("U12 W3 entry-audit field catalog", () => {
  it("cobre todos os códigos canônicos da vocabulary da API", () => {
    for (const code of API_FIELD_CODES) {
      expect(
        ENTRY_AUDIT_FIELD_CATALOG[code],
        `faltando catálogo para ${code}`,
      ).toBeDefined();
      expect(ENTRY_AUDIT_FIELD_CATALOG[code].label.trim()).not.toBe("");
      expect(ENTRY_AUDIT_FIELD_CATALOG[code].label.toLowerCase()).not.toBe(
        "field",
      );
      expect(["money", "percent", "date", "text"]).toContain(
        ENTRY_AUDIT_FIELD_CATALOG[code].kind,
      );
    }
  });

  it("resolve rótulos literais e nunca devolve o termo técnico field", () => {
    expect(entryAuditFieldLabel({ field: "total" })).toBe(
      "Valor total da nota",
    );
    expect(entryAuditFieldLabel({ field: "Vlr Total" })).toBe(
      "Valor total da nota",
    );
    expect(entryAuditFieldLabel({ field_label: "pCredSN (%)" })).toBe(
      "Alíquota de crédito do Simples",
    );
    expect(entryAuditFieldLabel({ field: "field" })).toBe(
      ENTRY_AUDIT_UNKNOWN_FIELD_LABEL,
    );
    expect(entryAuditFieldLabel({ field: "field", field_label: "field" })).toBe(
      ENTRY_AUDIT_UNKNOWN_FIELD_LABEL,
    );
  });

  it("formata Protheus/XML por tipo (R$, %, data, texto)", () => {
    expect(formatEntryAuditFieldValue("408.00", "money")).toMatch(/R\$/);
    expect(formatEntryAuditFieldValue("1.5", "percent")).toMatch(/%/);
    expect(formatEntryAuditFieldValue("2026-11-15", "date")).toBe("15/11/2026");
    expect(formatEntryAuditFieldValue("5102", "text")).toBe("5102");
    expect(
      formatOccurrenceValue("170.00", { field: "total" }),
    ).toMatch(/R\$/);
    expect(
      formatOccurrenceValue("12.00", { field: "rate" }),
    ).toMatch(/%/);
    expect(resolveEntryAuditField({ field: "cfop" })?.kind).toBe("text");
  });
});
