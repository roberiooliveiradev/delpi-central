/** PRC-REF-022-FIX-02 / GRANULAR-CORRECTION-09 — modal de devolução:
 * lista unificada de alvos (SB1 + células SA5) delegada ao componente
 * compartilhado do kit. A seleção granular por vínculo+atributo e o
 * payload do contrato são testados no próprio kit
 * (PrcCorrectionTargets.test.tsx); aqui ficam o contrato do modal e
 * as garantias de não-duplicação de UI. */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { prcReturnFieldOptions } from "./PrcReturnForCorrectionModal";

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

describe("prcReturnFieldOptions — campos elegíveis", () => {
  it("campos SB1 do catálogo viram opções com label oficial", () => {
    const options = prcReturnFieldOptions(SPECS);
    expect(options.map((o) => o.path)).toEqual([
      "description",
      "group",
      "productKind",
      "unit",
      "defaultWarehouse",
      "accountingAccount",
      "thirdPartyProduct",
      "customerReference",
    ]);
    // officialProductCode imutável nunca é devolvível.
    expect(options.some((o) => o.path === "officialProductCode")).toBe(
      false,
    );
    // path agregado 'suppliers' nunca é checkbox direto — vínculos
    // têm alvo próprio (SUPPLIER_LINK por célula).
    expect(options.some((o) => o.path === "suppliers")).toBe(false);
  });

  it("sem specs, usa os candidatos oficiais", () => {
    const options = prcReturnFieldOptions(null);
    expect(options.length).toBeGreaterThan(0);
    expect(options.some((o) => o.path === "description")).toBe(true);
    expect(options.some((o) => o.path === "officialProductCode")).toBe(
      false,
    );
  });

  it("paths duplicados no catálogo não repetem checkbox", () => {
    const dup = [...SPECS, { path: "unit", kind: "text" }] as never[];
    const options = prcReturnFieldOptions(dup);
    expect(
      options.filter((o) => o.path === "unit"),
    ).toHaveLength(1);
  });
});

describe("PrcReturnForCorrectionModal — composição compartilhada", () => {
  it("a seleção granular é o componente do kit — sem UI duplicada", () => {
    expect(SRC).toContain("PrcCorrectionTargetSelector");
    expect(SRC).toContain("@delpi/plugin-ui");
    // Nenhuma tabela/checklist própria reimplementada no modal.
    expect(SRC).not.toMatch(/<table|<fieldset/);
    expect(SRC).not.toMatch(/entries\.map/);
    expect(SRC).not.toMatch(/EngineeringCheckboxControl/);
  });

  it("o payload sai do contrato único do kit", () => {
    expect(SRC).toContain("correctionTargetsFromSelection");
    // Nenhum builder local de alvo.
    expect(SRC).not.toMatch(/targetType: "SUPPLIER_LINK"/);
    expect(SRC).not.toMatch(/supplierKey: \{/);
  });

  it("nenhum alvo ou motivo inválido bloqueia o envio", () => {
    expect(SRC).toMatch(/if \(!targets\)/);
    expect(SRC).toContain("setFormError(error)");
  });

  it("diálogo host-contained com título e ações canônicas", () => {
    expect(SRC).toContain("EngineeringHostDialog");
    expect(SRC).toContain("Devolver para correção");
    expect(SRC).toContain("EngineeringFormActions");
    expect(SRC).not.toMatch(/Adicionar vínculo/);
    expect(SRC).not.toMatch(/useSupplierSearch/);
  });

  it("fornecedores vêm da ficha — nunca de busca manual", () => {
    expect(SRC).not.toMatch(/PrcOfficialSupplierSearchField/);
    expect(SRC).not.toMatch(/EngineeringSearchableSelect/);
    expect(SRC).toMatch(/suppliers=\{suppliers \|\| \[\]\}/);
  });
});
