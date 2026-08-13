import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";

/**
 * CSS final da janela de impressão/PDF (vence stylesheets copiados do host).
 *
 * Cabeçalho/rodapé: tabela com thead/tfoot (display: table-*-group).
 * Chrome NÃO repete position:fixed de forma confiável em documentos longos;
 * thead/tfoot é o padrão estável (mesmo espírito dos certificados DELPI).
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
.delpi-ui-document-print-layout {
  width: 100% !important;
  border-collapse: collapse !important;
  border-spacing: 0 !important;
  table-layout: fixed !important;
}
.delpi-ui-document-print-layout > thead,
.delpi-ui-document-print-layout > tbody,
.delpi-ui-document-print-layout > tfoot {
  border: none !important;
}
.delpi-ui-document-print-layout > thead > tr > th,
.delpi-ui-document-print-layout > tbody > tr > td,
.delpi-ui-document-print-layout > tfoot > tr > td {
  border: none !important;
  margin: 0 !important;
  vertical-align: top !important;
  background: transparent !important;
}
/*
 * Margens ABNT NBR 14724 numa ÚNICA camada (não somar com @page):
 * superior 30mm · direita 20mm · inferior 20mm · esquerda 30mm.
 * @page { margin: 0 } — o inset vai no padding de thead/tbody/tfoot.
 * Cabeçalho ocupa a faixa superior; rodapé a inferior (texto do corpo
 * começa/termina na borda interna ABNT).
 */
:root {
  --delpi-ui-abnt-top: 30mm;
  --delpi-ui-abnt-right: 20mm;
  --delpi-ui-abnt-bottom: 20mm;
  --delpi-ui-abnt-left: 30mm;
  --delpi-ui-abnt-header-band: 12mm;
  --delpi-ui-abnt-footer-band: 14mm;
}
.delpi-ui-document-print-layout > thead > tr > th {
  /* topo até o logo + laterais; banda do chrome ≈ 12mm → corpo aos 30mm */
  padding:
    calc(var(--delpi-ui-abnt-top) - var(--delpi-ui-abnt-header-band))
    var(--delpi-ui-abnt-right)
    0
    var(--delpi-ui-abnt-left) !important;
}
.delpi-ui-document-print-layout > tbody > tr > td {
  padding: 0 var(--delpi-ui-abnt-right) 0 var(--delpi-ui-abnt-left) !important;
}
.delpi-ui-document-print-layout > tfoot > tr > td {
  padding:
    0
    var(--delpi-ui-abnt-right)
    calc(var(--delpi-ui-abnt-bottom) - var(--delpi-ui-abnt-footer-band))
    var(--delpi-ui-abnt-left) !important;
}
body:not(.has-print-running-header) .delpi-ui-document-print-layout > tbody > tr > td {
  padding-top: var(--delpi-ui-abnt-top) !important;
}
body:not(.has-print-running-footer) .delpi-ui-document-print-layout > tbody > tr > td {
  padding-bottom: var(--delpi-ui-abnt-bottom) !important;
}
/*
 * Chrome ABNT (NBR 14724):
 * - cabeçalho: identificação à esquerda (numeração via @page @top-right —
 *   counter(page) em elemento HTML no Chromium rende "0")
 * - rodapé: data | instituição | referência (10pt), linha 0,5 pt
 */
.delpi-ui-document-print-running-header,
.delpi-ui-document-print-running-footer,
.delpi-ui-document-print-abnt-header,
.delpi-ui-document-print-abnt-footer {
  display: block;
  width: 100%;
  box-sizing: border-box;
  margin: 0 !important;
  padding: 0 !important;
  background: #fff !important;
  color: #000 !important;
  font-family: Arial, Helvetica, sans-serif !important;
}
.delpi-ui-document-print-abnt-header {
  height: var(--delpi-ui-abnt-header-band);
  max-height: var(--delpi-ui-abnt-header-band);
  overflow: hidden;
}
.delpi-ui-document-print-abnt-header__row {
  display: flex !important;
  align-items: flex-end !important;
  justify-content: space-between !important;
  gap: 8mm;
  height: 100%;
  box-sizing: border-box;
  padding: 0 0 2mm !important;
  border-bottom: 0.5pt solid #000;
  margin: 0 !important;
}
.delpi-ui-document-print-abnt-header__brand {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
}
.delpi-ui-document-print-abnt-header__brand .tm-ata-document-brand,
.delpi-ui-document-print-abnt-header__brand .delpi-ui-document-header {
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  margin: 0 !important;
  padding: 0 !important;
  border: none;
}
.delpi-ui-document-print-abnt-header__brand img,
.delpi-ui-document-print-abnt-header__brand .tm-ata-document__logo,
.delpi-ui-document-print-abnt-header__brand svg {
  display: block;
  max-height: 9mm !important;
  max-width: 36mm !important;
  width: auto !important;
  height: auto !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.delpi-ui-document-print-abnt-footer {
  height: var(--delpi-ui-abnt-footer-band);
  max-height: var(--delpi-ui-abnt-footer-band);
  overflow: hidden;
  box-sizing: border-box;
}
.delpi-ui-document-print-abnt-footer .tm-ata-document-footer {
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-end !important;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}
.delpi-ui-document-print-abnt-footer .delpi-ui-document-footer {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.5fr) minmax(0, 1fr) !important;
  align-items: end !important;
  column-gap: 6mm !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 2mm 0 1.5mm !important;
  border-top: 0.5pt solid #000 !important;
  box-sizing: border-box !important;
  font-size: 10pt !important;
  line-height: 1.2 !important;
  color: #000 !important;
}
.delpi-ui-document-print-abnt-footer .delpi-ui-document-footer > :nth-child(1) {
  text-align: left !important;
  justify-self: start;
}
.delpi-ui-document-print-abnt-footer .delpi-ui-document-footer > :nth-child(2) {
  text-align: center !important;
  justify-self: center;
  font-weight: 700 !important;
}
.delpi-ui-document-print-abnt-footer .delpi-ui-document-footer > :nth-child(3) {
  text-align: right !important;
  justify-self: end;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar,
.delpi-ui-document-print-abnt-footer [class*="brand-bar"] {
  display: flex !important;
  height: 3px !important;
  width: 100% !important;
  margin: 0 !important;
  overflow: hidden;
  flex-shrink: 0;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar span,
.delpi-ui-document-print-abnt-footer [class*="brand-bar"] span {
  flex: 1 !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar span:nth-child(1) {
  background: #013866 !important;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar span:nth-child(2) {
  background: #025a8f !important;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar span:nth-child(3) {
  background: #0477a8 !important;
}
.delpi-ui-document-print-abnt-footer .tm-ata-brand-bar span:nth-child(4) {
  background: #089bdb !important;
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
/* Slots originais do papel: conteúdo já foi para thead/tfoot. */
.delpi-ui-document-page__header--print-source,
.delpi-ui-document-page__footer--print-source {
  display: none !important;
}
/*
 * Marca d'água no fluxo do papel (tiles A4) — mesma estratégia da prévia.
 * position:fixed no Chromium só aparece na última página e sobe o texto.
 */
.delpi-ui-document-page {
  position: relative !important;
}
.delpi-ui-document-page__watermark {
  position: absolute !important;
  inset: 0 !important;
  z-index: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  pointer-events: none !important;
  overflow: hidden !important;
}
.delpi-ui-document-page__watermark-tile {
  flex: 0 0 297mm !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 24% 20% !important;
  opacity: 0.09 !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.delpi-ui-document-page__watermark-tile img,
.delpi-ui-document-page__watermark-tile svg,
.delpi-ui-document-page__watermark img,
.delpi-ui-document-page__watermark svg {
  display: block !important;
  max-width: 100% !important;
  max-height: 100% !important;
}
.delpi-ui-document-page__header,
.delpi-ui-document-page__body,
.delpi-ui-document-page__footer {
  position: relative !important;
  z-index: 1 !important;
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
table:not(.delpi-ui-document-print-layout),
tr,
img,
figure {
  break-inside: avoid;
  page-break-inside: avoid;
}
@page {
  size: A4 portrait;
  /*
   * Margem zero no @page — ABNT aplicada só no padding thead/tbody/tfoot.
   * Somar @page 30mm + padding do chrome dobrava o branco (e o diálogo
   * "Margens: Padrão" ainda empilhava o default do browser).
   */
  margin: 0;
  /* Numeração ABNT (canto superior direito). Preferível a counter() no HTML. */
  @top-right {
    content: counter(page);
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    vertical-align: top;
    padding-top: 18mm;
    padding-right: 20mm;
  }
}
@media print {
  html, body {
    height: auto !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
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
  /*
   * Repetição por página — obrigatório no motor de impressão do Chromium.
   * Não usar position:fixed para este chrome (falha em atas longas).
   */
  .delpi-ui-document-print-layout > thead {
    display: table-header-group !important;
  }
  .delpi-ui-document-print-layout > tfoot {
    display: table-footer-group !important;
  }
  .delpi-ui-document-print-layout > tbody {
    display: table-row-group !important;
  }
  .delpi-ui-document-page__watermark {
    position: absolute !important;
    z-index: 0 !important;
  }
  .delpi-ui-document-page__header,
  .delpi-ui-document-page__body,
  .delpi-ui-document-page__footer {
    position: relative !important;
    z-index: 1 !important;
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
  /** Quantidade de tiles A4 da marca d'água no papel (fluxo, não fixed). */
  watermarkTileCount: number;
  pageHtml: string;
  hasRunningHeader: boolean;
  hasRunningFooter: boolean;
  hasRunningWatermark: boolean;
};

/**
 * Garante um tile A4 por faixa do papel contínuo no clone de impressão.
 * A prévia já mede via ResizeObserver; o clone reforça a cobertura.
 */
export function ensurePrintWatermarkTileCoverage(
  sourcePage: HTMLElement,
  clone: HTMLElement,
): number {
  const watermark = clone.querySelector<HTMLElement>(".delpi-ui-document-page__watermark");
  if (!watermark) return 0;

  let tiles = Array.from(
    watermark.querySelectorAll<HTMLElement>(".delpi-ui-document-page__watermark-tile"),
  );

  if (tiles.length === 0) {
    const wrap = document.createElement("div");
    wrap.className = "delpi-ui-document-page__watermark-tile";
    while (watermark.firstChild) {
      wrap.appendChild(watermark.firstChild);
    }
    if (!wrap.innerHTML.trim()) return 0;
    watermark.appendChild(wrap);
    tiles = [wrap];
  }

  const sourceTile = sourcePage.querySelector<HTMLElement>(
    ".delpi-ui-document-page__watermark-tile",
  );
  const tilePx =
    sourceTile?.getBoundingClientRect().height ||
    sourcePage.offsetHeight ||
    (297 * 96) / 25.4;
  const needed = Math.max(1, Math.ceil(Math.max(sourcePage.offsetHeight, 1) / tilePx));
  const template = tiles[0]!;
  while (tiles.length < needed) {
    watermark.appendChild(template.cloneNode(true));
    tiles = Array.from(
      watermark.querySelectorAll<HTMLElement>(".delpi-ui-document-page__watermark-tile"),
    );
  }
  return tiles.length;
}

/**
 * Extrai cabeçalho/rodapé do papel para thead/tfoot e mantém a marca d'água
 * no fluxo do corpo (tiles A4) — fixed no Chromium falha em multipágina.
 */
export function prepareDocumentPagePrintClone(page: HTMLElement): DocumentPrintChrome {
  const clone = page.cloneNode(true) as HTMLElement;
  absolutizeResourceUrls(clone);

  const headerEl = clone.querySelector<HTMLElement>(".delpi-ui-document-page__header");
  const footerEl = clone.querySelector<HTMLElement>(".delpi-ui-document-page__footer");

  const runningHeaderHtml = headerEl?.innerHTML.trim() || "";
  const runningFooterHtml = footerEl?.innerHTML.trim() || "";
  const watermarkTileCount = ensurePrintWatermarkTileCoverage(page, clone);

  if (headerEl && runningHeaderHtml) {
    headerEl.classList.add("delpi-ui-document-page__header--print-source");
  }
  if (footerEl && runningFooterHtml) {
    footerEl.classList.add("delpi-ui-document-page__footer--print-source");
  }

  return {
    runningHeaderHtml,
    runningFooterHtml,
    watermarkTileCount,
    pageHtml: clone.outerHTML,
    hasRunningHeader: Boolean(runningHeaderHtml),
    hasRunningFooter: Boolean(runningFooterHtml),
    hasRunningWatermark: watermarkTileCount > 0,
  };
}

/**
 * Conteúdo de um único tile (prévia/print podem repetir N tiles A4).
 * Preferência: primeiro `.delpi-ui-document-page__watermark-tile`.
 */
export function extractWatermarkInnerHtml(
  watermarkEl: HTMLElement | null | undefined,
): string {
  if (!watermarkEl) return "";
  const tile = watermarkEl.querySelector<HTMLElement>(
    ".delpi-ui-document-page__watermark-tile",
  );
  const source = tile ?? watermarkEl;
  return source.innerHTML.trim();
}

/** Parseia o HTML de impressão para asserts estruturais nos testes. */
export function parseDocumentPrintHtml(html: string): Document {
  return new DOMParser().parseFromString(html, "text/html");
}

/** Cabeçalho ABNT: marca à esquerda (numeração em @page @top-right). */
export function buildAbntPrintHeaderHtml(brandInnerHtml: string): string {
  return `<div class="delpi-ui-document-print-running-header delpi-ui-document-print-abnt-header">
  <div class="delpi-ui-document-print-abnt-header__row">
    <div class="delpi-ui-document-print-abnt-header__brand">${brandInnerHtml}</div>
  </div>
</div>`;
}

/** Rodapé ABNT: reaproveita meta (data | instituição | referência) + faixa. */
export function buildAbntPrintFooterHtml(footerInnerHtml: string): string {
  return `<div class="delpi-ui-document-print-running-footer delpi-ui-document-print-abnt-footer">
  ${footerInnerHtml}
</div>`;
}

/**
 * Serializa o papel ativo do DocumentReader em HTML standalone
 * com cabeçalho/rodapé ABNT em thead/tfoot e marca d'água em tiles no fluxo.
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
    chrome.hasRunningWatermark ? "has-print-flow-watermark" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const thead = chrome.hasRunningHeader
    ? `<thead>
  <tr>
    <th scope="col">
      ${buildAbntPrintHeaderHtml(chrome.runningHeaderHtml)}
    </th>
  </tr>
</thead>`
    : "";

  const tfoot = chrome.hasRunningFooter
    ? `<tfoot>
  <tr>
    <td>
      ${buildAbntPrintFooterHtml(chrome.runningFooterHtml)}
    </td>
  </tr>
</tfoot>`
    : "";

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)}</title>
${collectStylesheetsHtml()}
<style id="delpi-ui-document-print-base">${PRINT_WINDOW_BASE_CSS}</style>
</head>
<body class="${escapeHtml(bodyClasses)}" data-theme="light">
<div class="${escapeHtml(scopeClassAttr)}">
<table class="delpi-ui-document-print-layout">
${thead}
<tbody>
  <tr>
    <td>
${chrome.pageHtml}
    </td>
  </tr>
</tbody>
${tfoot}
</table>
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
