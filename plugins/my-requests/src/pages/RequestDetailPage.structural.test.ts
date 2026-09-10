import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

function indexOfOrFail(source: string, token: string): number {
  const idx = source.indexOf(token);
  expect(idx, `missing token: ${token}`).toBeGreaterThanOrEqual(0);
  return idx;
}

describe("RequestDetailPage structural", () => {
  it("renderiza progresso da API e não hardcodifica percentual por status", () => {
    const page = read("pages/RequestDetailPage.tsx");
    expect(page).toMatch(/journey_progress/);
    expect(page).toMatch(/MyRequestsProgressTracker/);
    expect(page).toMatch(/MyRequestsJourneyProgressBar/);
    expect(page).toMatch(/mapJourneyStagesToTrackerSteps/);
    expect(page).toMatch(/journeyTrackerCompactSummary/);
    expect(page).toMatch(/useViewportMaxWidth/);
    expect(page).not.toMatch(/density="compact"/);
    expect(page).not.toMatch(/status === ["']submitted["'].*33|progressPercent\s*=\s*33/);
    expect(page).not.toMatch(/canProcessAnyRequest/);
  });

  it("passa capabilities específicas aos painéis", () => {
    const page = read("pages/RequestDetailPage.tsx");
    expect(page).toMatch(/can_upload_attachment/);
    expect(page).toMatch(/can_upload_artifact/);
    expect(page).toMatch(/can_comment/);
    expect(page).toMatch(/allowed_actions/);
  });

  it("organiza DOM por fases Solicitação → Atendimento → Histórico", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const css = read("index.css");
    const attachments = read("components/AttachmentsPanel.tsx");
    const artifacts = read("components/ArtifactsPanel.tsx");

    expect(page).toMatch(/my-requests-detail-phase/);
    expect(page).toMatch(/my-requests-detail-service-grid/);
    expect(page).toMatch(/O que foi solicitado/);
    expect(page).toMatch(/Atendimento/);
    expect(page).toMatch(/Histórico/);
    expect(page).not.toMatch(/my-requests-detail-split/);
    expect(page).not.toMatch(/my-requests-detail-history/);
    expect(page).not.toMatch(/my-requests-detail-docs/);
    expect(css).toMatch(/my-requests-detail-phase/);
    expect(css).toMatch(/my-requests-detail-service-grid/);
    expect(css).not.toMatch(/my-requests-detail-split/);

    const requestPhase = indexOfOrFail(page, "my-requests-phase-request");
    const attachmentsIdx = indexOfOrFail(page, "<AttachmentsPanel");
    const servicePhase = indexOfOrFail(page, "my-requests-phase-service");
    const commentsIdx = indexOfOrFail(page, "<CommentsPanel");
    const artifactsIdx = indexOfOrFail(page, "<ArtifactsPanel");
    const historyPhase = indexOfOrFail(page, "my-requests-phase-history");
    const timelineIdx = indexOfOrFail(page, "<TimelinePanel");

    expect(requestPhase).toBeLessThan(attachmentsIdx);
    expect(attachmentsIdx).toBeLessThan(servicePhase);
    expect(servicePhase).toBeLessThan(commentsIdx);
    expect(commentsIdx).toBeLessThan(artifactsIdx);
    expect(artifactsIdx).toBeLessThan(historyPhase);
    expect(historyPhase).toBeLessThan(timelineIdx);

    expect(attachments).toMatch(/Documentos da solicitação/);
    expect(attachments).toMatch(/MyRequestsAttachmentPreviewStrip/);
    expect(attachments).toMatch(/RequestFilePreviewModal/);
    expect(attachments).toMatch(/Salvar documentos/);
    expect(attachments).toMatch(/Pendentes de envio/);
    expect(attachments).not.toMatch(/window\.open/);
    expect(attachments).not.toMatch(/attachmentDownloadUrl/);
    expect(artifacts).toMatch(/Documentos gerados no atendimento/);
    expect(artifacts).toMatch(/MyRequestsAttachmentPreviewStrip/);
    expect(artifacts).toMatch(/Tipo de documento/);
    expect(artifacts).toMatch(/RequestFilePreviewModal/);
    expect(artifacts).toMatch(/Salvar documentos/);
    expect(artifacts).not.toMatch(/window\.open/);
    expect(artifacts).not.toMatch(/artifactDownloadUrl/);
  });

  it("abre arquivo em modal autenticado e não faz upload imediato no detalhe", () => {
    const preview = read("components/RequestFilePreviewModal.tsx");
    const attachments = read("components/AttachmentsPanel.tsx");
    const artifacts = read("components/ArtifactsPanel.tsx");
    const staged = read("components/StagedAttachmentsField.tsx");

    expect(preview).toMatch(/FilePreviewModal/);
    expect(preview).toMatch(/downloadAttachmentBlob/);
    expect(preview).toMatch(/downloadArtifactBlob/);
    expect(preview).toMatch(/Baixar/);
    expect(preview).not.toMatch(/window\.open/);

    expect(attachments).toMatch(/stageFiles/);
    expect(attachments).toMatch(/onSavePending/);
    expect(attachments).not.toMatch(
      /onFilesSelected[\s\S]{0,200}uploadAttachment/,
    );
    expect(artifacts).toMatch(/stageFiles/);
    expect(artifacts).toMatch(/onSavePending/);
    expect(artifacts).not.toMatch(
      /onFilesSelected[\s\S]{0,200}uploadArtifact/,
    );
    expect(staged).toMatch(/RequestFilePreviewModal/);
    expect(staged).not.toMatch(/window\.open/);
  });

  it("abre edição real e destaca motivo da devolução", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const editPage = read("pages/RequestEditPage.tsx");
    expect(page).toMatch(/myRequestsEditPath/);
    expect(page).toMatch(/Corrigir dados/);
    expect(page).toMatch(/Motivo da devolução/);
    expect(page).not.toMatch(/Ajuste os dados quando a solicitação estiver aguardando/);
    expect(editPage).toMatch(/mode="edit"/);
  });

  it("liga hints nos labels do resumo e payload", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const payload = read("features/invoice-issuance/ui/InvoiceIssuancePayloadPanel.tsx");
    expect(page).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.type/);
    expect(page).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.status/);
    expect(page).toMatch(/detail\.returnReason/);
    expect(payload).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.party/);
  });

  it("não chama transição para view e usa avisos flutuantes", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const actionBar = read("components/ActionBar.tsx");
    const app = read("App.tsx");
    expect(actionBar).toMatch(/filterDetailBarActions/);
    expect(page).toMatch(/isTransitionAction/);
    expect(page).toMatch(/useMyRequestsFloatingNotice/);
    expect(page).toMatch(/notifyError/);
    expect(app).toMatch(/MyRequestsFloatingNoticeProvider/);
    expect(app).toMatch(/RequestEditPage/);
  });
});
