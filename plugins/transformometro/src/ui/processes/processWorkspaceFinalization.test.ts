import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  parseProcessoSecondaryFocusFromHash,
  parseProcessoSectionFromHash,
} from "./processWorkspaceNav";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const results = readFileSync(join(root, "ui/processes/ProcessResultsSection.tsx"), "utf8");
const docs = readFileSync(join(root, "ui/processes/ProcessDocumentationSection.tsx"), "utf8");
const detail = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");

describe("Process Workspace finalization — Results composition", () => {
  it("compõe medição/investimentos/recursos inline read-only no mesmo contextInstanciaId", () => {
    expect(results).toMatch(/data-selected-instancia=\{contextInstanciaId\}/);
    expect(results).toMatch(/data-selected-revisao=\{contextRevisaoId/);
    expect(results).toMatch(/RevisionMeasurementSection/);
    expect(results).toMatch(/RevisionInvestmentsSection/);
    expect(results).toMatch(/RevisionSharedResourcesSection/);
    expect(results).toMatch(/readOnly/);
    expect(results).toMatch(/fetchMedicao/);
    expect(results).toMatch(/fetchInvestimentos/);
    expect(results).toMatch(/fetchVinculos/);
    expect(results).toMatch(/Benefícios calculados/);
    expect(results).toMatch(/Comparação calculada/);
  });

  it("CASE multiple instance: exige seleção explícita e não usa fallback arbitrário", () => {
    expect(results).toMatch(/requiresInstanceSelection/);
    expect(results).toMatch(/Selecione uma melhoria para visualizar este conteúdo/);
    expect(results).toMatch(/if \(requiresInstanceSelection\) return selectedInstanciaId/);
    expect(results).toMatch(/if \(instancias\.length === 1\) return instancias\[0\]/);
  });

  it("CASE cross-instance: comparison e bundle usam o mesmo contexto filtrado", () => {
    expect(results).toMatch(/scopedComparisonItems/);
    expect(results).toMatch(/allowed\.has\(row\.revisao_id\)/);
    expect(results).toMatch(/loadRevisionBundle\(contextRevisaoId\)/);
    expect(results).toMatch(/setSelectedRevisaoId\(null\)/);
  });

  it("custos unitários do catálogo permanecem link-only (owner Configurações)", () => {
    expect(results).toMatch(/Recursos e custos/);
    expect(results).toMatch(/Configurações → Recursos compartilhados/);
    expect(results).not.toMatch(/RecursoCustosSection/);
  });

  it("lazy: comparação e bundle só com active", () => {
    expect(results).toMatch(/if \(!active\) return/);
    expect(results).toMatch(/if \(!active \|\| !contextRevisaoId\)/);
  });
});

describe("Process Workspace finalization — Documentation CTA", () => {
  it("mantém uma única CTA primária Novo documento no header", () => {
    const primaryCtas = docs.match(/Novo documento/g) ?? [];
    expect(primaryCtas).toHaveLength(1);
    expect(docs).toMatch(/ds-btn--primary[\s\S]{0,80}Novo documento/);
    const emptyBlock = docs.slice(docs.indexOf("<EmptyState"));
    expect(emptyBlock).not.toMatch(/Novo documento/);
  });

  it("usa heading Documentos sob a primary Documentação", () => {
    expect(docs).toMatch(/tm-process-documentacao-title[\s\S]*?Documentos/);
    expect(detail).toMatch(/Documentação/);
  });
});

describe("Process Workspace finalization — legacy deep links", () => {
  it.each([
    ["#dados", "visao-geral", null],
    ["#diagrama", "mapeamento", "fluxo"],
    ["#arquivos", "documentacao", "arquivos"],
    ["#priorizacao", "melhorias", "priorizacao"],
  ] as const)("%s → primary %s secondary %s", (hash, primary, secondary) => {
    expect(parseProcessoSectionFromHash(hash)).toBe(primary);
    expect(parseProcessoSecondaryFocusFromHash(hash)).toBe(secondary);
  });

  it("secondary mount é progressivo (não hidden dual-mount)", () => {
    expect(detail).toMatch(/mapeamentoFocus === "fluxo" \?/);
    expect(detail).toMatch(/documentacaoFocus === "arquivos" \?/);
    expect(detail).toMatch(/melhoriasFocus === "priorizacao" \?/);
    expect(detail).not.toMatch(/hidden=\{mapeamentoFocus/);
    expect(detail).not.toMatch(/hidden=\{documentacaoFocus/);
    expect(detail).not.toMatch(/hidden=\{melhoriasFocus/);
  });
});
