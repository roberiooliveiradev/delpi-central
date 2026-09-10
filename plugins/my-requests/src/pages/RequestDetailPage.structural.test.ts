import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("RequestDetailPage structural", () => {
  it("renderiza progresso da API e não hardcodifica percentual por status", () => {
    const page = read("pages/RequestDetailPage.tsx");
    expect(page).toMatch(/journey_progress/);
    expect(page).toMatch(/MyRequestsProgressTracker/);
    expect(page).toMatch(/MyRequestsJourneyProgressBar/);
    expect(page).toMatch(/mapJourneyStagesToTrackerSteps/);
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

  it("usa layout denso e copy de documentos", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const attachments = read("components/AttachmentsPanel.tsx");
    const artifacts = read("components/ArtifactsPanel.tsx");
    const css = read("index.css");
    expect(page).toMatch(/my-requests-detail-split/);
    expect(page).toMatch(/my-requests-detail-history/);
    expect(page).toMatch(/my-requests-detail-docs/);
    expect(css).toMatch(/my-requests-detail-split/);
    expect(attachments).toMatch(/Documentos da solicitação/);
    expect(artifacts).toMatch(/Documentos gerados no atendimento/);
    expect(attachments).toMatch(/canUpload/);
    expect(artifacts).toMatch(/Tipo de documento/);
  });

  it("liga hints nos labels do resumo e payload", () => {
    const page = read("pages/RequestDetailPage.tsx");
    const payload = read("features/invoice-issuance/ui/InvoiceIssuancePayloadPanel.tsx");
    expect(page).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.type/);
    expect(page).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.status/);
    expect(payload).toMatch(/hint:\s*MY_REQUESTS_HELP_TOOLTIPS\.detail\.party/);
  });
});
