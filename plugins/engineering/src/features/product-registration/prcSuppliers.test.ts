import { describe, expect, it } from "vitest";

import {
  duplicateDraftRowIds,
  duplicateSupplierIndexes,
  emptySupplierRow,
  findRowWithOfficialKey,
  officialSupplierRow,
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
      supplierHitSecondary(
        hit({ supplier_short_name: "fornecedor industrial" }),
      ),
    ).toBe("Código: 000101 · Loja: 01");
  });

  it("omite fantasia quando vazia", () => {
    expect(supplierHitSecondary(hit({ supplier_short_name: " " }))).toBe(
      "Código: 000101 · Loja: 01",
    );
  });
});

describe("row identity (D14-FIX-02)", () => {
  it("emptySupplierRow e officialSupplierRow têm rowId/origin distintos", () => {
    const d = emptySupplierRow();
    const o = officialSupplierRow({
      supplierCode: "000002",
      store: "01",
      supplierName: "TE",
    });
    expect(d.origin).toBe("draft");
    expect(o.origin).toBe("official");
    expect(d.rowId).not.toBe(o.rowId);
    expect(d.rowId.length).toBeGreaterThan(4);
  });

  it("duplicateDraftRowIds marca só a candidata, preserva oficial", () => {
    const official = officialSupplierRow({
      supplierCode: "000002",
      store: "01",
      supplierName: "TE",
    });
    const draft = {
      ...emptySupplierRow(),
      supplierCode: "000002",
      store: "01",
      supplierName: "TE",
    };
    const dups = duplicateDraftRowIds([official, draft]);
    expect(dups.has(draft.rowId)).toBe(true);
    expect(dups.has(official.rowId)).toBe(false);
  });

  it("dois drafts com mesma chave: ambos marcados", () => {
    const a = {
      ...emptySupplierRow(),
      supplierCode: "0001",
      store: "01",
    };
    const b = {
      ...emptySupplierRow(),
      supplierCode: "0001",
      store: "01",
    };
    const dups = duplicateDraftRowIds([a, b]);
    expect(dups.has(a.rowId)).toBe(true);
    expect(dups.has(b.rowId)).toBe(true);
  });

  it("findRowWithOfficialKey ignora exceptRowId", () => {
    const official = officialSupplierRow({
      supplierCode: "000002",
      store: "01",
      supplierName: "TE",
    });
    const draft = emptySupplierRow();
    expect(
      findRowWithOfficialKey(
        [official, draft],
        "000002",
        "01",
        draft.rowId,
      )?.rowId,
    ).toBe(official.rowId);
    expect(
      findRowWithOfficialKey(
        [official],
        "000002",
        "01",
        official.rowId,
      ),
    ).toBeUndefined();
  });

  it("remover linha intermediária não desloca rowIds das demais", () => {
    const a = emptySupplierRow();
    const b = emptySupplierRow();
    const c = emptySupplierRow();
    const after = [a, b, c].filter((r) => r.rowId !== b.rowId);
    expect(after.map((r) => r.rowId)).toEqual([a.rowId, c.rowId]);
  });
});

describe("duplicateSupplierIndexes (compat)", () => {
  it("marca índices das candidatas duplicadas", () => {
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
