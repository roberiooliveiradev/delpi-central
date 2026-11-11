/** PRC-REF-023-UI-FIX-07 — estrutura da página de acompanhamento PRC
 * do solicitante. Garante a ficha compartilhada única (não uma segunda
 * implementação local), hero + duas abas, documentos dentro da ficha,
 * correção contextual e zero privilégio/acesso de Engenharia. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

const page = readFileSync(
  join(root, "features/product-registration/PrcCasePage.tsx"),
  "utf8",
);
const api = readFileSync(
  join(root, "features/product-registration/prcApi.ts"),
  "utf8",
);

function indexOfOrFail(source: string, token: string): number {
  const idx = source.indexOf(token);
  expect(idx, `missing token: ${token}`).toBeGreaterThanOrEqual(0);
  return idx;
}

describe("PrcCasePage — composição compartilhada", () => {
  it("usa a ficha de leitura única do kit (não implementa a própria)", () => {
    expect(page).toMatch(/PrcTechnicalSheetView/);
    expect(page).toMatch(/from "@delpi\/plugin-ui\/index"/);
    // Proibição de segunda ficha: sem grupos/grid JSX próprios.
    expect(page).not.toMatch(/FIELD_GROUPS/);
    expect(page).not.toMatch(/delpi-prc__sheet-grid/);
    expect(page).not.toMatch(/delpi-prc__sheet-field/);
    expect(page).not.toMatch(/delpi-prc__sheet-table/);
  });

  it("hero consolida identificação, status, datas e progresso", () => {
    expect(page).toMatch(/Acompanhamento da solicitação/);
    expect(page).toMatch(/PRC_TYPE_LABELS\[detail\.requestType\]/);
    expect(page).toMatch(/officialCode/);
    expect(page).toMatch(/createdAt/);
    expect(page).toMatch(/updatedAt/);
    expect(page).toMatch(/prcRequesterLabel\(detail\.requester\)/);
    expect(page).toMatch(/PrcWorkflowProgress/);
  });

  it("expõe exatamente Ficha técnica e Histórico, ficha como inicial", () => {
    expect(page).toMatch(/key: "sheet", label: "Ficha técnica"/);
    expect(page).toMatch(/key: "history", label: "Histórico"/);
    expect(page).toMatch(/useState<CaseTab>\("sheet"\)/);
    // Solicitante não recebe abas de atendimento técnico.
    expect(page).not.toMatch(/Verificação TOTVS/i);
    expect(page).not.toMatch(/Revisões/);
    expect(page).not.toMatch(/verification/i);
    expect(page).not.toMatch(/revisions/i);
  });

  it("documentos vivem somente na aba Ficha técnica", () => {
    const sheetIdx = indexOfOrFail(page, 'tab === "sheet"');
    const docsIdx = indexOfOrFail(page, "Documentos de apoio");
    const historyIdx = indexOfOrFail(page, 'tab === "history"');
    // Ordem: bloco ficha → Documentos → bloco histórico.
    expect(docsIdx).toBeGreaterThan(sheetIdx);
    expect(historyIdx).toBeGreaterThan(docsIdx);
    // Uma única renderização de documentos.
    expect(page.match(/Documentos de apoio/g)).toHaveLength(1);
    expect(page).toMatch(/MyRequestsAttachmentPreviewStrip/);
    expect(page).toMatch(/downloadPrcAttachment/);
  });

  it("correção é contextual na ficha — não é aba nem update livre", () => {
    expect(page).toMatch(/detail\?\.status === "needs_correction"/);
    expect(page).toMatch(/correctionExchange\?\.canCorrect === true/);
    expect(page).toMatch(/openReturn\?\.targets/);
    expect(page).toMatch(/savePrcReturnedFields/);
    expect(page).toMatch(/resubmitPrcCorrection/);
    // Correção preserva o mesmo requestId oficial.
    expect(page).toMatch(/resubmitPrcCorrection\(\s*requestId/);
  });

  it("edição pré-atendimento só quando o backend emite edit_draft (FIX-08)", () => {
    // Ação visível exclusivamente por allowedActions do backend.
    expect(page).toMatch(/allowedActions\?\.includes\("edit_draft"\)/);
    // Mesmo formulário compartilhado do kit — nunca um terceiro wizard.
    expect(page).toMatch(/PrcRequestForm/);
    expect(page).toMatch(/editCase=\{\{/);
    // Mesmo requestId e CAS pela versão atual do caso.
    expect(page).toMatch(/requestId,\s*\n\s*expectedVersion: detail\.caseVersion/);
    // Provider salva via PATCH /draft canônico, mesmo requestId.
    expect(page).toMatch(/saveDraft: \(caseId, expectedVersion, changes, idempotencyKey\) =>/);
    expect(page).toMatch(/updatePrcDraft\(\s*caseId,\s*expectedVersion,\s*changes,\s*idempotencyKey,/);
    expect(api).toMatch(/export function updatePrcDraft\(/);
    expect(api).toMatch(/\/draft/);
    expect(api).toMatch(/Idempotency-Key/);
    // Após salvar, o caso é recarregado (mesma identidade).
    expect(page).toMatch(/setEditing\(false\);\s*\n\s*load\(\);/);
  });

  it("histórico usa o renderer padronizado de Minhas Solicitações", () => {
    expect(page).toMatch(/RequestHistoryTimeline/);
    expect(page).toMatch(/prcTimelineItemViews\(timeline\)/);
  });

  it("ficha consome o contrato autoritativo da Engineering API", () => {
    expect(page).toMatch(/detail\.technicalDraft/);
    expect(page).toMatch(/detail\.changedPaths/);
    expect(page).toMatch(/officialBaseline\?\.fields/);
    expect(api).toMatch(/technicalDraft\?/);
    expect(api).toMatch(/officialBaseline\?/);
  });

  it("zero privilégio de Engenharia e zero chamada direta à api-delpi", () => {
    expect(page).not.toMatch(/engineering\.access/);
    expect(page).not.toMatch(/apiDelpiUrl|API_DELPI_BASE|\/apps\/api-delpi/);
    expect(api).not.toMatch(/apiDelpiUrl|API_DELPI_BASE|\/apps\/api-delpi/);
  });
});
