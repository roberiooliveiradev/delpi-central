import type { DrawingAnalysisExportPayload } from "./drawingAnalysisExport";

export type DrawingExportTable = NonNullable<
  DrawingAnalysisExportPayload["tables"]
>[number];

type ReportHeaderContext = {
  exportLabels: NonNullable<DrawingAnalysisExportPayload["exportLabels"]>;
  productCode: string;
  overall: string;
  critical: unknown;
  sealClass: string;
  logoMarkup: string;
};

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function resolveSealClass(drawingAnalysis?: Record<string, unknown>): string {
  const status = String(drawingAnalysis?.status || "").toLowerCase();

  if (status === "approved" || status === "ok") {
    return "cert-seal--approved";
  }

  if (status === "rejected") {
    return "cert-seal--rejected";
  }

  const label = String(drawingAnalysis?.overallLabel || "").toLowerCase();

  if (label.includes("reprov")) {
    return "cert-seal--rejected";
  }

  if (label.includes("aprov")) {
    return "cert-seal--approved";
  }

  return "cert-seal--neutral";
}

function buildDrawingReportStyles(): string {
  return `
    :root {
      --cert-blue-900: #013866;
      --cert-blue-700: #015488;
      --cert-blue-500: #208BB8;
      --cert-blue-accent: #30B8EC;
      --cert-gray-900: #1A202C;
      --cert-gray-600: #64748B;
      --cert-gray-200: #E2E8F0;
      --cert-gray-50: #F8FAFC;
      --cert-green: #166534;
      --cert-red: #B91C1C;
      --cert-running-header-height: 20mm;
      --cert-footer-height: 18mm;
    }
    @page { size: A4 portrait; margin: 10mm 12mm 14mm; }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 10pt;
      line-height: 1.4;
      color: var(--cert-gray-900);
      background: #ffffff;
    }
    body {
      padding: 0;
      box-decoration-break: clone;
      -webkit-box-decoration-break: clone;
    }
    .cert-print-running-header { display: none; }
    .cert-print-layout {
      width: 100%;
      border-collapse: collapse;
      border-spacing: 0;
    }
    .cert-print-layout > tbody > tr > td,
    .cert-print-layout > tfoot > tr > td {
      border: none;
      padding: 0;
      vertical-align: top;
    }
    .cert-print-footer-spacer { height: var(--cert-footer-height); }
    .cert-main {
      max-width: 186mm;
      margin: 0 auto;
      width: 100%;
    }
    .cert-header {
      background: linear-gradient(180deg, #f8fbfd 0%, #ffffff 100%);
      border: 1px solid var(--cert-gray-200);
      border-radius: 4px 4px 0 0;
      padding: 10px 12px 0;
    }
    .cert-header__top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding-bottom: 10px;
    }
    .cert-header__brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      flex: 1;
    }
    .cert-logo { width: 88px; height: auto; flex-shrink: 0; }
    .cert-logo--compact { width: 52px; }
    .cert-title {
      margin: 0;
      font-size: 15pt;
      font-weight: 700;
      color: var(--cert-blue-900);
      line-height: 1.15;
    }
    .cert-title--compact { font-size: 10.5pt; }
    .cert-subtitle {
      margin: 2px 0 0;
      font-size: 9.5pt;
      font-weight: 600;
      color: var(--cert-gray-600);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .cert-subtitle--compact { font-size: 7.5pt; margin-top: 1px; }
    .cert-running-meta {
      margin: 0;
      font-size: 7.5pt;
      color: var(--cert-gray-600);
      line-height: 1.3;
    }
    .cert-seal {
      flex-shrink: 0;
      min-width: 88px;
      padding: 6px 12px;
      border-radius: 3px;
      border: 1.5px solid var(--cert-blue-700);
      background: #ffffff;
      text-align: center;
      font-size: 8.5pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      line-height: 1.2;
      color: var(--cert-blue-900);
    }
    .cert-seal--compact {
      min-width: 72px;
      padding: 4px 8px;
      font-size: 7.5pt;
    }
    .cert-seal--approved { border-color: var(--cert-green); color: var(--cert-green); }
    .cert-seal--rejected { border-color: var(--cert-red); color: var(--cert-red); }
    .cert-seal--neutral { border-color: var(--cert-gray-600); color: var(--cert-gray-600); }
    .cert-header__brand-bar {
      display: flex;
      height: 3px;
      margin: 0 -12px;
    }
    .cert-header__brand-bar span { flex: 1; }
    .cert-header__brand-bar span:nth-child(1) { background: var(--cert-blue-900); }
    .cert-header__brand-bar span:nth-child(2) { background: var(--cert-blue-700); }
    .cert-header__brand-bar span:nth-child(3) { background: var(--cert-blue-500); }
    .cert-header__brand-bar span:nth-child(4) { background: var(--cert-blue-accent); }
    .cert-summary {
      border: 1px solid var(--cert-gray-200);
      border-top: none;
      border-radius: 0 0 4px 4px;
      padding: 10px 12px;
      margin-bottom: 12px;
      background: #ffffff;
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .cert-summary__grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px 16px;
    }
    .cert-info-line {
      margin: 0;
      font-size: 9pt;
      color: var(--cert-gray-900);
      line-height: 1.35;
    }
    .cert-info-line strong {
      display: block;
      font-size: 7.5pt;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--cert-gray-600);
      font-weight: 700;
      margin-bottom: 2px;
    }
    .cert-section {
      margin-bottom: 12px;
      break-inside: auto;
      page-break-inside: auto;
    }
    .cert-section__title {
      margin: 0 0 6px;
      font-size: 8pt;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--cert-blue-900);
      font-weight: 700;
      break-after: avoid;
      page-break-after: avoid;
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .cert-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 8pt;
      table-layout: fixed;
      break-inside: auto;
      page-break-inside: auto;
    }
    .cert-table thead { display: table-header-group; }
    .cert-table tbody { display: table-row-group; }
    .cert-table th, .cert-table td {
      border: 1px solid var(--cert-gray-200);
      padding: 4px 5px;
      vertical-align: top;
      text-align: left;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }
    .cert-table th {
      background: var(--cert-blue-900);
      color: #ffffff;
      font-weight: 700;
      font-size: 7pt;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .cert-table tbody tr {
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .cert-table tbody tr:nth-child(even) td { background: var(--cert-gray-50); }
    .cert-status--error { color: var(--cert-red); font-weight: 700; }
    .cert-status--ok { color: var(--cert-green); font-weight: 700; }
    .cert-footer {
      max-width: 186mm;
      margin: 14px auto 0;
      padding: 8px 0 12px;
      border-top: 1px solid var(--cert-gray-200);
      font-size: 8pt;
      color: var(--cert-gray-600);
      text-align: center;
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .cert-print-footer {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      width: 100%;
      visibility: hidden;
      pointer-events: none;
    }
    .cert-footer__brand-bar { display: flex; height: 4px; }
    .cert-footer__brand-bar span { flex: 1; }
    .cert-footer__brand-bar span:nth-child(1) { background: var(--cert-blue-900); }
    .cert-footer__brand-bar span:nth-child(2) { background: var(--cert-blue-700); }
    .cert-footer__brand-bar span:nth-child(3) { background: var(--cert-blue-500); }
    .cert-footer__brand-bar span:nth-child(4) { background: var(--cert-blue-accent); }
    .cert-footer__meta {
      padding: 7px 12mm 8px;
      background: var(--cert-blue-900);
      color: #E2E8F0;
      font-size: 7pt;
      line-height: 1.4;
    }
    .cert-footer__meta p { margin: 0; }
    .cert-footer__site { font-size: 7pt; color: #CBD5E1; margin-bottom: 2px; }
    @media print {
      html, body {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
        background: #ffffff;
      }
      .cert-print-running-header {
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 20;
        background: #ffffff;
        border-bottom: 1px solid var(--cert-gray-200);
        padding: 4mm 12mm 3mm;
      }
      .cert-print-running-header__inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }
      .cert-print-running-header__brand {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
      }
      .cert-print-running-header__text { min-width: 0; }
      .cert-print-running-header__bar {
        display: flex;
        height: 2px;
        margin-top: 3px;
      }
      .cert-print-running-header__bar span { flex: 1; }
      .cert-print-running-header__bar span:nth-child(1) { background: var(--cert-blue-900); }
      .cert-print-running-header__bar span:nth-child(2) { background: var(--cert-blue-700); }
      .cert-print-running-header__bar span:nth-child(3) { background: var(--cert-blue-500); }
      .cert-print-running-header__bar span:nth-child(4) { background: var(--cert-blue-accent); }
      .cert-first-header { display: none; }
      .cert-body-content {
        padding-top: var(--cert-running-header-height);
      }
      .cert-print-layout { display: table; width: 100%; }
      .cert-print-layout tfoot { display: table-footer-group; }
      .cert-main { max-width: none; }
      .cert-print-footer {
        visibility: visible;
      }
    }
  `;
}

function buildRunningHeaderHtml(context: ReportHeaderContext): string {
  const criticalSuffix =
    context.critical != null
      ? ` · ${escapeHtml(
          String(context.exportLabels.pdfSummaryCritical || "Erros críticos"),
        )}: ${escapeHtml(String(context.critical))}`
      : "";

  return `
    <div class="cert-print-running-header" aria-hidden="true">
      <div class="cert-print-running-header__inner">
        <div class="cert-print-running-header__brand">
          ${context.logoMarkup.replace('class="cert-logo"', 'class="cert-logo cert-logo--compact"')}
          <div class="cert-print-running-header__text">
            <p class="cert-title cert-title--compact">${escapeHtml(
              String(context.exportLabels.pdfTitle || "Relatório de Análise de Desenho DELPI"),
            )}</p>
            <p class="cert-running-meta">${escapeHtml(
              String(context.exportLabels.pdfSummaryProduct || "Produto"),
            )}: ${escapeHtml(context.productCode)} · ${escapeHtml(
              String(context.exportLabels.pdfSummaryStatus || "Status"),
            )}: ${escapeHtml(context.overall)}${criticalSuffix}</p>
          </div>
        </div>
        <div class="cert-seal cert-seal--compact ${context.sealClass}">${escapeHtml(
          context.overall,
        )}</div>
      </div>
      <div class="cert-print-running-header__bar" aria-hidden="true">
        <span></span><span></span><span></span><span></span>
      </div>
    </div>
  `;
}

function buildFirstPageHeaderHtml(context: ReportHeaderContext): string {
  return `
    <header class="cert-header cert-first-header">
      <div class="cert-header__top">
        <div class="cert-header__brand">
          ${context.logoMarkup}
          <div>
            <h1 class="cert-title">${escapeHtml(
              String(context.exportLabels.pdfTitle || "Relatório de Análise de Desenho DELPI"),
            )}</h1>
            <p class="cert-subtitle">${escapeHtml(
              String(context.exportLabels.pdfSubtitle || "Validação técnica PDF × API DELPI"),
            )}</p>
          </div>
        </div>
        <div class="cert-seal ${context.sealClass}">${escapeHtml(context.overall)}</div>
      </div>
      <div class="cert-header__brand-bar" aria-hidden="true">
        <span></span><span></span><span></span><span></span>
      </div>
    </header>
  `;
}

function buildTableSection(table: DrawingExportTable): string {
  const columns = table.columns ?? [];
  const rows = table.rows ?? [];

  if (!columns.length || !rows.length) {
    return "";
  }

  const header = columns
    .map((column) => `<th>${escapeHtml(String(column.label || column.key || ""))}</th>`)
    .join("");

  const body = rows
    .map((row) => {
      const cells = columns
        .map((column) => {
          const raw = String(row[column.key] ?? "—");
          const lower = raw.toLowerCase();
          let className = "";

          if (column.key === "status") {
            if (lower.includes("erro") || lower.includes("crítico")) {
              className = ' class="cert-status--error"';
            } else if (lower === "ok") {
              className = ' class="cert-status--ok"';
            }
          }

          return `<td${className}>${escapeHtml(raw)}</td>`;
        })
        .join("");

      return `<tr>${cells}</tr>`;
    })
    .join("");

  return `
    <section class="cert-section">
      <h2 class="cert-section__title">${escapeHtml(String(table.title || ""))}</h2>
      <table class="cert-table">
        <thead><tr>${header}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </section>
  `;
}

function buildPrintFooterMeta(productCode: string): string {
  const issuedAt = new Date().toLocaleString("pt-BR");

  return `
    <footer class="cert-print-footer">
      <div class="cert-footer__brand-bar" aria-hidden="true">
        <span></span><span></span><span></span><span></span>
      </div>
      <div class="cert-footer__meta">
        <p class="cert-footer__site">www.delpi.com.br</p>
        <p><strong>Produto:</strong> ${escapeHtml(productCode)} · <strong>Emitido em:</strong> ${escapeHtml(
          issuedAt,
        )} · Gerado pelo Minha DELPI</p>
      </div>
    </footer>
  `;
}

export function buildDrawingAnalysisReportHtml(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
  logoUrl?: string,
): string {
  const exportLabels = exportPayload.exportLabels ?? {};
  const tables = exportPayload.tables ?? [];
  const productCode = String(drawingAnalysis?.productCode || "—");
  const overall = String(drawingAnalysis?.overallLabel ?? "—");
  const critical = drawingAnalysis?.criticalErrors;
  const sealClass = resolveSealClass(drawingAnalysis);
  const logoMarkup = logoUrl
    ? `<img class="cert-logo" src="${escapeHtml(logoUrl)}" alt="DELPI Conexões Elétricas" />`
    : "";
  const headerContext: ReportHeaderContext = {
    exportLabels,
    productCode,
    overall,
    critical,
    sealClass,
    logoMarkup,
  };
  const sections = tables.map(buildTableSection).join("");
  const criticalBlock =
    critical != null
      ? `<p class="cert-info-line"><strong>${escapeHtml(
          String(exportLabels.pdfSummaryCritical || "Erros críticos"),
        )}</strong>${escapeHtml(String(critical))}</p>`
      : "";

  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(String(exportLabels.pdfTitle || "Relatório de Análise de Desenho DELPI"))}</title>
    <style>${buildDrawingReportStyles()}</style>
  </head>
  <body>
    ${buildRunningHeaderHtml(headerContext)}
    <table class="cert-print-layout">
      <tbody>
        <tr>
          <td>
            <div class="cert-main cert-body-content">
              ${buildFirstPageHeaderHtml(headerContext)}

              <div class="cert-summary">
                <div class="cert-summary__grid">
                  <p class="cert-info-line"><strong>${escapeHtml(
                    String(exportLabels.pdfSummaryProduct || "Produto"),
                  )}</strong>${escapeHtml(productCode)}</p>
                  <p class="cert-info-line"><strong>${escapeHtml(
                    String(exportLabels.pdfSummaryStatus || "Status geral"),
                  )}</strong>${escapeHtml(overall)}</p>
                  ${criticalBlock}
                </div>
              </div>

              ${sections}

              <footer class="cert-footer">
                <p>${escapeHtml(
                  String(
                    exportLabels.pdfFooterNote ||
                      "Relatório gerado eletronicamente pelo Minha DELPI.",
                  ),
                )}</p>
              </footer>
            </div>
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td>
            <div class="cert-print-footer-spacer" aria-hidden="true"></div>
          </td>
        </tr>
      </tfoot>
    </table>

    ${buildPrintFooterMeta(productCode)}
  </body>
</html>`;
}

function waitForImagesThenPrint(targetWindow: Window, onDone?: () => void): void {
  const doc = targetWindow.document;
  const images = Array.from(doc.images);

  const runPrint = () => {
    targetWindow.focus();
    targetWindow.scrollTo(0, 0);
    targetWindow.print();
    onDone?.();
  };

  if (images.length === 0) {
    window.setTimeout(runPrint, 100);
    return;
  }

  let ready = 0;

  const tryPrint = () => {
    ready += 1;

    if (ready >= images.length) {
      window.setTimeout(runPrint, 150);
    }
  };

  for (const image of images) {
    if (image.complete) {
      tryPrint();
    } else {
      image.addEventListener("load", tryPrint, { once: true });
      image.addEventListener("error", tryPrint, { once: true });
    }
  }

  window.setTimeout(runPrint, 1_500);
}

function scheduleDrawingReportPrint(targetWindow: Window, onDone?: () => void): void {
  let started = false;

  const triggerPrint = () => {
    if (started || targetWindow.closed) {
      return;
    }

    started = true;
    waitForImagesThenPrint(targetWindow, onDone);
  };

  targetWindow.addEventListener("load", triggerPrint, { once: true });
  window.setTimeout(triggerPrint, 1_000);
}

function printViaIframe(html: string, onDone?: () => void): boolean {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("title", "Relatório de análise de desenho");
  iframe.setAttribute(
    "style",
    [
      "position:fixed",
      "inset:0",
      "width:100%",
      "height:100%",
      "border:0",
      "z-index:99999",
      "background:#ffffff",
    ].join(";"),
  );
  document.body.appendChild(iframe);

  const targetWindow = iframe.contentWindow;
  const doc = iframe.contentDocument ?? targetWindow?.document;

  if (!targetWindow || !doc) {
    iframe.remove();
    return false;
  }

  doc.open();
  doc.write(html);
  doc.close();

  scheduleDrawingReportPrint(targetWindow, () => {
    window.setTimeout(() => {
      iframe.remove();
      onDone?.();
    }, 1_000);
  });

  return true;
}

export function printDrawingAnalysisReport(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): boolean {
  const logoUrl =
    typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : undefined;
  const html = buildDrawingAnalysisReportHtml(exportPayload, drawingAnalysis, logoUrl);
  const printWindow = window.open("", "_blank");

  if (printWindow) {
    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
    scheduleDrawingReportPrint(printWindow);
    return true;
  }

  return printViaIframe(html);
}
