import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  buildDocumentReaderPrintHtml,
  collectPrintScopeClasses,
  downloadDocumentReaderPdf,
  findActiveDocumentPage,
  printDocumentReaderInWindow,
} from "./printDocumentReaderHtml";

describe("printDocumentReaderHtml", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("serializa o papel com estilos e CSS multipágina", () => {
    document.head.insertAdjacentHTML(
      "beforeend",
      `<style id="doc-test-style">.tm-x{color:red}</style>`,
    );
    document.body.innerHTML = `
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page">
          <div class="delpi-ui-document-page__body">
            <img src="/logo.svg" alt="logo" />
            <p>Conteúdo longo</p>
          </div>
        </article>
      </section>
    `;
    const page = findActiveDocumentPage();
    expect(page).toBeTruthy();
    const html = buildDocumentReaderPrintHtml(page!, "Ata teste");
    expect(html).toContain("<title>Ata teste</title>");
    expect(html).toContain("delpi-ui-document-page");
    expect(html).toContain("Conteúdo longo");
    expect(html).toContain("height: auto !important");
    expect(html).toContain('src="');
    expect(html).toMatch(/https?:\/\/.+\/logo\.svg|file:\/\/.+\/logo\.svg|http:\/\/localhost.+\/logo\.svg/);
    expect(html).toContain("doc-test-style");
    document.getElementById("doc-test-style")?.remove();
  });

  it("preserva escopo dashboard-* da prévia (CSS do MFE)", () => {
    document.head.insertAdjacentHTML(
      "beforeend",
      `<style id="tm-facts-style">
        .dashboard-transformometro .tm-ata-document__facts {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
        }
        .dashboard-transformometro .tm-ata-document-brand {
          justify-content: flex-start;
        }
      </style>`,
    );
    document.body.innerHTML = `
      <div class="dashboard-transformometro dashboard-page">
        <div class="tm-atas-view__document">
          <section class="delpi-ui-document-reader tm-ata-reader">
            <article class="delpi-ui-document-page tm-ata-paper">
              <div class="tm-ata-document-brand"><img src="/logo.png" alt="logo" /></div>
              <dl class="tm-ata-document__facts">
                <div><dt>Tipo</dt><dd>Reunião</dd></div>
                <div><dt>Unidade</dt><dd>01</dd></div>
              </dl>
            </article>
          </section>
        </div>
      </div>
    `;
    const page = findActiveDocumentPage()!;
    const scope = collectPrintScopeClasses(page);
    expect(scope).toContain("dashboard-transformometro");
    expect(scope).toContain("delpi-ui-document-reader");

    const html = buildDocumentReaderPrintHtml(page, "Ata Transforma+");
    expect(html).toMatch(
      /class="delpi-ui-document-print-scope[^"]*dashboard-transformometro[^"]*"/,
    );
    expect(html).toContain("tm-ata-document__facts");
    expect(html).toContain("tm-ata-paper");
    expect(html).toContain("tm-facts-style");
    expect(html).toContain('data-theme="light"');
    // Folha não pode herdar max-width mobile na janela estreita
    expect(html).toContain("padding: 14mm 21mm 16mm !important");
    document.getElementById("tm-facts-style")?.remove();
  });

  it("absolutiza href de stylesheets para about:blank", () => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/assets/plugin.css";
    document.head.appendChild(link);
    document.body.innerHTML = `
      <div class="dashboard-cipa">
        <section class="delpi-ui-document-reader">
          <article class="delpi-ui-document-page"><p>CIPA</p></article>
        </section>
      </div>
    `;
    const html = buildDocumentReaderPrintHtml(findActiveDocumentPage()!, "CIPA");
    expect(html).toMatch(/href="https?:\/\/[^"]+\/assets\/plugin\.css"/);
    expect(html).toContain("dashboard-cipa");
    link.remove();
  });

  it("abre janela via printDelpiDocumentHtml", () => {
    document.body.innerHTML = `
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page"><p>Ata</p></article>
      </section>
    `;
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

    expect(printDocumentReaderInWindow({ title: "Ata" })).toBe(true);
    expect(fakeDoc.write).toHaveBeenCalled();
    const written = String(fakeDoc.write.mock.calls[0]?.[0] ?? "");
    expect(written).toContain("Ata");
    expect(written).toContain("delpi-ui-document-page");

    vi.advanceTimersByTime(1_500);
    expect(print).toHaveBeenCalledTimes(1);
  });

  it("downloadDocumentReaderPdf reutiliza o HTML da prévia", () => {
    document.body.innerHTML = `
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page"><p>Prévia</p></article>
      </section>
    `;
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
      print: vi.fn(),
      document: fakeDoc,
      addEventListener: vi.fn(),
    } as unknown as Window;
    vi.spyOn(window, "open").mockReturnValue(fakeWindow);

    expect(downloadDocumentReaderPdf({ title: "Ata" })).toBe(true);
    expect(String(fakeDoc.write.mock.calls[0]?.[0] ?? "")).toContain("Prévia");
  });
});
