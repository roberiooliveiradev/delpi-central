import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentPage, DocumentReader } from "./DocumentReader";
import { DocumentReaderToolbar } from "./DocumentReaderToolbar";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("DocumentReaderToolbar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("dispara impressão em janela dedicada", () => {
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

    render(
      <DocumentReader toolbar={<DocumentReaderToolbar />}>
        <DocumentPage>
          <p>Ata</p>
        </DocumentPage>
      </DocumentReader>,
    );
    fireEvent.click(screen.getByTestId("document-reader-print"));
    expect(fakeDoc.write).toHaveBeenCalled();
    vi.advanceTimersByTime(1_500);
    expect(print).toHaveBeenCalledOnce();
  });

  it("baixa PDF via callback autenticado", async () => {
    vi.useRealTimers();
    const onDownloadPdf = vi.fn(async () => undefined);
    render(<DocumentReaderToolbar onDownloadPdf={onDownloadPdf} />);
    fireEvent.click(screen.getByTestId("document-reader-download-pdf"));
    await waitFor(() => {
      expect(onDownloadPdf).toHaveBeenCalledOnce();
    });
  });

  it("omite Baixar PDF sem onDownloadPdf", () => {
    render(<DocumentReaderToolbar />);
    expect(screen.queryByTestId("document-reader-download-pdf")).toBeNull();
  });
});
