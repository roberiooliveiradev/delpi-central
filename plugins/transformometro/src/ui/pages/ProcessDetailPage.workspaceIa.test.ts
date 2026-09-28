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
    expect(resultsSection).toMatch(/needs_instance_selection/);
    expect(resultsSection).toMatch(/Selecione uma melhoria para visualizar este conteúdo/);
    expect(resultsSection).toMatch(/buildRevisionComparisonView/);
    expect(resultsSection).toMatch(/data-selected-instancia=\{comparison\.instanceId\}/);
  });

  it("CASE F/G: comparação distingue calculado e não inventa authority", () => {
    expect(resultsSection).toMatch(/Ver comparação detalhada/);
    expect(resultsSection).toMatch(/fetchProcessoComparativo/);
    expect(resultsSection).toMatch(/Ainda não há baseline\/medição comparável/);
    expect(resultsSection).toMatch(/legacy_reference_missing/);
  });

  it("CASE T: scoped revisões usam um único comparison.instanceId", () => {
    expect(resultsSection).toMatch(/data-selected-instancia=\{comparison\.instanceId\}/);
    expect(resultsSection).toMatch(/filterComparativoByRevisoes/);
    expect(resultsSection).toMatch(/scopedComparisonItems/);
  });
});

describe("Deep-linked selection — URL = navigation authority", () => {
  it("R: seleção de melhoria/cenário vem da rota, não de state local", () => {
    expect(resultsSection).toMatch(/routeInstanciaId/);
    expect(resultsSection).toMatch(/routeRevisaoId/);
    expect(resultsSection).toMatch(/selectedInstanciaId = routeInstanciaId/);
    expect(resultsSection).toMatch(/selectedRevisaoId = routeRevisaoId/);
    expect(resultsSection).not.toMatch(/useState<string \| null>\(null\);\s*\n\s*const \[selected/);
  });

  it("B/C: escolhas navegam para P/I/R preservando a seção atual", () => {
    expect(resultsSection).toMatch(/navigateSelection/);
    expect(resultsSection).toMatch(/buildProcessoPath\(processoId, revisaoId, instanciaId\)/);
    expect(resultsSection).toMatch(/window\.location\.hash \|\| "#resultados"/);
    expect(resultsSection).toMatch(/navigateSelection\(comparison\.instanceId, revisao\.revisao_id\)/);
    expect(resultsSection).toMatch(/navigateSelection\(instancia\.instancia_id, null\)/);
  });

  it("J/K: trocar melhoria limpa revisão — nunca mistura cross-instance", () => {
    expect(resultsSection).toMatch(/navigateSelection\(null, null\)/);
    expect(resultsSection).not.toMatch(/setSelectedRevisaoId/);
    expect(resultsSection).not.toMatch(/setSelectedInstanciaId/);
  });

  it("D: nav de seções preserva P/I/R — workspace page e chrome usam view efetiva", () => {
    expect(workspacePage).toMatch(/resolveWorkspacePanelView/);
    expect(workspacePage).toMatch(/useWorkspaceLocationHash/);
    expect(workspacePage).toMatch(/routeInstanciaId=\{route\.instanciaId\}/);
    expect(workspacePage).toMatch(/routeRevisaoId=\{route\.revisaoId\}/);
    expect(detailPage).toMatch(/buildProcessWorkspacePath/);
    expect(detailPage).toMatch(/routeInstanciaId=\{routeInstanciaId\}/);
    expect(detailPage).toMatch(/routeRevisaoId=\{routeRevisaoId\}/);
  });
});
