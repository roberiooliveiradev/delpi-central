/** PRC-REF-022-FIX-02 — devolução simplificada: lista única de
 * checkboxes (SB1 + SA5) sem seção especial de fornecedores. */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { prcReturnEntryList } from "./PrcReturnForCorrectionModal";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(
  join(here, "PrcReturnForCorrectionModal.tsx"),
  "utf8",
);

const SPECS = [
  { path: "description", kind: "text" },
  { path: "group", kind: "text" },
  { path: "productKind", kind: "text" },
  { path: "unit", kind: "text" },
  { path: "defaultWarehouse", kind: "text" },
  { path: "accountingAccount", kind: "text" },
  { path: "thirdPartyProduct", kind: "text" },
  { path: "customerReference", kind: "text" },
  { path: "officialProductCode", kind: "text" },
  { path: "suppliers", kind: "suppliers" },
] as never[];

const SUP_A = { supplierCode: "000123", store: "01", supplierName: "F1" };
const SUP_B = { supplierCode: "000456", store: "02", supplierName: "F2" };

describe("PrcReturnForCorrectionModal — FIX-02 lista unificada", () => {
  it("campos SB1 viram entradas checkbox na lista única", () => {
    const entries = prcReturnEntryList(SPECS, []);
    const fields = entries.filter((e) => e.kind === "field");
    expect(fields.map((f) => f.key)).toEqual([
      "FIELD:description",
      "FIELD:group",
      "FIELD:productKind",
      "FIELD:unit",
      "FIELD:defaultWarehouse",
      "FIELD:accountingAccount",
      "FIELD:thirdPartyProduct",
      "FIELD:customerReference",
    ]);
    // officialProductCode imutável nunca é devolvível.
    expect(entries.some((e) => e.key.includes("officialProductCode"))).toBe(
      false,
    );
    // path agregado 'suppliers' nunca é checkbox direto.
    expect(
      entries.some((e) => e.kind === "field" && e.path === "suppliers"),
    ).toBe(false);
  });

  it("vínculo único gera Fornecedor, Part Number e Catálogo como checkboxes", () => {
    const entries = prcReturnEntryList(SPECS, [SUP_A]);
    const sup = entries.filter((e) => e.kind === "supplier");
    expect(sup.map((e) => e.targetAttribute)).toEqual([
      null,
      "partNumber",
      "catalogNumber",
    ]);
    expect(sup.map((e) => e.label)).toEqual([
      "Fornecedor",
      "Part Number",
      "Catálogo",
    ]);
    // Identidade técnica preservada na entrada — invisível ao analista.
    for (const e of sup) {
      expect(e.supplierCode).toBe("000123");
      expect(e.store).toBe("01");
    }
  });

  it("múltiplos fornecedores preservam identidade no rótulo e na chave", () => {
    const entries = prcReturnEntryList(SPECS, [SUP_A, SUP_B]);
    const sup = entries.filter((e) => e.kind === "supplier");
    expect(sup).toHaveLength(6);
    expect(sup.map((e) => e.label)).toContain(
      "Part Number — Fornecedor 000123 / 01",
    );
    expect(sup.map((e) => e.label)).toContain(
      "Catálogo — Fornecedor 000456 / 02",
    );
    expect(sup.map((e) => e.label)).toContain("Fornecedor 000123 / 01");
    const keys = sup.map((e) => e.key);
    expect(new Set(keys).size).toBe(6);
    expect(keys).toContain("SUP:000123|01:partNumber");
    expect(keys).toContain("SUP:000456|02:catalogNumber");
  });

  it("zeros à esquerda e vínculos duplicados são tratados", () => {
    const entries = prcReturnEntryList(SPECS, [SUP_A, SUP_A, SUP_A]);
    const sup = entries.filter((e) => e.kind === "supplier");
    expect(sup).toHaveLength(3); // dedup por (code, store)
    expect(sup[1].supplierCode).toBe("000123");
    expect(sup[1].store).toBe("01");
  });

  it("sem fornecedores a lista tem apenas campos SB1", () => {
    const entries = prcReturnEntryList(SPECS, []);
    expect(entries.every((e) => e.kind === "field")).toBe(true);
  });

  it("sem seção especial: sem botão Adicionar vínculo nem pesquisa de fornecedor", () => {
    expect(SRC).not.toMatch(/Adicionar vínculo/);
    expect(SRC).not.toMatch(/PrcOfficialSupplierSearchField/);
    expect(SRC).not.toMatch(/EngineeringSearchableSelect/);
    expect(SRC).not.toMatch(/supplierTargets|SupplierTargetDraft/);
    expect(SRC).not.toMatch(/useSupplierSearch/);
    expect(SRC).not.toMatch(/Vínculos de fornecedores/);
  });

  it("cada entrada rende checkbox + motivo no mesmo padrão", () => {
    // Um único loop de renderização para todas as entradas.
    expect(SRC).toMatch(/entries\.map\(\(entry\)/);
    expect(SRC).toMatch(/EngineeringCheckboxControl/);
    expect(SRC).toMatch(/Motivo da correção/);
    expect(SRC).toMatch(/reason\.length < 3/);
  });

  it("payload: entradas SA5 viram SUPPLIER_LINK com identidade completa", () => {
    expect(SRC).toMatch(/targetType: "SUPPLIER_LINK"/);
    expect(SRC).toMatch(/targetPath: "suppliers"/);
    expect(SRC).toMatch(/targetAttribute: entry\.targetAttribute/);
    expect(SRC).toMatch(/supplierKey: \{/);
    expect(SRC).toMatch(/supplierCode: entry\.supplierCode/);
    expect(SRC).toMatch(/store: entry\.store/);
  });

  it("nenhum campo selecionado bloqueia a devolução", () => {
    expect(SRC).toMatch(/!targets\.length/);
    expect(SRC).toMatch(/Selecione ao menos um campo/);
  });

  it("entrada 'Fornecedor' (link integral) não envia targetAttribute", () => {
    const [link] = prcReturnEntryList(SPECS, [SUP_A]).filter(
      (e) => e.kind === "supplier" && e.targetAttribute === null,
    );
    expect(link).toBeDefined();
    expect(link?.kind).toBe("supplier");
  });
});
