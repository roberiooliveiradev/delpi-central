import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";

/**
 * CSS final da janela de impressão/PDF (vence stylesheets copiados do host).
 * Margens ABNT NBR 14724 via @page — não via padding da folha contínua.
 * Cabeçalho/rodapé do DocumentPage viram chrome fixo por página (padrão certificados).
 */
const PRINT_WINDOW_BASE_CSS = `
:root {
  --delpi-ui-doc-print-header-height: 22mm;
  --delpi-ui-doc-print-footer-height: 18mm;
}
html, body {
  margin: 0;
  padding: 0;
  background: #fff !important;
  color: #000 !important;
  height: auto !important;
  overflow: visible !important;
  color-scheme: light !important;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
  font-family: Arial, Helvetica, sans-serif !important;
  font-size: 12pt !important;
  line-height: 1.5 !important;
}
.delpi-ui-document-page {
  width: 100% !important;
  max-width: none !important;
  min-height: 0 !important;
  height: auto !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  box-shadow: none !important;
  background: #fff !important;
  color: #000 !important;
  font-family: Arial, Helvetica, sans-serif !important;
  font-size: 12pt !important;
  line-height: 1.5 !important;
}
.delpi-ui-document-page__body,
.delpi-ui-document-page__header,
.delpi-ui-document-page__footer {
  overflow: visible !important;
}
.delpi-ui-document-page__body {
  padding: 0 !important;
  flex: none !important;
}
.delpi-ui-document-page > .delpi-ui-document-page__footer,
.tm-ata-paper > .delpi-ui-document-page__footer {
  margin-left: 0 !important;
  margin-right: 0 !important;
  width: 100% !important;
  max-width: none !important;
}
.tm-ata-document-footer > .delpi-ui-document-footer {
  padding-left: 0 !important;
  padding-right: 0 !important;
}
.delpi-ui-document-print-scope,
.delpi-ui-document-print-scope.ds-print-root,
body.delpi-ui-document-print-window .ds-print-root {
  display: block !important;
  position: static !important;
  left: auto !important;
  top: auto !important;
  width: 100% !important;
  max-width: none !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: auto !important;
  background: #fff !important;
  color: #000 !important;
  box-shadow: none !important;
  animation: none !important;
}
/* Tipografia ABNT */
.delpi-ui-document-page p,
.delpi-ui-document-rich-content p,
.tm-ata-document__body p,
.tm-ata-document__lede {
  text-align: justify !important;
  orphans: 3;
  widows: 3;
}
.delpi-ui-document-rich-content > p,
.tm-ata-document__body > p {
  text-indent: 1.25cm;
}
.delpi-ui-document-rich-content li,
.tm-ata-document__body li,
.tm-ata-document__participants li {
  text-align: justify !important;
  text-indent: 0 !important;
  orphans: 2;
  widows: 2;
}
.delpi-ui-document-rich-content li > p,
.tm-ata-document__body li > p {
  text-indent: 0 !important;
  text-align: justify !important;
}
.tm-ata-document__title,
.delpi-ui-document-header__title,
.delpi-ui-document-header__copy {
  text-align: center !important;
  text-indent: 0 !important;
}
.tm-ata-document__facts,
.tm-ata-document__facts dt,
.tm-ata-document__facts dd {
  text-align: left !important;
  text-indent: 0 !important;
}
h1, h2, h3, h4, h5, h6,
.tm-ata-document__body h2,
.tm-ata-document__signatures h2,
.tm-ata-document__participants h2,
.tm-ata-document__title {
  break-after: avoid-page;
  page-break-after: avoid;
  break-inside: avoid;
  page-break-inside: avoid;
  orphans: 3;
  widows: 3;
  text-indent: 0 !important;
}
.delpi-ui-document-signature,
.tm-ata-document__facts,
.tm-ata-document__participants,
.tm-ata-document__signature-grid,
.delpi-ui-document-header,
.tm-ata-document-brand,
table,
tr,
img,
figure {
  break-inside: avoid;
  page-break-inside: avoid;
}
/* Chrome fixo: oculto na prévia da janela; ativo só no @media print. */
.delpi-ui-document-print-running-header,
.delpi-ui-document-print-running-footer {
  display: none;
}
.delpi-ui-document-print-footer-spacer {
  display: none;
  height: 0;
}
@page {
  size: A4 portrait;
  /* NBR 14724: superior 3cm · direita 2cm · inferior 2cm · esquerda 3cm */
  margin: 30mm 20mm 20mm 30mm;
}
@media print {
  html, body {
    height: auto !important;
    overflow: visible !important;
  }
  body.delpi-ui-document-print-window,
  body.delpi-ui-document-print-window * {
    visibility: visible !important;
  }
  body.delpi-ui-document-print-window {
    background: #fff !important;
    color: #000 !important;
  }
  .delpi-ui-document-print-scope,
  .delpi-ui-document-print-scope.ds-print-root,
  body.delpi-ui-document-print-window .ds-print-root {
    position: static !important;
  }
  body.has-print-running-header .delpi-ui-document-print-scope {
    padding-top: var(--delpi-ui-doc-print-header-height) !important;
  }
  body.has-print-running-footer .delpi-ui-document-print-footer-spacer {
    display: block !important;
    height: var(--delpi-ui-doc-print-footer-height) !important;
  }
  /* Slots originais do papel: só na prévia; na impressão o chrome fixo assume. */
  .delpi-ui-document-page__header--print-source,
  .delpi-ui-document-page__footer--print-source {
    display: none !important;
  }
  .delpi-ui-document-print-running-header {
    display: block !important;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 40;
    box-sizing: border-box;
    max-height: var(--delpi-ui-doc-print-header-height);
    padding: 0 0 2mm;
    background: #fff !important;
    border-bottom: 1px solid #111;
    overflow: hidden;
  }
  .delpi-ui-document-print-running-header .tm-ata-document-brand,
  .delpi-ui-document-print-running-header .delpi-ui-document-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
  }
  .delpi-ui-document-print-running-header img,
  .delpi-ui-document-print-running-header .tm-ata-document__logo,
  .delpi-ui-document-print-running-header svg {
    display: block;
    max-height: 14mm !important;
    max-width: 42mm !important;
    width: auto !important;
    height: auto !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .delpi-ui-document-print-running-footer {
    display: block !important;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 40;
    box-sizing: border-box;
    max-height: var(--delpi-ui-doc-print-footer-height);
    background: #fff !important;
    overflow: hidden;
  }
  .delpi-ui-document-print-running-footer .tm-ata-document-footer,
  .delpi-ui-document-print-running-footer .delpi-ui-document-footer {
    width: 100% !important;
    margin: 0 !important;
    padding: 1.5mm 0 0 !important;
    box-sizing: border-box;
  }
  .delpi-ui-document-print-running-footer .delpi-ui-document-footer {
    border-top: 1px solid #111;
    font-size: 9px !important;
    line-height: 1.3 !important;
  }
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar,
  .delpi-ui-document-print-running-footer [class*="brand-bar"] {
    display: flex !important;
    height: 4px !important;
    width: 100% !important;
    margin: 0 !important;
  }
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar span,
  .delpi-ui-document-print-running-footer [class*="brand-bar"] span {
    flex: 1 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  /* Fallback de cores da faixa se tokens do MFE não resolverem no about:blank */
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar span:nth-child(1) {
    background: #013866 !important;
  }
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar span:nth-child(2) {
    background: #025a8f !important;
  }
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar span:nth-child(3) {
    background: #0477a8 !important;
  }
  .delpi-ui-document-print-running-footer .tm-ata-brand-bar span:nth-child(4) {
    background: #089bdb !important;
  }
}
`;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Classes de escopo do MFE (ex.: dashboard-transformometro, dashboard-cipa)
 * necessárias para o CSS da prévia casar na janela de impressão.
 */
export function collectPrintScopeClasses(page: HTMLElement): string[] {
  const classes: string[] = [];
  const seen = new Set<string>();
  let el: HTMLElement | null = page.parentElement;
  let hasDashboardScope = false;
  while (el && el !== document.documentElement) {
    for (const name of Array.from(el.classList)) {
      const keep =
        name.startsWith("dashboard-") ||
        name === "delpi-ui-document-reader" ||
        name.startsWith("tm-atas-") ||
        name.startsWith("cipa-") ||
        name.startsWith("cec-") ||
        name === "dashboard-page" ||
        name === "ds-print-root";
      if (name.startsWith("dashboard-")) hasDashboardScope = true;
      if (keep && !seen.has(name)) {
        seen.add(name);
        classes.push(name);
      }
    }
    const explicit = el.getAttribute("data-delpi-print-scope");
    if (explicit) {
      for (const name of explicit.split(/\s+/).filter(Boolean)) {
        if (!seen.has(name)) {
          seen.add(name);
          classes.push(name);
        }
      }
    }
    el = el.parentElement;
  }
  if (hasDashboardScope && !seen.has("ds-print-root")) {
    classes.push("ds-print-root");
  }
  return classes;
}

function collectStylesheetsHtml(): string {
  return Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((node) => {
      if (node instanceof HTMLLinkElement) {
        const href = node.getAttribute("href") || node.href;
        if (!href) return node.outerHTML;
        try {
          const absolute = new URL(href, document.baseURI).href;
          const media = node.media ? ` media="${escapeHtml(node.media)}"` : "";
          return `<link rel="stylesheet" href="${escapeHtml(absolute)}"${media} />`;
        } catch {
          return node.outerHTML;
        }
      }
      return node.outerHTML;
    })
    .join("\n");
}

function absolutizeResourceUrls(root: ParentNode): void {
  root.querySelectorAll("[src]").forEach((el) => {
    const raw = el.getAttribute("src");
    if (!raw || raw.startsWith("data:") || raw.startsWith("blob:")) return;
    try {
      el.setAttribute("src", new URL(raw, document.baseURI).href);
    } catch {
      /* keep original */
    }
  });
  root.querySelectorAll("img[srcset]").forEach((el) => {
    el.removeAttribute("srcset");
  });
}

export type DocumentPrintChrome = {
  runningHeaderHtml: string;
  runningFooterHtml: string;
  pageHtml: string;
  hasRunningHeader: boolean;
  hasRunningFooter: boolean;
};

/**
 * Extrai cabeçalho/rodapé do papel para chrome fixo por página
 * e marca os slots originais para ocultar no @media print.
 */
export function prepareDocumentPagePrintClone(page: HTMLElement): DocumentPrintChrome {
  const clone = page.cloneNode(true) as HTMLElement;
  absolutizeResourceUrls(clone);

  const headerEl = clone.querySelector<HTMLElement>(".delpi-ui-document-page__header");
  const footerEl = clone.querySelector<HTMLElement>(".delpi-ui-document-page__footer");

  const runningHeaderHtml = headerEl?.innerHTML.trim() || "";
  const runningFooterHtml = footerEl?.innerHTML.trim() || "";

  if (headerEl && runningHeaderHtml) {
    headerEl.classList.add("delpi-ui-document-page__header--print-source");
  }
  if (footerEl && runningFooterHtml) {
    footerEl.classList.add("delpi-ui-document-page__footer--print-source");
    const spacer = clone.ownerDocument!.createElement("div");
    spacer.className = "delpi-ui-document-print-footer-spacer";
    spacer.setAttribute("aria-hidden", "true");
    footerEl.insertAdjacentElement("afterend", spacer);
  }

  return {
    runningHeaderHtml,
    runningFooterHtml,
    pageHtml: clone.outerHTML,
    hasRunningHeader: Boolean(runningHeaderHtml),
    hasRunningFooter: Boolean(runningFooterHtml),
  };
}

/**
 * Serializa o papel ativo do DocumentReader em HTML standalone
 * com cabeçalho/rodapé repetidos em cada página impressa.
 */
export function buildDocumentReaderPrintHtml(
  page: HTMLElement,
  title = "Documento",
): string {
  const chrome = prepareDocumentPagePrintClone(page);
  const scopeClasses = collectPrintScopeClasses(page);
  const scopeClassAttr = ["delpi-ui-document-print-scope", ...scopeClasses]
    .filter(Boolean)
    .join(" ");
  const bodyClasses = [
    "delpi-ui-document-print-window",
    chrome.hasRunningHeader ? "has-print-running-header" : "",
    chrome.hasRunningFooter ? "has-print-running-footer" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const runningHeaderBlock = chrome.hasRunningHeader
    ? `<div class="delpi-ui-document-print-running-header" aria-hidden="true">${chrome.runningHeaderHtml}</div>`
    : "";
  const runningFooterBlock = chrome.hasRunningFooter
    ? `<div class="delpi-ui-document-print-running-footer" aria-hidden="true">${chrome.runningFooterHtml}</div>`
    : "";

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)}</title>
${collectStylesheetsHtml()}
<style>${PRINT_WINDOW_BASE_CSS}</style>
</head>
<body class="${escapeHtml(bodyClasses)}" data-theme="light">
${runningHeaderBlock}
${runningFooterBlock}
<div class="${escapeHtml(scopeClassAttr)}">
${chrome.pageHtml}
</div>
</body>
</html>`;
}

export function findActiveDocumentPage(): HTMLElement | null {
  const pages = Array.from(
    document.querySelectorAll<HTMLElement>(
      ".delpi-ui-document-reader .delpi-ui-document-page",
    ),
  );
  if (!pages.length) return null;
  return pages[pages.length - 1] ?? null;
}

export type PrintDocumentReaderOptions = {
  title?: string;
  iframeTitle?: string;
};

/**
 * Imprime o DocumentReader em janela/iframe dedicada (fluxo canônico DELPI).
 * Preserva classes de escopo do MFE e chrome de cabeçalho/rodapé por página.
 */
export function printDocumentReaderInWindow(
  options: PrintDocumentReaderOptions = {},
): boolean {
  const page = findActiveDocumentPage();
  if (!page) return false;
  const title = options.title?.trim() || document.title || "Documento";
  const html = buildDocumentReaderPrintHtml(page, title);
  return printDelpiDocumentHtml(html, {
    iframeTitle: options.iframeTitle || title,
  });
}

/**
 * PDF com a formatação da prévia — mesmo HTML da impressão (Salvar como PDF).
 */
export function downloadDocumentReaderPdf(
  options: PrintDocumentReaderOptions = {},
): boolean {
  return printDocumentReaderInWindow(options);
}
