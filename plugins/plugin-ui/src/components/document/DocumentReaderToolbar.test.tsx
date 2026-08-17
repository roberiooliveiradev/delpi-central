import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../export/pdf/delpiDocumentPrint", () => ({
  printDelpiDocumentHtml: vi.fn(() => true),
}));

import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";
import { DocumentPage, DocumentReader } from "./DocumentReader";
import { DocumentReaderToolbar } from "./DocumentReaderToolbar";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("DocumentReaderToolbar", () => {
  beforeEach(() => {
    vi.mocked(printDelpiDocumentHtml).mockClear().mockReturnValue(true);
  });

  it("Imprimir e Baixar PDF usam a prévia (mesmo HTML)", () => {
    render(
      <DocumentReader toolbar={<DocumentReaderToolbar printTitle="Ata" />}>
        <DocumentPage>
          <p>Conteúdo da prévia</p>
        </DocumentPage>
      </DocumentReader>,
    );

    fireEvent.click(screen.getByTestId("document-reader-download-pdf"));
    expect(printDelpiDocumentHtml).toHaveBeenCalled();
    expect(String(vi.mocked(printDelpiDocumentHtml).mock.calls[0]?.[0] ?? "")).toContain(
      "Conteúdo da prévia",
    );

    fireEvent.click(screen.getByTestId("document-reader-print"));
    expect(vi.mocked(printDelpiDocumentHtml).mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("honra onDownloadPdf quando informado (override servidor)", async () => {
    const onDownloadPdf = vi.fn(async () => undefined);
    render(<DocumentReaderToolbar onDownloadPdf={onDownloadPdf} />);
    fireEvent.click(screen.getByTestId("document-reader-download-pdf"));
    await waitFor(() => {
      expect(onDownloadPdf).toHaveBeenCalledOnce();
    });
  });

  it("pode ocultar Baixar PDF", () => {
    render(<DocumentReaderToolbar showDownloadPdf={false} />);
    expect(screen.queryByTestId("document-reader-download-pdf")).toBeNull();
  });
});
