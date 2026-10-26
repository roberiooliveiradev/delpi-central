import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getItemMock = vi.fn();
const getValidationMock = vi.fn();
const listDocsMock = vi.fn();
const getDocMock = vi.fn();
const listVersionsMock = vi.fn();
const listEventsMock = vi.fn();
const downloadMock = vi.fn();
const saveBlobMock = vi.fn();
const uploadMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("../../api/competencesApi", () => ({
  getCompetenceItem: (...args: unknown[]) => getItemMock(...args),
  getItemValidation: (...args: unknown[]) => getValidationMock(...args),
}));

vi.mock("../../api/documentsApi", () => ({
  CLOSING_DOCUMENT_ACCEPT: ".pdf",
  listClosingDocuments: (...args: unknown[]) => listDocsMock(...args),
  getClosingDocument: (...args: unknown[]) => getDocMock(...args),
  listDocumentVersions: (...args: unknown[]) => listVersionsMock(...args),
  listDocumentEvents: (...args: unknown[]) => listEventsMock(...args),
  downloadClosingDocument: (...args: unknown[]) => downloadMock(...args),
  saveDocumentBlob: (...args: unknown[]) => saveBlobMock(...args),
  uploadClosingDocument: (...args: unknown[]) => uploadMock(...args),
  replaceClosingDocument: (...args: unknown[]) => replaceMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { DocumentDetailPanel } from "./DocumentDetailPanel";

const ITEM = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  sort_order: 1,
  sheet: "ELETRONICO",
  name: "Balancete mensal",
  origin_kind: "TOTVS",
  recipient_area: "CONTABIL",
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  totvs_report_ref: null,
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  exceptional: false,
  revision: 1,
  state_reason: null,
  purpose: null,
  requirement_notes: null,
  source_template_item_id: null,
  source_version_id: null,
};

const DOC = {
  document_id: "d-1",
  competence_id: "c-1",
  link_kind: "competence_item",
  snapshot_item_id: "s-1",
  snapshot_item_key: "CK-E-01",
  title: "Balancete mensal",
  attachment_role: "generic",
  state: "ATTACHED",
  current_version_no: 1,
  revision: 3,
  uploaded_by: "u-1",
  created_at: "2026-05-02T10:00:00Z",
  updated_at: "2026-05-02T10:00:00Z",
  original_name: "balancete.pdf",
  mime_type: "application/pdf",
  size_bytes: 2048,
  checksum_sha256: "a".repeat(64),
};

const VALIDATION = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  applicability: "REQUIRED",
  documents: [],
  decisions: [],
};

function renderDetail(documentRef: string, extras?: {
  onBack?: () => void;
  onOpenRef?: (ref: string) => void;
}) {
  return render(
    <DocumentDetailPanel
      period="2026-05"
      documentRef={documentRef}
      onBack={extras?.onBack ?? (() => {})}
      onOpenRef={extras?.onOpenRef ?? (() => {})}
    />,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DocumentDetailPanel — item exigido", () => {
  it("abre o detalhe pelo item com decisões reais e histórico", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue({
      ...VALIDATION,
      decisions: [
        {
          decision_id: "dec-1",
          document_id: "d-1",
          scope: "PER_ATTACHMENT",
          composition: [],
          decision: "REJECTED",
          reason_code: "ILLEGIBLE",
          comment: "Arquivo ilegível.",
          result_state: "UNDER_REVIEW",
          reverses_decision_id: null,
          decided_by: "revisor-1",
          created_at: "2026-05-11T10:00:00Z",
        },
      ],
    });
    listVersionsMock.mockResolvedValue([
      {
        document_version_id: "v-1",
        document_id: "d-1",
        version_no: 1,
        state: "ATTACHED",
        uploaded_by: "u-1",
        created_at: "2026-05-02T10:00:00Z",
        original_name: "balancete.pdf",
        mime_type: "application/pdf",
        size_bytes: 2048,
        checksum_sha256: "a".repeat(64),
      },
    ]);
    listEventsMock.mockResolvedValue({
      events: [
        {
          event_id: "e-1",
          event_type: "DOCUMENT_UPLOADED",
          actor_subject: "u-1",
          detail: { version_no: 1 },
          created_at: "2026-05-02T10:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });

    renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText("Balancete mensal")).toBeTruthy(),
    );
    expect(getItemMock).toHaveBeenCalledWith(
      "2026-05",
      "CK-E-01",
      expect.anything(),
    );
    expect(listDocsMock).toHaveBeenCalledWith(
      "2026-05",
      { snapshotItemId: "s-1" },
      expect.anything(),
    );
    await waitFor(() =>
      expect(screen.getByText(/Ajuste solicitado/)).toBeTruthy(),
    );
    expect(screen.getByText(/Arquivo ilegível/)).toBeTruthy();
    expect(screen.getByText(/revisor-1/)).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText(/Arquivo anexado/)).toBeTruthy(),
    );
    expect(screen.getByTestId("file-preview")).toBeTruthy();
  });

  it("item sem arquivo mostra dropzone e envia anexo contextual", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(VALIDATION);
    uploadMock.mockResolvedValue(DOC);

    renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText(/Nenhum arquivo anexado ainda/)).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByLabelText("Anexar arquivo ao documento"),
    );
    await waitFor(() => expect(uploadMock).toHaveBeenCalled());
    const [period, payload] = uploadMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(payload.snapshotItemId).toBe("s-1");
    expect(payload.title).toBe("Balancete mensal");
    expect(payload.idempotencyKey).toBeTruthy();
  });

  it("download e nova versão preservam revisão e idempotência", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(VALIDATION);
    listVersionsMock.mockResolvedValue([]);
    listEventsMock.mockResolvedValue({
      events: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    downloadMock.mockResolvedValue(new Blob(["pdf"]));
    replaceMock.mockResolvedValue({ ...DOC, current_version_no: 2 });

    const { container } = renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText("Baixar")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledWith("2026-05", "d-1", 1),
    );

    fireEvent.click(screen.getByText("Enviar nova versão"));
    fireEvent.change(
      container.querySelector('input[type="file"]') as HTMLInputElement,
      {
        target: {
          files: [new File(["x"], "v2.pdf", { type: "application/pdf" })],
        },
      },
    );
    await waitFor(() => expect(replaceMock).toHaveBeenCalled());
    const [, documentId, payload] = replaceMock.mock.calls[0];
    expect(documentId).toBe("d-1");
    expect(payload.revision).toBe(3);
    expect(payload.idempotencyKey).toBeTruthy();
  });
});

describe("DocumentDetailPanel — documento adicional", () => {
  it("abre pelo id com prévia, interações honestas e histórico", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });
    listVersionsMock.mockResolvedValue([]);
    listEventsMock.mockResolvedValue({
      events: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    renderDetail("d-1");

    await waitFor(() =>
      expect(screen.getByTestId("file-preview")).toBeTruthy(),
    );
    expect(getDocMock).toHaveBeenCalledWith(
      "2026-05",
      "d-1",
      expect.anything(),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma solicitação registrada/),
      ).toBeTruthy(),
    );
    expect(
      screen.getByText(/conversa livre por documento ainda não está disponível/),
    ).toBeTruthy();
  });
});

describe("DocumentDetailPanel — novo documento adicional", () => {
  it("anexa sem exigência e navega ao documento criado", async () => {
    uploadMock.mockResolvedValue({ ...DOC, document_id: "d-9" });
    const onOpenRef = vi.fn();

    renderDetail("new", { onOpenRef });

    fireEvent.change(screen.getByLabelText("Nome do documento"), {
      target: { value: "Comprovante extra" },
    });
    fireEvent.click(
      screen.getByLabelText("Anexar documento adicional"),
    );

    await waitFor(() => expect(uploadMock).toHaveBeenCalled());
    const [period, payload] = uploadMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(payload.snapshotItemId).toBeNull();
    expect(payload.title).toBe("Comprovante extra");
    await waitFor(() =>
      expect(onOpenRef).toHaveBeenCalledWith("d-9"),
    );
  });
});

describe("DocumentDetailPanel — estados honestos", () => {
  it("documento inexistente exibe erro sem inventar conteúdo", async () => {
    getDocMock.mockRejectedValue(
      new ApiError(404, "Not found", "document_not_found"),
    );

    renderDetail("d-404");

    await waitFor(() =>
      expect(
        screen.getByText(/não encontrado ou fora do escopo/),
      ).toBeTruthy(),
    );
  });

  it("voltar chama o retorno contextual", async () => {
    getDocMock.mockResolvedValue(DOC);
    const onBack = vi.fn();

    renderDetail("d-1", { onBack });

    fireEvent.click(screen.getByText(/Voltar aos documentos/));
    expect(onBack).toHaveBeenCalled();
  });
});
