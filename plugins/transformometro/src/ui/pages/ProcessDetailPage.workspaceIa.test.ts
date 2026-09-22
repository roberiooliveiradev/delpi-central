import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  parseProcessoSecondaryFocusFromHash,
  parseProcessoSectionFromHash,
  PROCESSO_WORKSPACE_SECTIONS,
} from "../processes/processWorkspaceNav";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const detailPage = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
const workspacePage = readFileSync(join(root, "ui/pages/ProcessWorkspacePage.tsx"), "utf8");
const resultsSection = readFileSync(join(root, "ui/processes/ProcessResultsSection.tsx"), "utf8");

describe("Process Workspace IA consolidation", () => {
  it("CASE H–N: legacy hashes resolvem primary correto", () => {
    const cases: Array<[string, string, string | null]> = [
      ["#dados", "visao-geral", null],
      ["#diagrama", "mapeamento", "fluxo"],
      ["#arquivos", "documentacao", "arquivos"],
      ["#priorizacao", "melhorias", "priorizacao"],
      ["#tarefas", "tarefas", null],
      ["#sala", "sala", null],
      ["#timeline", "historico", null],
    ];
    for (const [hash, primary, secondary] of cases) {
      expect(parseProcessoSectionFromHash(hash)).toBe(primary);
      expect(parseProcessoSecondaryFocusFromHash(hash)).toBe(secondary);
    }
  });

  it("CASE U: initial load do detail não dispara reads pesados no Promise.all de entry", () => {
    expect(detailPage).toMatch(/fetchProcesso\(/);
    expect(detailPage).toMatch(/fetchRevisoes\(/);
    expect(detailPage).toMatch(/fetchOptions\(/);
    expect(detailPage).toMatch(/fetchProcessoInstancias\(/);

    // Heavy reads must not be in the entry load Promise.all.
    const loadMatch = detailPage.match(
      /const load = useCallback\(async \(\) => \{[\s\S]*?\}, \[getAccessToken, processoId\]\);/,
    );
    expect(loadMatch?.[0]).toBeTruthy();
    const entryLoad = loadMatch![0];
    expect(entryLoad).not.toMatch(/fetchProcessoDiagrama/);
    expect(entryLoad).not.toMatch(/fetchProcessoDecomposicao/);
    expect(entryLoad).not.toMatch(/fetchProcessoArquivos/);
    expect(entryLoad).not.toMatch(/fetchProcessoComparativo/);
    expect(entryLoad).not.toMatch(/fetchProcessTimeline/);
    expect(entryLoad).not.toMatch(/listProcessoRelatedTasks/);
    expect(entryLoad).not.toMatch(/openInteractionRoom/);
  });

  it("CASE U: workspace chrome tree não busca arquivos no entry", () => {
    expect(workspacePage).not.toMatch(/fetchProcessoArquivos/);
  });

  it("CASE O/P: seções usam mount-on-visit (visibleSections)", () => {
    expect(detailPage).toMatch(/mountedSections/);
    expect(detailPage).toMatch(/visibleSections\.has\("mapeamento"\)/);
    expect(detailPage).toMatch(/visibleSections\.has\("resultados"\)/);
    expect(detailPage).toMatch(/visibleSections\.has\("historico"\)/);
  });

  it("CASE Q/R/S: histórico tem loading/erro local e timeline só no historico", () => {
    expect(detailPage).toMatch(/activeSection !== "historico"/);
    expect(detailPage).toMatch(/Falha ao carregar histórico/);
    expect(detailPage).toMatch(/ProcessTimeline/);
  });

  it("primary nav final tem 8 itens", () => {
    expect(PROCESSO_WORKSPACE_SECTIONS).toHaveLength(8);
    expect(detailPage).toMatch(/sectionId="resultados"/);
    expect(detailPage).toMatch(/ProcessResultsSection/);
    expect(detailPage).not.toMatch(/sectionId="dados"/);
    expect(detailPage).not.toMatch(/sectionId="diagrama"/);
    expect(detailPage).not.toMatch(/sectionId="timeline"/);
  });
});

describe("ProcessResultsSection context isolation", () => {
  it("CASE C/T: múltiplas instâncias exigem seleção explícita", () => {
    expect(resultsSection).toMatch(/requiresInstanceSelection/);
    expect(resultsSection).toMatch(/Selecione uma melhoria para visualizar este conteúdo/);
    expect(resultsSection).toMatch(/if \(requiresInstanceSelection\) return selectedInstanciaId/);
    expect(resultsSection).toMatch(/data-selected-instancia=\{contextInstanciaId\}/);
  });

  it("CASE F/G: comparação distingue calculado e não inventa authority", () => {
    expect(resultsSection).toMatch(/Comparação \(calculado\)/);
    expect(resultsSection).toMatch(/fetchProcessoComparativo/);
    expect(resultsSection).toMatch(/Ainda não há baseline\/medição comparável/);
  });

  it("CASE T: scoped revisões usam um único contextInstanciaId", () => {
    expect(resultsSection).toMatch(/const contextInstanciaId = resolvedInstanciaId/);
    expect(resultsSection).toMatch(/buildProcessoPath\(processoId, revisao\.revisao_id, contextInstanciaId\)/);
  });
});
