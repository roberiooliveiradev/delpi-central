import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";

/**
 * CSS final da janela de impressão/PDF (vence stylesheets copiados do host).
 * Margens ABNT NBR 14724 via @page — não via padding da folha contínua
 * (padding só nas bordas do fluxo; páginas do meio cortam o texto).
 */
const PRINT_WINDOW_BASE_CSS = `
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
/*
 * Folha = fluxo contínuo; área útil por página vem de @page (ABNT).
 * Evita max-width mobile e min-height 297mm que empurram quebras ruins.
 */
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
/* TM sangra o rodapé com margem negativa da prévia — no print corta a página. */
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
/* Tipografia / alinhamento ABNT (corpo justificado; títulos sem indent). */
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
thead,
tbody,
tfoot,
tr,
img,
figure,
.delpi-ui-document-rich-content li {
  break-inside: avoid;
  page-break-inside: avoid;
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
  /*
   * MFEs (ex.: transformometro) copiam regras de isolamento:
   *   @media print { body * { visibility: hidden } }
   *   .dashboard-*.ds-print-root * { visibility: visible }
   * Sem override, a prévia na tela fica ok e o diálogo de impressão sai em branco.
   */
  body.delpi-ui-document-print-window,
  body.delpi-ui-document-print-window * {
    visibility: visible !important;
  }
  body.delpi-ui-document-print-window {
    background: #fff !important;
    color: #000 !important;
  }
  /* Absolute do ds-print-root dos dashboards corta multipágina no Chrome. */
  .delpi-ui-document-print-scope,
  .delpi-ui-document-print-scope.ds-print-root,
  body.delpi-ui-document-print-window .ds-print-root {
    position: static !important;
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
  // Compatível com isolamento print dos dashboards (visibility só com ds-print-root).
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

/**
 * Serializa o papel ativo do DocumentReader em HTML standalone
 * com o mesmo escopo CSS da prévia (dashboard-* / data-delpi-print-scope).
 */
export function buildDocumentReaderPrintHtml(
  page: HTMLElement,
  title = "Documento",
): string {
  const clone = page.cloneNode(true) as HTMLElement;
  absolutizeResourceUrls(clone);
  const scopeClasses = collectPrintScopeClasses(page);
  const scopeClassAttr = ["delpi-ui-document-print-scope", ...scopeClasses]
    .filter(Boolean)
    .join(" ");
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)}</title>
${collectStylesheetsHtml()}
<style>${PRINT_WINDOW_BASE_CSS}</style>
</head>
<body class="delpi-ui-document-print-window" data-theme="light">
<div class="${escapeHtml(scopeClassAttr)}">
${clone.outerHTML}
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
 * Preserva classes de escopo do MFE para paridade visual com a prévia.
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
