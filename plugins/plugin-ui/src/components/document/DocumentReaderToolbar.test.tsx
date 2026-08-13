import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { __resetScopedPrintForTests } from "../../export/pdf/printOnce";
import { DocumentReaderToolbar } from "./DocumentReaderToolbar";

afterEach(() => {
  cleanup();
  document.body.classList.remove("delpi-ui-document-printing");
  __resetScopedPrintForTests();
  vi.restoreAllMocks();
});

describe("DocumentReaderToolbar", () => {
  it("dispara impressão canônica", () => {
    const print = vi.spyOn(window, "print").mockImplementation(() => {});
    render(<DocumentReaderToolbar />);
    fireEvent.click(screen.getByTestId("document-reader-print"));
    expect(print).toHaveBeenCalledOnce();
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(true);
  });

  it("baixa PDF via callback autenticado", async () => {
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
