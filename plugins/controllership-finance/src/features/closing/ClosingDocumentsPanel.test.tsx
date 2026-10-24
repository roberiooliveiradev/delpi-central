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

vi.mock("../../api/documentsApi", () => ({
  CLOSING_DOCUMENT_ACCEPT: ".pdf",
  listClosingDocuments: (...args: unknown[]) =>
    listDocumentsMock(...args),
  uploadClosingDocument: (...args: unknown[]) =>
    uploadDocumentMock(...args),
  downloadClosingDocument: (...args: unknown[]) =>
    downloadDocumentMock(...args),
  saveDocumentBlob: (...args: unknown[]) => saveBlobMock(...args),
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
});
