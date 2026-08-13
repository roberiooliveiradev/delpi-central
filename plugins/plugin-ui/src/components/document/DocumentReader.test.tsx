// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("DocumentReader", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

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

  it("imprime via janela dedicada (printDelpiDocumentHtml)", () => {
    render(
      <DocumentReader>
        <DocumentPage>
          <p>Corpo da ata</p>
        </DocumentPage>
      </DocumentReader>,
    );

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

    expect(printDocumentReader({ title: "Ata formal" })).toBe(true);
    expect(fakeDoc.write).toHaveBeenCalled();
    const written = String(fakeDoc.write.mock.calls[0]?.[0] ?? "");
    expect(written).toContain("Corpo da ata");
    expect(written).toContain("delpi-ui-document-page");
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(false);

    vi.advanceTimersByTime(1_500);
    expect(print).toHaveBeenCalledTimes(1);
  });

  it("CSS de leitura mantém tabelas como grade e print multipágina sem clip", () => {
    const css = readFileSync(
      resolve(dirname(fileURLToPath(import.meta.url)), "../../styles/document-reader.css"),
      "utf8",
    );
    expect(css).toMatch(
      /\.delpi-ui-document-rich-content table \{[\s\S]*?display:\s*table/,
    );
    expect(css).toMatch(
      /\.delpi-ui-document-rich-content th,\s*\n\.delpi-ui-document-rich-content td \{[\s\S]*?display:\s*table-cell/,
    );
    expect(css).toMatch(/\.delpi-ui-document-page \{[\s\S]*?overflow:\s*visible/);
  });
});
