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
    expect(html).toContain("ds-print-root");
    expect(html).toContain("tm-ata-document__facts");
    expect(html).toContain("tm-ata-paper");
    expect(html).toContain("tm-facts-style");
    expect(html).toContain('data-theme="light"');
    // A4 + margens ABNT NBR 14724 (não padding da folha contínua)
    expect(html).toContain("size: A4 portrait");
    expect(html).toContain("margin: 30mm 20mm 20mm 30mm");
    expect(html).toContain("text-align: justify !important");
    expect(html).toContain("text-indent: 1.25cm");
    expect(html).toContain("orphans: 3");
    expect(html).toContain("break-after: avoid-page");
    expect(html).toContain("position: static !important");
    // Neutraliza body * { visibility:hidden } dos MFEs no @media print
    expect(html).toContain(
      "body.delpi-ui-document-print-window * {\n    visibility: visible !important;",
    );
    document.getElementById("tm-facts-style")?.remove();
  });

  it("define página A4 ABNT e tipografia anti-corte no HTML de impressão", () => {
    document.body.innerHTML = `
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page">
          <div class="delpi-ui-document-page__body delpi-ui-document-rich-content">
            <h2>2. Objetivo</h2>
            <p>Parágrafo longo da ata.</p>
          </div>
        </article>
      </section>
    `;
    const html = buildDocumentReaderPrintHtml(findActiveDocumentPage()!, "Ata");
    expect(html).toMatch(/@page\s*\{[^}]*size:\s*A4 portrait/);
    expect(html).toMatch(/@page\s*\{[^}]*margin:\s*30mm 20mm 20mm 30mm/);
    expect(html).toContain("padding: 0 !important");
    expect(html).toContain("widows: 3");
    expect(html).toContain("page-break-inside: avoid");
  });

  it("cria cabeçalho e rodapé fixos por página a partir dos slots do papel", () => {
    document.body.innerHTML = `
      <div class="dashboard-transformometro">
        <section class="delpi-ui-document-reader">
          <article class="delpi-ui-document-page tm-ata-paper">
            <div class="delpi-ui-document-page__header">
              <div class="tm-ata-document-brand">
                <img class="tm-ata-document__logo" src="/logo.svg" alt="Transforma+" />
              </div>
            </div>
            <div class="delpi-ui-document-page__body"><p>Corpo da ata</p></div>
            <div class="delpi-ui-document-page__footer">
              <div class="tm-ata-document-footer">
                <footer class="delpi-ui-document-footer">
                  <span>30/07/2026</span>
                  <span>DELPI<br>Jaraguá do Sul — SC</span>
                  <span>Ata 2026/003</span>
                </footer>
                <div class="tm-ata-brand-bar" aria-hidden="true">
                  <span></span><span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </article>
        </section>
      </div>
    `;
    const html = buildDocumentReaderPrintHtml(findActiveDocumentPage()!, "Ata");
    expect(html).toContain('class="delpi-ui-document-print-window has-print-running-header has-print-running-footer"');
    expect(html).toContain('class="delpi-ui-document-print-running-header"');
    expect(html).toContain('class="delpi-ui-document-print-running-footer"');
    expect(html).toContain("tm-ata-document__logo");
    expect(html).toContain("Ata 2026/003");
    expect(html).toContain("tm-ata-brand-bar");
    expect(html).toContain("delpi-ui-document-page__header--print-source");
    expect(html).toContain("delpi-ui-document-page__footer--print-source");
    expect(html).toContain("delpi-ui-document-print-footer-spacer");
    expect(html).toContain("position: fixed");
    // Chrome fixo aparece antes do corpo no HTML (padrão certificados)
    const headerIdx = html.indexOf("delpi-ui-document-print-running-header");
    const footerIdx = html.indexOf("delpi-ui-document-print-running-footer");
    const bodyIdx = html.indexOf("Corpo da ata");
    expect(headerIdx).toBeGreaterThan(-1);
    expect(footerIdx).toBeGreaterThan(headerIdx);
    expect(bodyIdx).toBeGreaterThan(footerIdx);
  });

  it("mantém conteúdo visível sob regra host body * { visibility:hidden }", () => {
    document.head.insertAdjacentHTML(
      "beforeend",
      `<style id="hostile-print">
        @media print {
          body * { visibility: hidden; }
          .dashboard-transformometro.ds-print-root,
          .dashboard-transformometro.ds-print-root * { visibility: visible; }
        }
      </style>`,
    );
    document.body.innerHTML = `
      <div class="dashboard-transformometro">
        <section class="delpi-ui-document-reader">
          <article class="delpi-ui-document-page"><p>Texto da ata</p></article>
        </section>
      </div>
    `;
    const html = buildDocumentReaderPrintHtml(findActiveDocumentPage()!, "Ata");
    expect(html).toContain("visibility: visible !important");
    expect(html).toContain("ds-print-root");
    expect(html).toContain("Texto da ata");
    // Override vem DEPOIS do CSS host (última stylesheet vence na ausência de !important host)
    const hostileIdx = html.indexOf("hostile-print");
    const overrideIdx = html.indexOf("body.delpi-ui-document-print-window *");
    expect(hostileIdx).toBeGreaterThan(-1);
    expect(overrideIdx).toBeGreaterThan(hostileIdx);
    document.getElementById("hostile-print")?.remove();
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
