import { describe, expect, it } from "vitest";

import {
  duplicateSupplierIndexes,
  emptySupplierRow,
  supplierHitLabel,
  supplierHitMain,
  supplierHitSecondary,
} from "./prcSuppliers";

const hit = (over = {}) => ({
  supplier_code: "000101",
  supplier_store: "01",
  supplier_name: "FORNECEDOR INDUSTRIAL",
  supplier_short_name: "FORNEX",
  ...over,
});

describe("supplierHitLabel/Main", () => {
  it("razão social (A2_NOME) é a linha principal — nunca a fantasia", () => {
    expect(supplierHitMain(hit())).toBe("FORNECEDOR INDUSTRIAL");
    expect(supplierHitLabel(hit())).toBe("FORNECEDOR INDUSTRIAL");
  });
});

describe("supplierHitSecondary", () => {
  it("linha secundária traz código, loja e fantasia distinta", () => {
    expect(supplierHitSecondary(hit())).toBe(
      "Código: 000101 · Loja: 01 · Fantasia: FORNEX",
    );
  });

  it("omite fantasia quando igual à razão social", () => {
    expect(
      supplierHitSecondary(hit({ supplier_short_name: "fornecedor industrial" })),
    ).toBe("Código: 000101 · Loja: 01");
  });

  it("omite fantasia quando vazia", () => {
    expect(
      supplierHitSecondary(hit({ supplier_short_name: " " })),
    ).toBe("Código: 000101 · Loja: 01");
  });
});

describe("duplicateSupplierIndexes", () => {
  it("marca vínculos com mesmo (supplierCode, store)", () => {
    const rows = [
      { ...emptySupplierRow(), supplierCode: "0001", store: "01" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "02" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "01" },
    ];
    expect([...duplicateSupplierIndexes(rows)].sort()).toEqual([0, 2]);
  });

  it("ignora linhas sem identidade completa", () => {
    const rows = [
      { ...emptySupplierRow(), supplierCode: "0001", store: "" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "" },
    ];
    expect(duplicateSupplierIndexes(rows).size).toBe(0);
  });
});
