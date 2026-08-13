import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentPage, DocumentReader } from "./DocumentReader";
import { DocumentReaderToolbar } from "./DocumentReaderToolbar";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

function mockPrintWindow() {
  const print = vi.fn();
  const fakeDoc = {
    open: vi.fn(),
    write: vi.fn(),
    close: vi.fn(),
    images: [] as unknown as HTMLCollectionOf<HTMLImageElement>,
  };
  const fakeWindow = {
    closed: false,
    focus: vi.fn(),
    scrollTo: vi.fn(),
    print,
    document: fakeDoc,
    addEventListener: vi.fn(),
  } as unknown as Window;
  vi.spyOn(window, "open").mockReturnValue(fakeWindow);
  return { print, fakeDoc };
}

describe("DocumentReaderToolbar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("Imprimir e Baixar PDF usam a prévia (janela dedicada)", () => {
    const { print, fakeDoc } = mockPrintWindow();

    render(
      <DocumentReader toolbar={<DocumentReaderToolbar printTitle="Ata" />}>
        <DocumentPage>
          <p>Conteúdo da prévia</p>
        </DocumentPage>
      </DocumentReader>,
    );

    fireEvent.click(screen.getByTestId("document-reader-download-pdf"));
    expect(fakeDoc.write).toHaveBeenCalled();
    expect(String(fakeDoc.write.mock.calls[0]?.[0] ?? "")).toContain("Conteúdo da prévia");

    fireEvent.click(screen.getByTestId("document-reader-print"));
    expect(fakeDoc.write.mock.calls.length).toBeGreaterThanOrEqual(2);

    vi.advanceTimersByTime(1_500);
    expect(print).toHaveBeenCalled();
  });

  it("honra onDownloadPdf quando informado (override servidor)", async () => {
    vi.useRealTimers();
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
