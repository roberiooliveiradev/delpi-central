import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";

const PRINT_WINDOW_BASE_CSS = `
html, body {
  margin: 0;
  padding: 0;
  background: #fff;
  height: auto !important;
  overflow: visible !important;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.delpi-ui-document-page {
  width: 210mm !important;
  max-width: 100% !important;
  min-height: 0 !important;
  height: auto !important;
  margin: 0 auto !important;
  overflow: visible !important;
  box-shadow: none !important;
}
.delpi-ui-document-page__body,
.delpi-ui-document-page__header,
.delpi-ui-document-page__footer {
  overflow: visible !important;
}
@page {
  size: A4;
  margin: 10mm;
}
@media print {
  html, body {
    height: auto !important;
    overflow: visible !important;
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

function collectStylesheetsHtml(): string {
  return Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((node) => node.outerHTML)
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

/**
 * Serializa o papel ativo do DocumentReader em HTML standalone
 * (mesma estratégia do chat / certificados: nova janela via printDelpiDocumentHtml).
 */
export function buildDocumentReaderPrintHtml(
  page: HTMLElement,
  title = "Documento",
): string {
  const clone = page.cloneNode(true) as HTMLElement;
  absolutizeResourceUrls(clone);
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)}</title>
${collectStylesheetsHtml()}
<style>${PRINT_WINDOW_BASE_CSS}</style>
</head>
<body class="delpi-ui-document-print-window">
${clone.outerHTML}
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
  // Prefer the last rendered reader (nested shells / abas).
  return pages[pages.length - 1] ?? null;
}

export type PrintDocumentReaderOptions = {
  title?: string;
  iframeTitle?: string;
};

/**
 * Imprime o DocumentReader em janela/iframe dedicada (fluxo canônico DELPI).
 * Evita o clip de 1 página do print in-place com visibility/inset.
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
