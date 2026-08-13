// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../export/pdf/delpiDocumentPrint", () => ({
  printDelpiDocumentHtml: vi.fn(() => true),
}));

import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";
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
    vi.mocked(printDelpiDocumentHtml).mockClear().mockReturnValue(true);
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

  it("imprime via printDelpiDocumentHtml (iframe oculto no host)", () => {
    render(
      <DocumentReader>
        <DocumentPage>
          <p>Corpo da ata</p>
        </DocumentPage>
      </DocumentReader>,
    );

    expect(printDocumentReader({ title: "Ata formal" })).toBe(true);
    expect(printDelpiDocumentHtml).toHaveBeenCalled();
    const html = String(vi.mocked(printDelpiDocumentHtml).mock.calls[0]?.[0] ?? "");
    expect(html).toContain("Corpo da ata");
    expect(html).toContain("delpi-ui-document-page");
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(false);
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
    expect(css).toMatch(/@page\s*\{[\s\S]*?size:\s*A4 portrait/);
    expect(css).toMatch(/@page\s*\{[\s\S]*?margin:\s*0/);
    expect(css).toMatch(/text-align:\s*justify/);
    expect(css).toMatch(/break-after:\s*avoid-page/);
  });
});
