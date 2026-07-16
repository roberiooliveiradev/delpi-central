// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DocumentFooter,
  DocumentHeader,
  DocumentPage,
  DocumentReader,
  DocumentSignatureBlock,
  printDocumentReader,
} from "./DocumentReader";

afterEach(() => {
  cleanup();
  document.body.classList.remove("delpi-ui-document-printing");
  vi.restoreAllMocks();
});

describe("DocumentReader", () => {
  it("compõe papel A4 com slots institucionais e assinatura", () => {
    render(
      <DocumentReader toolbar={<button>Baixar</button>}>
        <DocumentPage
          header={<DocumentHeader title="Ata formal" subtitle="Segurança" logo={<span>Logo</span>} />}
          watermark={<span>Marca</span>}
          footer={<DocumentFooter left="Data" center="DELPI" right="1" />}
        >
          <p>Conteúdo</p>
          <DocumentSignatureBlock name="Pessoa" role="Presidente" status="Assinado" />
        </DocumentPage>
      </DocumentReader>,
    );

    expect(screen.getByLabelText("Leitura do documento")).toBeTruthy();
    expect(screen.getByText("Ata formal")).toBeTruthy();
    expect(screen.getByText("Pessoa")).toBeTruthy();
    expect(screen.getByText("Baixar")).toBeTruthy();
  });

  it("ativa o escopo de impressão do documento", () => {
    vi.useFakeTimers();
    const print = vi.spyOn(window, "print").mockImplementation(() => {});

    printDocumentReader();

    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(true);
    expect(print).toHaveBeenCalledOnce();
    vi.runAllTimers();
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(false);
    vi.useRealTimers();
  });
});
