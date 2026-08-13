import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";

const PRINT_WINDOW_BASE_CSS = `
html, body {
  margin: 0;
  padding: 0;
  background: #fff !important;
  color: #151515 !important;
  height: auto !important;
  overflow: visible !important;
  color-scheme: light !important;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
/* Evita @media max-width do DocumentReader/MFE encolher a folha na janela estreita. */
.delpi-ui-document-page {
  width: 210mm !important;
  max-width: 210mm !important;
  min-height: 0 !important;
  height: auto !important;
  margin: 0 auto !important;
  padding: 14mm 21mm 16mm !important;
  overflow: visible !important;
  box-shadow: none !important;
  background: #fff !important;
  color: #151515 !important;
}
.delpi-ui-document-page__body,
.delpi-ui-document-page__header,
.delpi-ui-document-page__footer {
  overflow: visible !important;
}
.delpi-ui-document-print-scope {
  display: block;
  width: 100%;
  background: #fff;
  color: #151515;
}
@page {
  size: A4;
  margin: 0;
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

/**
 * Classes de escopo do MFE (ex.: dashboard-transformometro, dashboard-cipa)
 * necessárias para o CSS da prévia casar na janela de impressão.
 */
export function collectPrintScopeClasses(page: HTMLElement): string[] {
  const classes: string[] = [];
  const seen = new Set<string>();
  let el: HTMLElement | null = page.parentElement;
  while (el && el !== document.documentElement) {
    for (const name of Array.from(el.classList)) {
      const keep =
        name.startsWith("dashboard-") ||
        name === "delpi-ui-document-reader" ||
        name.startsWith("tm-atas-") ||
        name.startsWith("cipa-") ||
        name.startsWith("cec-") ||
        name === "dashboard-page";
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
