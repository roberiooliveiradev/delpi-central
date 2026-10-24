import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listDocumentsMock = vi.fn();
const uploadDocumentMock = vi.fn();
const downloadDocumentMock = vi.fn();
const saveBlobMock = vi.fn();
const replaceDocumentMock = vi.fn();
const listVersionsMock = vi.fn();
const cancelDocumentMock = vi.fn();
const listEventsMock = vi.fn();

vi.mock("../../api/documentsApi", () => ({
  CLOSING_DOCUMENT_ACCEPT: ".pdf",
  listClosingDocuments: (...args: unknown[]) =>
    listDocumentsMock(...args),
  uploadClosingDocument: (...args: unknown[]) =>
    uploadDocumentMock(...args),
  downloadClosingDocument: (...args: unknown[]) =>
    downloadDocumentMock(...args),
  saveDocumentBlob: (...args: unknown[]) => saveBlobMock(...args),
  replaceClosingDocument: (...args: unknown[]) =>
    replaceDocumentMock(...args),
  listDocumentVersions: (...args: unknown[]) =>
    listVersionsMock(...args),
  cancelClosingDocument: (...args: unknown[]) =>
    cancelDocumentMock(...args),
  listDocumentEvents: (...args: unknown[]) =>
    listEventsMock(...args),
}));

const decideEvidenceMock = vi.fn();
vi.mock("../../api/competencesApi", () => ({
  decideDocumentEvidence: (...args: unknown[]) =>
    decideEvidenceMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { ClosingDocumentsPanel } from "./ClosingDocumentsPanel";

const DOC = {
  document_id: "d-1",
  competence_id: "c-1",
  link_kind: "competence_item",
  snapshot_item_id: "s-1",
  snapshot_item_key: "CK-E-01",
  title: "Extrato",
  attachment_role: "generic",
  state: "ATTACHED",
  current_version_no: 1,
  revision: 3,
  uploaded_by: "u-1",
  created_at: "2026-05-02T10:00:00Z",
  updated_at: "2026-05-02T10:00:00Z",
  original_name: "extrato.pdf",
  mime_type: "application/pdf",
  size_bytes: 2048,
  checksum_sha256: "a".repeat(64),
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ClosingDocumentsPanel", () => {
  it("lista evidências da competência e oferece download", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    downloadDocumentMock.mockResolvedValue(new Blob(["pdf"]));

    render(<ClosingDocumentsPanel period="2026-05" />);

    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );
    expect(listDocumentsMock).toHaveBeenCalledWith(
      "2026-05",
      {},
      expect.objectContaining({ signal: expect.anything() }),
    );

    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(downloadDocumentMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        1,
      ),
    );
  });

  it("falha de download exibe feedback acessível e permite recuperação", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    downloadDocumentMock
      .mockRejectedValueOnce(
        new ApiError(404, "Not found", "document_not_found"),
      )
      .mockResolvedValueOnce(new Blob(["pdf"]));

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(screen.getByText("Falha no download")).toBeTruthy(),
    );
    expect(
      screen.getByText(/não encontrado ou fora do escopo/),
    ).toBeTruthy();
    expect(saveBlobMock).not.toHaveBeenCalled();

    // Recuperação: retry no banner baixa com sucesso e limpa o erro.
    fireEvent.click(screen.getByText("Tentar novamente"));
    await waitFor(() =>
      expect(saveBlobMock).toHaveBeenCalledTimes(1),
    );
    await waitFor(() =>
      expect(screen.queryByText("Falha no download")).toBeNull(),
    );
  });

  it("download sem autorização distingue a causa no feedback", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    downloadDocumentMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(
        screen.getByText(/não tem autorização para baixar/),
      ).toBeTruthy(),
    );
  });

  it("erro de rede no download orienta nova tentativa", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    downloadDocumentMock.mockRejectedValue(new TypeError("fetch failed"));

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(
        screen.getByText(/Falha de comunicação ao baixar/),
      ).toBeTruthy(),
    );
  });

  it("arquivo indisponível no download informa indisponibilidade", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    downloadDocumentMock.mockRejectedValue(
      new ApiError(503, "Unavailable", "file_missing"),
    );

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(
        screen.getByText(/não está disponível no armazenamento/),
      ).toBeTruthy(),
    );
  });

  it("exibe estado vazio sem inventar evidências", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    render(
      <ClosingDocumentsPanel period="2026-05" snapshotItemId="s-1" />,
    );

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma evidência anexada/),
      ).toBeTruthy(),
    );
    expect(listDocumentsMock).toHaveBeenCalledWith(
      "2026-05",
      { snapshotItemId: "s-1" },
      expect.anything(),
    );
  });

  it("upload envia a chave de idempotência e recarrega a lista", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    uploadDocumentMock.mockResolvedValue(DOC);

    render(
      <ClosingDocumentsPanel period="2026-05" snapshotItemId="s-1" />,
    );
    fireEvent.click(
      screen.getByLabelText("Enviar evidência documental"),
    );

    await waitFor(() => expect(uploadDocumentMock).toHaveBeenCalled());
    const [period, input] = uploadDocumentMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(input.snapshotItemId).toBe("s-1");
    expect(input.idempotencyKey).toBeTruthy();
    // Recarregou a listagem após anexar.
    await waitFor(() =>
      expect(listDocumentsMock.mock.calls.length).toBeGreaterThan(1),
    );
  });

  it("erro de validação oferece retry com a mesma chave (D-U7)", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    uploadDocumentMock
      .mockRejectedValueOnce(
        new ApiError(
          422,
          "Formato não permitido. Use PDF, imagem, XLS, XLSX ou CSV.",
          "unsupported_media_type",
        ),
      )
      .mockResolvedValueOnce(DOC);

    render(<ClosingDocumentsPanel period="2026-05" />);
    fireEvent.click(
      screen.getByLabelText("Enviar evidência documental"),
    );

    await waitFor(() =>
      expect(screen.getByText("Falha no envio")).toBeTruthy(),
    );
    const firstKey = uploadDocumentMock.mock.calls[0][1].idempotencyKey;

    fireEvent.click(screen.getByText("Tentar novamente"));
    await waitFor(() =>
      expect(uploadDocumentMock.mock.calls.length).toBe(2),
    );
    expect(uploadDocumentMock.mock.calls[1][1].idempotencyKey).toBe(
      firstKey,
    );
  });

  it("falha de listagem não expõe dropzone habilitada para upload", async () => {
    listDocumentsMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );

    render(<ClosingDocumentsPanel period="2026-05" />);

    await waitFor(() =>
      expect(screen.getByText("Acesso restrito")).toBeTruthy(),
    );
    const dropzone = screen.getByLabelText(
      "Enviar evidência documental",
    ) as HTMLButtonElement;
    expect(dropzone.disabled).toBe(true);
  });

  it("substituir envia a revisão vista e recarrega a lista", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    replaceDocumentMock.mockResolvedValue({
      ...DOC,
      current_version_no: 2,
      revision: 4,
    });

    const { container } = render(
      <ClosingDocumentsPanel period="2026-05" />,
    );
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Substituir"));
    const input = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    expect(input).toBeTruthy();
    fireEvent.change(input, {
      target: {
        files: [
          new File(["%PDF-1.4 novo"], "extrato-v2.pdf", {
            type: "application/pdf",
          }),
        ],
      },
    });

    await waitFor(() => expect(replaceDocumentMock).toHaveBeenCalled());
    const [period, documentId, payload] = replaceDocumentMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(documentId).toBe("d-1");
    expect(payload.revision).toBe(3);
    expect(payload.file.name).toBe("extrato-v2.pdf");
    expect(typeof payload.idempotencyKey).toBe("string");
    await waitFor(() =>
      expect(listDocumentsMock.mock.calls.length).toBeGreaterThan(1),
    );
  });

  it("retry da substituição reutiliza a mesma idempotency_key", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    replaceDocumentMock
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce({ ...DOC, current_version_no: 2 });

    const { container } = render(
      <ClosingDocumentsPanel period="2026-05" />,
    );
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Substituir"));
    const input = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [
          new File(["%PDF-1.4 novo"], "v2.pdf", {
            type: "application/pdf",
          }),
        ],
      },
    });

    await waitFor(() =>
      expect(screen.getByText("Falha ao substituir o arquivo.")).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Tentar novamente" }),
    );

    await waitFor(() =>
      expect(replaceDocumentMock.mock.calls.length).toBe(2),
    );
    const first = replaceDocumentMock.mock.calls[0][2];
    const second = replaceDocumentMock.mock.calls[1][2];
    expect(second.idempotencyKey).toBe(first.idempotencyKey);
  });

  it("revisão obsoleta na substituição informa e atualiza a lista", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    replaceDocumentMock.mockRejectedValue(
      new ApiError(409, "Conflict", "stale_revision"),
    );

    const { container } = render(
      <ClosingDocumentsPanel period="2026-05" />,
    );
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Substituir"));
    const input = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["x"], "novo.pdf", { type: "application/pdf" })],
      },
    });

    await waitFor(() =>
      expect(
        screen.getByText(/foi alterado por outra pessoa/),
      ).toBeTruthy(),
    );
    await waitFor(() =>
      expect(listDocumentsMock.mock.calls.length).toBeGreaterThan(1),
    );
  });

  it("substituição negada informa a regra de posse", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    replaceDocumentMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );

    const { container } = render(
      <ClosingDocumentsPanel period="2026-05" />,
    );
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Substituir"));
    fireEvent.change(
      container.querySelector('input[type="file"]') as HTMLInputElement,
      {
        target: {
          files: [new File(["x"], "novo.pdf", { type: "application/pdf" })],
        },
      },
    );

    await waitFor(() =>
      expect(
        screen.getByText(/Somente quem anexou/),
      ).toBeTruthy(),
    );
  });

  it("cancelar exige confirmação e envia a revisão", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    cancelDocumentMock.mockResolvedValue({
      ...DOC,
      state: "CANCELLED",
      revision: 4,
    });

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Cancelar"));
    await waitFor(() =>
      expect(
        screen.getByText(/O documento sai da lista/),
      ).toBeTruthy(),
    );
    expect(cancelDocumentMock).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", { name: "Cancelar documento" }),
    );
    await waitFor(() =>
      expect(cancelDocumentMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        { revision: 3 },
      ),
    );
    await waitFor(() =>
      expect(listDocumentsMock.mock.calls.length).toBeGreaterThan(1),
    );
  });

  it("versões lista o histórico e baixa versão anterior", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [{ ...DOC, current_version_no: 2 }],
      total: 1,
      limit: 50,
      offset: 0,
    });
    listVersionsMock.mockResolvedValue([
      {
        document_version_id: "v-2",
        document_id: "d-1",
        version_no: 2,
        state: "ATTACHED",
        uploaded_by: "u-1",
        created_at: "2026-05-10T10:00:00Z",
        original_name: "extrato-v2.pdf",
        mime_type: "application/pdf",
        size_bytes: 3000,
        checksum_sha256: "b".repeat(64),
      },
      {
        document_version_id: "v-1",
        document_id: "d-1",
        version_no: 1,
        state: "SUPERSEDED",
        uploaded_by: "u-1",
        created_at: "2026-05-02T10:00:00Z",
        original_name: "extrato.pdf",
        mime_type: "application/pdf",
        size_bytes: 2048,
        checksum_sha256: "a".repeat(64),
      },
    ]);
    downloadDocumentMock.mockResolvedValue(new Blob(["pdf"]));

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Versões"));
    await waitFor(() =>
      expect(screen.getByText(/v1 · Substituída/)).toBeTruthy(),
    );
    expect(screen.getByText(/v2 · Atual/)).toBeTruthy();
    expect(listVersionsMock).toHaveBeenCalledWith("2026-05", "d-1");

    // Baixar a versão anterior segue o mesmo U4 com version_no.
    // Ordem dos «Baixar»: item da lista, depois v2 e v1 no diálogo.
    fireEvent.click(screen.getAllByText("Baixar")[2]);
    await waitFor(() =>
      expect(downloadDocumentMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        1,
      ),
    );
  });

  it("eventos lista a auditoria do documento", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    listEventsMock.mockResolvedValue({
      events: [
        {
          event_id: "e-2",
          event_type: "DOCUMENT_DOWNLOADED",
          actor_subject: "u-1",
          detail: { version_no: 1, result: "AUTHORIZED" },
          created_at: "2026-05-03T10:00:00Z",
        },
        {
          event_id: "e-1",
          event_type: "DOCUMENT_UPLOADED",
          actor_subject: "u-1",
          detail: { original_name: "extrato.pdf" },
          created_at: "2026-05-02T10:00:00Z",
        },
      ],
      total: 2,
      limit: 50,
      offset: 0,
    });

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Eventos"));
    await waitFor(() =>
      expect(screen.getByText("Documento anexado")).toBeTruthy(),
    );
    expect(screen.getByText(/Download/)).toBeTruthy();
    expect(listEventsMock).toHaveBeenCalledWith("2026-05", "d-1");
  });

  it("valida evidência de competência (sem item) com aceite", async () => {
    const competenceDoc = { ...DOC, snapshot_item_id: null };
    listDocumentsMock.mockResolvedValue({
      documents: [competenceDoc],
      total: 1,
      limit: 50,
      offset: 0,
    });
    decideEvidenceMock.mockResolvedValue({});

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Aceitar"));
    await waitFor(() =>
      expect(decideEvidenceMock).toHaveBeenCalledWith("2026-05", "d-1", {
        decision: "ACCEPTED",
      }),
    );
  });

  it("rejeita evidência de competência com motivo estruturado", async () => {
    const competenceDoc = { ...DOC, snapshot_item_id: null };
    listDocumentsMock.mockResolvedValue({
      documents: [competenceDoc],
      total: 1,
      limit: 50,
      offset: 0,
    });
    decideEvidenceMock.mockResolvedValue({});

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    fireEvent.click(screen.getByText("Rejeitar"));
    fireEvent.change(screen.getByLabelText(/Motivo da rejeição/), {
      target: { value: "WRONG_COMPETENCE" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar rejeição" }),
    );

    await waitFor(() =>
      expect(decideEvidenceMock).toHaveBeenCalledWith("2026-05", "d-1", {
        decision: "REJECTED",
        reason_code: "WRONG_COMPETENCE",
      }),
    );
  });

  it("não oferece decisão em documento vinculado a item", async () => {
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });

    render(<ClosingDocumentsPanel period="2026-05" />);
    await waitFor(() =>
      expect(screen.getByText("extrato.pdf")).toBeTruthy(),
    );

    expect(screen.queryByText("Aceitar")).toBeNull();
    expect(screen.queryByText("Rejeitar")).toBeNull();
  });
});
