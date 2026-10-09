import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

const api = readFileSync(join(root, "data/api/bpmnMigrationApi.ts"), "utf8");
const wizard = readFileSync(
  join(root, "components/process/BpmnMigrationWizard.tsx"),
  "utf8"
);
const card = readFileSync(
  join(root, "components/process/ProcessBpmnCard.tsx"),
  "utf8"
);
const page = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");

describe("G8 — migração governada flowchart_v1 → BPMN nativo", () => {
  it("client usa o caminho governado canônico (prepare → commit_proposal)", () => {
    // Mesma superfície TÉO — nunca um executor genérico de XML (§109).
    expect(api).toMatch(/governed-operations\/prepare/);
    expect(api).toMatch(/migrate_legacy_diagram_to_native_bpmn/);
    expect(api).toMatch(/proposals\/commit/);
    expect(api).toMatch(/confirmation:\s*true/);
    // Resolutions trafegam no re-PREPARE, nunca no commit direto.
    expect(api).toMatch(/\.\.\.\(resolutions \? \{ resolutions \} : \{\}\)/);
    // Nenhuma rota de escrita direta em documento BPMN/legado.
    expect(api).not.toMatch(/bpmn-document.*method:\s*"POST"/);
    expect(api).not.toMatch(/processes\/\$\{.*\}\/diagram.*POST/);
  });

  it("wizard PREPARE no mount + relatório com estatísticas e ambiguidades", () => {
    expect(wizard).toMatch(/useEffect[\s\S]*void runPrepare\(\)/);
    expect(wizard).toMatch(/TÉO analisou o mapeamento/);
    expect(wizard).toMatch(/Mapeamentos exatos/);
    expect(wizard).toMatch(/Mapeados por heurística/);
    expect(wizard).toMatch(/resolução humana\s*\n?\s*obrigatória/);
    expect(wizard).toMatch(/Perdas reportadas/);
  });

  it("ambiguidades exigem decisão explícita — sem resolução silenciosa", () => {
    // Opções renderizadas como escolha do usuário (radio), não auto-pick.
    expect(wizard).toMatch(/type="radio"/);
    expect(wizard).toMatch(/allAmbiguitiesAnswered/);
    // Re-PREPARE só habilita depois de todas respondidas.
    expect(wizard).toMatch(
      /disabled=\{!allAmbiguitiesAnswered \|\| busy\}/
    );
    expect(wizard).toMatch(/Re-analisar com resoluções/);
  });

  it("preview é somente leitura e não persiste", () => {
    // Thumbnail render-only; candidate XML vem da proposta selada.
    expect(wizard).toMatch(/renderBpmnThumbnail/);
    expect(wizard).toMatch(/exact_change\.candidate_xml/);
    // Preview não chama save/commit — commit só em handleConfirm.
    expect(wizard).not.toMatch(/saveProcessBpmnWorkingCopy/);
    expect(wizard).toMatch(/handleConfirm[\s\S]*commitBpmnMigration/);
  });

  it("confirmação explicita preservação do legado antes do ACT", () => {
    expect(wizard).toMatch(/Confirmar migração para BPMN/);
    expect(wizard).toMatch(/desenho legado será preservado/i);
    expect(wizard).toMatch(/Cancelar/);
  });

  it("CTA aparece apenas com legado presente e sem autoridade BPMN", () => {
    expect(card).toMatch(/Migrar para BPMN com\s*\n?\s*TÉO/);
    expect(card).toMatch(/\{hasLegacy \? \(/);
    expect(card).toMatch(/BpmnMigrationWizard/);
    // Dentro do branch !document && !hasExternalRef.
    const noDoc = card.indexOf(") : (");
    const cta = card.indexOf("Migrar para BPMN com");
    expect(cta).toBeGreaterThan(noDoc);
  });

  it("legado deixa de ser 'visão vigente' após migração (G8H)", () => {
    expect(page).toMatch(/hasNativeBpmn/);
    expect(page).toMatch(/onDocumentChange/);
    // Estado migrado: legado colapsado, somente leitura, sem edição.
    expect(page).toMatch(/Mapeamento legado/);
    expect(page).toMatch(/<details[\s\S]*legacy-mapping/);
    expect(page).toMatch(/editable=\{false\}/);
    expect(page).toMatch(/edição desabilitada após a migração/);
    // "visão vigente" só existe no branch SEM BPMN nativo.
    const migrated = page.indexOf("{hasNativeBpmn ? (");
    const legacy = page.indexOf(") : (", migrated);
    const vigente = page.indexOf("visão vigente", migrated);
    expect(vigente).toBeGreaterThan(legacy);
  });
});
