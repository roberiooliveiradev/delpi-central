// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { __resetScopedPrintForTests } from "../../export/pdf/printOnce";
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
  __resetScopedPrintForTests();
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

  it("ativa o escopo de impressão do documento uma única vez", () => {
    const print = vi.spyOn(window, "print").mockImplementation(() => {});

    expect(printDocumentReader()).toBe(true);
    expect(printDocumentReader()).toBe(false);

    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(true);
    expect(print).toHaveBeenCalledOnce();

    window.dispatchEvent(new Event("afterprint"));
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(false);
  });

  it("CSS de leitura mantém tabelas como grade (não colapsa em texto)", () => {
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
  });
});
