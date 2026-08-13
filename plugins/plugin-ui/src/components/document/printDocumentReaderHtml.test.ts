import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  buildDocumentReaderPrintHtml,
  collectPrintScopeClasses,
  downloadDocumentReaderPdf,
  findActiveDocumentPage,
  parseDocumentPrintHtml,
  prepareDocumentPagePrintClone,
  printDocumentReaderInWindow,
} from "./printDocumentReaderHtml";

function mountAtaPaperWithChrome(): HTMLElement {
  document.body.innerHTML = `
    <div class="dashboard-transformometro">
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page tm-ata-paper">
          <div class="delpi-ui-document-page__header">
            <div class="tm-ata-document-brand">
              <img class="tm-ata-document__logo" src="/logo.svg" alt="Transforma+" />
            </div>
          </div>
          <div class="delpi-ui-document-page__body">
            <p>Corpo da ata</p>
            <h2>2. Objetivo</h2>
            <p>Texto longo que atravessa páginas.</p>
          </div>
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
  return findActiveDocumentPage()!;
}

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
    expect(html).toContain("size: A4 portrait");
    expect(html).toContain("--delpi-ui-abnt-top: 30mm");
    expect(html).toContain("--delpi-ui-abnt-left: 30mm");
    expect(html).toContain("--delpi-ui-abnt-right: 20mm");
    expect(html).toContain("--delpi-ui-abnt-bottom: 20mm");
    // Uma camada só: @page zerado (não somar com padding do chrome)
    expect(html).toMatch(/@page\s*\{[^}]*margin:\s*0/);
    expect(html).not.toMatch(/@page\s*\{[^}]*margin:\s*30mm 20mm 20mm 30mm/);
    expect(html).toContain("text-align: justify !important");
    expect(html).toContain("text-indent: 1.25cm");
    expect(html).toContain("orphans: 3");
    expect(html).toContain("break-after: avoid-page");
    expect(html).toContain("position: static !important");
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
    expect(html).toMatch(/@page\s*\{[^}]*margin:\s*0/);
    expect(html).toContain("--delpi-ui-abnt-top: 30mm");
    expect(html).toContain("padding: 0 !important");
    expect(html).toContain("widows: 3");
    expect(html).toContain("page-break-inside: avoid");
  });

  it("prepareDocumentPagePrintClone extrai slots sem perder conteúdo", () => {
    const page = mountAtaPaperWithChrome();
    const chrome = prepareDocumentPagePrintClone(page);
    expect(chrome.hasRunningHeader).toBe(true);
    expect(chrome.hasRunningFooter).toBe(true);
    expect(chrome.runningHeaderHtml).toContain("tm-ata-document__logo");
    expect(chrome.runningFooterHtml).toContain("Ata 2026/003");
    expect(chrome.runningFooterHtml).toContain("tm-ata-brand-bar");
    expect(chrome.pageHtml).toContain("header--print-source");
    expect(chrome.pageHtml).toContain("footer--print-source");
    expect(chrome.pageHtml).toContain("Corpo da ata");
  });

  it("coloca cabeçalho no thead e rodapé no tfoot (DOM parseável)", () => {
    const html = buildDocumentReaderPrintHtml(mountAtaPaperWithChrome(), "Ata");
    const doc = parseDocumentPrintHtml(html);

    const layout = doc.querySelector("table.delpi-ui-document-print-layout");
    expect(layout).toBeTruthy();

    const header = layout!.querySelector(
      "thead .delpi-ui-document-print-abnt-header",
    );
    const footer = layout!.querySelector(
      "tfoot .delpi-ui-document-print-abnt-footer",
    );
    const body = layout!.querySelector("tbody .delpi-ui-document-page__body");

    expect(header).toBeTruthy();
    expect(footer).toBeTruthy();
    expect(body).toBeTruthy();
    expect(header!.querySelector(".delpi-ui-document-print-abnt-header__brand img")).toBeTruthy();
    expect(header!.querySelector(".delpi-ui-document-print-abnt-header__page")).toBeNull();
    expect(footer!.textContent).toContain("30/07/2026");
    expect(footer!.textContent).toContain("DELPI");
    expect(footer!.textContent).toContain("Ata 2026/003");
    expect(footer!.querySelector(".tm-ata-brand-bar span")).toBeTruthy();
    expect(body!.textContent).toContain("Corpo da ata");

    expect(
      layout!.querySelector(".delpi-ui-document-page__header--print-source"),
    ).toBeTruthy();
    expect(
      layout!.querySelector(".delpi-ui-document-page__footer--print-source"),
    ).toBeTruthy();

    const scope = doc.querySelector(".delpi-ui-document-print-scope");
    expect(scope?.contains(layout)).toBe(true);
    expect(scope?.className).toContain("ds-print-root");
  });

  it("organiza cabeçalho/rodapé no padrão ABNT sem somar margens", () => {
    const html = buildDocumentReaderPrintHtml(mountAtaPaperWithChrome(), "Ata");
    const style = html.match(
      /<style id="delpi-ui-document-print-base">([\s\S]*?)<\/style>/,
    )?.[1];
    expect(style).toBeTruthy();
    expect(style!).toMatch(/@page\s*\{[\s\S]*?margin:\s*0/);
    expect(style!).not.toMatch(/@page\s*\{[\s\S]*?margin:\s*30mm/);
    expect(style!).toContain("--delpi-ui-abnt-top: 30mm");
    expect(style!).toContain("--delpi-ui-abnt-left: 30mm");
    expect(style!).toContain(
      "calc(var(--delpi-ui-abnt-top) - var(--delpi-ui-abnt-header-band))",
    );
    expect(style!).toContain(
      "calc(var(--delpi-ui-abnt-bottom) - var(--delpi-ui-abnt-footer-band))",
    );
    expect(style!).toMatch(/@top-right\s*\{[^}]*content:\s*counter\(page\)/);
    expect(style!).not.toContain(
      ".delpi-ui-document-print-abnt-header__page::after",
    );
    expect(style!).toMatch(
      /\.delpi-ui-document-print-abnt-footer \.delpi-ui-document-footer\s*\{[^}]*font-size:\s*10pt/,
    );
    expect(style!).toContain("border-bottom: 0.5pt solid #000");
    expect(style!).toContain("border-top: 0.5pt solid #000");

    const doc = parseDocumentPrintHtml(html);
    const row = doc.querySelector(".delpi-ui-document-print-abnt-header__row");
    expect(row?.querySelector(".delpi-ui-document-print-abnt-header__brand")).toBeTruthy();
    expect(row?.querySelector(".delpi-ui-document-print-abnt-header__page")).toBeNull();
  });

  it("CSS de impressão usa table-header-group/footer-group (não position:fixed)", () => {
    const html = buildDocumentReaderPrintHtml(mountAtaPaperWithChrome(), "Ata");
    const style = html.match(
      /<style id="delpi-ui-document-print-base">([\s\S]*?)<\/style>/,
    )?.[1];
    expect(style).toBeTruthy();
    expect(style!).toMatch(
      /\.delpi-ui-document-print-layout\s*>\s*thead\s*\{[^}]*display:\s*table-header-group\s*!important/,
    );
    expect(style!).toMatch(
      /\.delpi-ui-document-print-layout\s*>\s*tfoot\s*\{[^}]*display:\s*table-footer-group\s*!important/,
    );
    // Regressão: fixed falhou em atas longas no Chromium
    expect(style!).not.toMatch(
      /\.delpi-ui-document-print-running-header\s*\{[^}]*position:\s*fixed/,
    );
    expect(style!).not.toMatch(
      /\.delpi-ui-document-print-running-footer\s*\{[^}]*position:\s*fixed/,
    );
  });

  it("omite thead/tfoot quando o papel não tem cabeçalho/rodapé", () => {
    document.body.innerHTML = `
      <section class="delpi-ui-document-reader">
        <article class="delpi-ui-document-page">
          <div class="delpi-ui-document-page__body"><p>Só corpo</p></div>
        </article>
      </section>
    `;
    const html = buildDocumentReaderPrintHtml(findActiveDocumentPage()!, "Doc");
    const doc = parseDocumentPrintHtml(html);
    expect(doc.querySelector("thead")).toBeNull();
    expect(doc.querySelector("tfoot")).toBeNull();
    expect(doc.querySelector("tbody")?.textContent).toContain("Só corpo");
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
    const html = buildDocumentReaderPrintHtml(mountAtaPaperWithChrome(), "Ata");
    expect(html).toContain("visibility: visible !important");
    expect(html).toContain("ds-print-root");
    expect(html).toContain("Corpo da ata");
    const doc = parseDocumentPrintHtml(html);
    // Header/footer precisam estar dentro do escopo visível do MFE
    const scope = doc.querySelector(".delpi-ui-document-print-scope");
    expect(scope?.querySelector("thead .delpi-ui-document-print-running-header")).toBeTruthy();
    expect(scope?.querySelector("tfoot .delpi-ui-document-print-running-footer")).toBeTruthy();
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

  it("abre janela via printDelpiDocumentHtml com layout thead/tfoot", () => {
    mountAtaPaperWithChrome();
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
    const written = String(fakeDoc.write.mock.calls[0]?.[0] ?? "");
    const doc = parseDocumentPrintHtml(written);
    expect(doc.querySelector("thead .delpi-ui-document-print-running-header")).toBeTruthy();
    expect(doc.querySelector("tfoot .delpi-ui-document-print-running-footer")).toBeTruthy();
    expect(written).toContain("table-header-group");
    expect(written).toContain("delpi-ui-document-print-abnt-header");
    expect(written).toContain("@top-right");
    expect(written).toContain("counter(page)");
    expect(written).toMatch(/@page\s*\{[^}]*margin:\s*0/);

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
