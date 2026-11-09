import { describe, expect, it } from "vitest";

import type { PrcFieldResult, PrcVerification } from "./api/productRegistrationApi";
import {
  buildDiagnosisItems,
  diagnosisItemRoutingKey,
  formatDiagnosticValue,
  pickActiveFieldResults,
  summarizeDiagnosis,
  technicalTargetElementId,
} from "./prcVerificationDiagnosis";

const fieldResults: Record<string, PrcFieldResult> = {
  description: {
    result: "mismatched",
    expected: "CHICOTE A",
    observed: "CHICOTE B",
    reason: "mismatch",
  },
  group: {
    result: "matched",
    expected: "1001",
    observed: "1001",
  },
  unit: {
    result: "mismatched",
    expected: "UN",
    observed: "PC",
    reason: "mismatch",
  },
  accountingAccount: {
    result: "unverifiable",
    expected: "11401002",
    observed: null,
    reason: "field_absent",
  },
  customerReference: {
    result: "mismatched",
    expected: "REF-1",
    observed: "",
    reason: "mismatch",
  },
  suppliers: {
    result: "mismatched",
    detail: [
      {
        key: "update:000123.01",
        result: "partNumber:mismatched",
        supplierCode: "000123",
        store: "01",
        operation: "update",
        attributes: [
          {
            attribute: "partNumber",
            expected: "PN-2026",
            observed: "PN-2025",
            result: "mismatched",
            reasonCode: "mismatch",
          },
          {
            attribute: "catalogNumber",
            expected: "CAT-001",
            observed: "CAT-001",
            result: "matched",
          },
        ],
      },
    ],
  },
};

describe("prcVerificationDiagnosis", () => {
  it("counts problems without double-counting suppliers aggregate", () => {
    const summary = summarizeDiagnosis({ fieldResults });
    // description, unit, accountingAccount, customerReference, PN = 5
    expect(summary.problems).toBe(5);
    expect(summary.matched).toBe(2); // group + catalogNumber
    expect(summary.totalChecks).toBe(7);
    expect(summary.problemItems.every((i) => i.isProblem)).toBe(true);
  });

  it("builds specific observations for mismatched and unverifiable fields", () => {
    const items = buildDiagnosisItems(fieldResults);
    const desc = items.find((i) => i.path === "description");
    expect(desc?.observation).toMatch(/descrição solicitada é diferente/i);
    const acct = items.find((i) => i.path === "accountingAccount");
    expect(acct?.observation).toMatch(/Não foi possível confirmar/i);
    const emptyOfficial = items.find((i) => i.path === "customerReference");
    expect(emptyOfficial?.observation).toMatch(/valor vazio/i);
  });

  it("formats empty vs absent distinctly", () => {
    expect(formatDiagnosticValue("")).toMatch(/Vazio/);
    expect(formatDiagnosticValue(null)).toMatch(/Não retornado/);
    expect(formatDiagnosticValue("X")).toBe("X");
  });

  it("keeps PN and catalog separate for SA5", () => {
    const items = buildDiagnosisItems(fieldResults).filter(
      (i) => i.kind === "supplier_attribute",
    );
    expect(items).toHaveLength(2);
    expect(items[0].attribute).toBe("partNumber");
    expect(items[0].isProblem).toBe(true);
    expect(items[1].attribute).toBe("catalogNumber");
    expect(items[1].isProblem).toBe(false);
    expect(items[0].supplierCode).toBe("000123");
    expect(items[0].store).toBe("01");
  });

  it("preserves leading zeros in supplier identity", () => {
    const items = buildDiagnosisItems({
      suppliers: {
        result: "mismatched",
        detail: [
          {
            key: "update:000089.01",
            result: "mismatched",
            supplierCode: "000089",
            store: "01",
            reasonCode: "missing_in_official",
            attributes: [],
          },
        ],
      },
    });
    expect(items[0].supplierCode).toBe("000089");
    expect(items[0].label).toMatch(/000089/);
  });

  it("parses legacy SA5 detail tokens", () => {
    const items = buildDiagnosisItems({
      suppliers: {
        result: "mismatched",
        detail: [
          {
            key: "update:000010.01",
            result: "partNumber:mismatched,catalogNumber:matched",
          },
        ],
      },
    });
    expect(items).toHaveLength(2);
    expect(items.filter((i) => i.isProblem)).toHaveLength(1);
  });

  it("treats infra global results without inventing field problems", () => {
    const summary = summarizeDiagnosis({
      fieldResults,
      globalResult: "timeout",
    });
    expect(summary.isInfra).toBe(true);
    expect(summary.problems).toBe(0);
    expect(summary.items).toHaveLength(0);
  });

  it("prefers persisted verification after refresh and clears stale error on completed", () => {
    const verification: PrcVerification = {
      id: "v1",
      official_product_code: "10080022",
      checked_at: "2026-11-09T12:00:00Z",
      result: "mismatched",
      field_results: fieldResults,
    };
    const active = pickActiveFieldResults({
      verifications: [verification],
      lastError: { description: { result: "mismatched" } },
      status: "in_progress",
    });
    expect(active.fieldResults).toBe(fieldResults);
    const done = pickActiveFieldResults({
      verifications: [verification],
      lastError: { description: { result: "mismatched" } },
      status: "completed",
    });
    expect(done.staleError).toBe(true);
  });

  it("builds navigation element ids for field and supplier", () => {
    const field = buildDiagnosisItems(fieldResults).find(
      (i) => i.path === "description",
    )!;
    expect(technicalTargetElementId(field)).toBe("prc-field-description");
    const pn = buildDiagnosisItems(fieldResults).find(
      (i) => i.attribute === "partNumber",
    )!;
    expect(technicalTargetElementId(pn)).toBe(
      "prc-supplier-000123-01-partNumber",
    );
  });

  it("builds stable routing keys for SB1 and SA5 (REF-021)", () => {
    const field = buildDiagnosisItems(fieldResults).find(
      (i) => i.path === "unit",
    )!;
    expect(diagnosisItemRoutingKey(field)).toBe("FIELD:unit");
    const pn = buildDiagnosisItems(fieldResults).find(
      (i) => i.attribute === "partNumber",
    )!;
    expect(diagnosisItemRoutingKey(pn)).toBe(
      "SUPPLIER_LINK:000123/01:partNumber",
    );
  });

  it("puts SB1 and SA5 problems in one flat item list", () => {
    const items = buildDiagnosisItems(fieldResults);
    expect(items.some((i) => i.kind === "field")).toBe(true);
    expect(items.some((i) => i.kind === "supplier_attribute")).toBe(true);
    expect(items.filter((i) => i.isProblem).map((i) => i.label).join("|")).toMatch(
      /Unidade|Descrição|Part Number|Conta|Referência/i,
    );
  });
});
