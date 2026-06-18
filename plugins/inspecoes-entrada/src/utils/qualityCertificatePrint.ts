import type { InspecoesEntradaHistoricoDetalhe } from "../types/inspecoesEntradaHistoricoDetalhe";
import {
  collectCertificateInspectorNames,
  escapeCertificateHtml,
  formatBranchUnitLabel,
  formatCertificateIssuedAt,
  formatCertificateMeasuredValue,
  formatCertificateMeasurementAt,
  formatCertificateMultiline,
  formatCertificateProductLabel,
  formatCertificateQuantity,
  formatCertificateReceivedAt,
  formatCertificateReportAt,
  formatCertificateSpecification,
  isCertificateFailedTest,
  resolveCertificateSealClass,
} from "./certificateFormat";
import { formatText } from "./format";

export type PrintQualityCertificateResult = {
  success: boolean;
  error?: string;
};

/** Altura reservada no fim de cada página para não sobrepor a faixa azul. */
const PRINT_FOOTER_HEIGHT_MM = 18;

function buildCertificateStyles(): string {
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
      --cert-footer-height: ${PRINT_FOOTER_HEIGHT_MM}mm;
    }
    @page {
      size: A4 portrait;
      margin: 0;
    }
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
      padding: 10mm 12mm 0;
      box-decoration-break: clone;
      -webkit-box-decoration-break: clone;
    }
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
    .cert-print-footer-spacer {
      height: var(--cert-footer-height);
    }
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
      margin-bottom: 0;
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
    .cert-logo {
      width: 88px;
      height: auto;
      flex-shrink: 0;
    }
    .cert-header__titles {
      min-width: 0;
    }
    .cert-title {
      margin: 0;
      font-size: 15pt;
      font-weight: 700;
      color: var(--cert-blue-900);
      line-height: 1.15;
      letter-spacing: -0.01em;
    }
    .cert-subtitle {
      margin: 2px 0 0;
      font-size: 9.5pt;
      font-weight: 600;
      color: var(--cert-gray-600);
      text-transform: uppercase;
      letter-spacing: 0.06em;
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
    .cert-seal--approved {
      border-color: var(--cert-green);
      color: var(--cert-green);
    }
    .cert-seal--rejected {
      border-color: var(--cert-red);
      color: var(--cert-red);
    }
    .cert-seal--neutral {
      border-color: var(--cert-gray-600);
      color: var(--cert-gray-600);
    }
    .cert-header__brand-bar {
      display: flex;
      height: 3px;
      margin: 0 -12px;
      border-radius: 0;
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
      margin-bottom: 10px;
      background: #ffffff;
    }
    .cert-summary__grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 20px;
    }
    .cert-summary__block h2 {
      margin: 0 0 5px;
      font-size: 7.5pt;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--cert-blue-900);
      font-weight: 700;
      border-bottom: 1px solid var(--cert-gray-200);
      padding-bottom: 3px;
    }
    .cert-info-line {
      margin: 0 0 3px;
      font-size: 9pt;
      color: var(--cert-gray-900);
      line-height: 1.35;
    }
    .cert-info-line strong {
      font-weight: 600;
      color: var(--cert-gray-600);
    }
    .cert-supplier-name {
      margin: 0 0 8px;
      font-size: 10pt;
      font-weight: 700;
      color: var(--cert-gray-900);
      line-height: 1.3;
    }
    .cert-product-title {
      margin: 0 0 3px;
      font-size: 9.5pt;
      font-weight: 700;
      color: var(--cert-gray-900);
      line-height: 1.35;
    }
    .cert-product-meta {
      margin: 0;
      font-size: 9pt;
      color: var(--cert-gray-600);
    }
    .cert-section {
      margin-bottom: 10px;
    }
    .cert-section h2 {
      margin: 0 0 6px;
      font-size: 8pt;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--cert-blue-900);
      font-weight: 700;
    }
    .cert-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 8pt;
      table-layout: fixed;
    }
    .cert-table thead {
      display: table-header-group;
    }
    .cert-table th,
    .cert-table td {
      border: 1px solid var(--cert-gray-200);
      padding: 4px 5px;
      vertical-align: middle;
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
    .cert-table tbody tr:nth-child(even) td {
      background: var(--cert-gray-50);
    }
    .cert-table .col-test { width: 20%; }
    .cert-table .col-spec { width: 26%; }
    .cert-table .col-measured { width: 26%; }
    .cert-table .col-datetime { width: 14%; white-space: nowrap; font-size: 7pt; }
    .cert-table .col-result { width: 10%; white-space: nowrap; }
    .cert-row--failed td {
      background: #FEF2F2 !important;
    }
    .cert-result-badge {
      display: inline-block;
      font-weight: 700;
      font-size: 7pt;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .cert-result-badge--failed { color: var(--cert-red); }
    .cert-result-badge--approved { color: var(--cert-green); }
    .cert-cell-pre {
      white-space: pre-line;
      word-break: break-word;
    }
    .cert-footer {
      max-width: 186mm;
      margin: 14px auto 0;
      margin-left: -12mm;
      margin-right: -12mm;
      width: calc(100% + 24mm);
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .cert-footer__content {
      padding: 10px 12mm 8px;
      background: var(--cert-gray-50);
      border-top: 1px solid var(--cert-gray-200);
      font-size: 7.5pt;
      line-height: 1.45;
      color: var(--cert-gray-600);
    }
    .cert-footer__content p {
      margin: 0 0 4px;
    }
    .cert-footer__content ul {
      margin: 3px 0 5px 16px;
      padding: 0;
    }
    .cert-footer__content strong {
      color: var(--cert-gray-900);
      font-weight: 600;
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
    .cert-footer__brand-bar {
      display: flex;
      height: 4px;
    }
    .cert-footer__brand-bar span {
      flex: 1;
    }
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
    .cert-footer__meta p {
      margin: 0;
    }
    .cert-footer__site {
      font-size: 7pt;
      color: #CBD5E1;
      margin-bottom: 2px;
    }
    .cert-footer__meta strong {
      color: #ffffff;
      font-weight: 600;
    }
    @media print {
      html, body {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
        background: #ffffff;
        color: var(--cert-gray-900);
      }
      body {
        padding: 10mm 12mm 0;
        box-decoration-break: clone;
        -webkit-box-decoration-break: clone;
      }
      .cert-print-layout {
        display: table;
        width: 100%;
      }
      .cert-print-layout tfoot {
        display: table-footer-group;
      }
      .cert-main {
        max-width: none;
      }
      .cert-footer {
        margin-left: -12mm;
        margin-right: -12mm;
        width: calc(100% + 24mm);
      }
      .cert-print-footer {
        visibility: visible;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        z-index: 1000;
        margin: 0;
        pointer-events: auto;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
      .cert-header,
      .cert-summary {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
      .cert-table th,
      .cert-header__brand-bar span,
      .cert-footer__brand-bar span,
      .cert-footer__meta {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
      .cert-table tbody tr:nth-child(even) td {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
    }
  `;
}

function buildTestRows(tests: InspecoesEntradaHistoricoDetalhe["tests"]): string {
  if (tests.length === 0) {
    return `<tr><td colspan="5">Nenhum ensaio registrado para esta inspeção.</td></tr>`;
  }

  return tests
    .map((test) => {
      const failed = isCertificateFailedTest(test);
      const resultClass = failed ? "cert-result-badge--failed" : "cert-result-badge--approved";
      const rowClass = failed ? "cert-row--failed" : "";
      const measurementAt = formatCertificateMeasurementAt(test);

      return `
        <tr class="${rowClass}">
          <td class="col-test">${escapeCertificateHtml(formatText(test.test_name))}</td>
          <td class="col-spec cert-cell-pre">${formatCertificateMultiline(formatCertificateSpecification(test))}</td>
          <td class="col-measured cert-cell-pre">${formatCertificateMultiline(formatCertificateMeasuredValue(test))}</td>
          <td class="col-datetime">${escapeCertificateHtml(measurementAt || "—")}</td>
          <td class="col-result"><span class="cert-result-badge ${resultClass}">${escapeCertificateHtml(formatText(test.result))}</span></td>
        </tr>
      `;
    })
    .join("");
}

function buildResponsibleFooter(detail: InspecoesEntradaHistoricoDetalhe): string {
  const names = collectCertificateInspectorNames(detail);

  if (names.length === 0) {
    return "";
  }

  if (names.length === 1) {
    return `<p><strong>Responsável técnico informado no Protheus:</strong> ${escapeCertificateHtml(names[0])}</p>`;
  }

  const items = names.map((name) => `<li>${escapeCertificateHtml(name)}</li>`).join("");
  return `<p><strong>Responsáveis técnicos informados no Protheus:</strong></p><ul>${items}</ul>`;
}

function buildIdentificationBlock(detail: InspecoesEntradaHistoricoDetalhe): string {
  const { summary, branch } = detail;
  const receivedAt = formatCertificateReceivedAt(summary);
  const reportAt = formatCertificateReportAt(summary);
  const inspectorName = formatText(summary.inspector_name);
  const nfParts = [
    summary.invoice_number?.trim() ?? "",
    summary.invoice_series?.trim() ? `Série: ${summary.invoice_series.trim()}` : "",
    summary.invoice_item?.trim() ? `Item: ${summary.invoice_item.trim()}` : "",
  ].filter(Boolean);
  const nfLine = nfParts.join(" · ");

  const lines = [
    `<p class="cert-info-line"><strong>Unidade:</strong> ${escapeCertificateHtml(formatBranchUnitLabel(branch))}</p>`,
    nfLine ? `<p class="cert-info-line"><strong>NF:</strong> ${escapeCertificateHtml(nfLine)}</p>` : "",
    receivedAt
      ? `<p class="cert-info-line"><strong>Entrada:</strong> ${escapeCertificateHtml(receivedAt)}</p>`
      : "",
    reportAt ? `<p class="cert-info-line"><strong>Laudo:</strong> ${escapeCertificateHtml(reportAt)}</p>` : "",
    inspectorName !== "—"
      ? `<p class="cert-info-line"><strong>Ensaiador:</strong> ${escapeCertificateHtml(inspectorName)}</p>`
      : "",
  ].filter(Boolean);

  return lines.join("\n");
}

function buildSummaryBlock(detail: InspecoesEntradaHistoricoDetalhe): string {
  const { summary } = detail;
  const lot = summary.lot?.trim();
  const quantity = formatCertificateQuantity(summary);
  const metaParts = [
    lot ? `Lote ${lot}` : "",
    quantity && quantity !== "—" ? `Quantidade ${quantity}` : "",
  ].filter(Boolean);

  return `
    <div class="cert-summary__grid">
      <div class="cert-summary__block">
        <h2>Identificação</h2>
        ${buildIdentificationBlock(detail)}
      </div>
      <div class="cert-summary__block">
        <h2>Fornecedor</h2>
        <p class="cert-supplier-name">${escapeCertificateHtml(formatText(summary.supplier_name))}</p>
        <h2>Produto</h2>
        <p class="cert-product-title">${escapeCertificateHtml(formatCertificateProductLabel(summary))}</p>
        ${metaParts.length > 0 ? `<p class="cert-product-meta">${escapeCertificateHtml(metaParts.join(" · "))}</p>` : ""}
      </div>
    </div>
  `;
}

function buildPrintFooterMeta(issuedAt: string, inspectionId: string): string {
  return `
    <footer class="cert-print-footer">
      <div class="cert-footer__brand-bar" aria-hidden="true">
        <span></span><span></span><span></span><span></span>
      </div>
      <div class="cert-footer__meta">
        <p class="cert-footer__site">www.delpi.com.br</p>
        <p><strong>Emitido em:</strong> ${escapeCertificateHtml(issuedAt)} · <strong>ID:</strong> ${escapeCertificateHtml(inspectionId)} · Gerado pelo Minha DELPI</p>
      </div>
    </footer>
  `;
}

export function buildQualityCertificateHtml(
  detail: InspecoesEntradaHistoricoDetalhe,
  logoUrl?: string,
): string {
  const { summary, tests, inspection_id: inspectionId } = detail;
  const issuedAt = formatCertificateIssuedAt();
  const sealClass = resolveCertificateSealClass(summary.result);
  const logoMarkup = logoUrl
    ? `<img class="cert-logo" src="${escapeCertificateHtml(logoUrl)}" alt="DELPI Conexões Elétricas" />`
    : "";

  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>Certificado de Qualidade — NF ${escapeCertificateHtml(formatText(summary.invoice_number))}</title>
    <style>${buildCertificateStyles()}</style>
  </head>
  <body>
    <table class="cert-print-layout">
      <tbody>
        <tr>
          <td>
            <div class="cert-main">
              <header class="cert-header">
                <div class="cert-header__top">
                  <div class="cert-header__brand">
                    ${logoMarkup}
                    <div class="cert-header__titles">
                      <h1 class="cert-title">Certificado de Qualidade</h1>
                      <p class="cert-subtitle">Inspeção de Recebimento</p>
                    </div>
                  </div>
                  <div class="cert-seal ${sealClass}">
                    ${escapeCertificateHtml(formatText(summary.result))}
                  </div>
                </div>
                <div class="cert-header__brand-bar" aria-hidden="true">
                  <span></span><span></span><span></span><span></span>
                </div>
              </header>

              <div class="cert-summary">
                ${buildSummaryBlock(detail)}
              </div>

              <section class="cert-section">
                <h2>Ensaios e medições</h2>
                <table class="cert-table">
                  <thead>
                    <tr>
                      <th class="col-test">Ensaio</th>
                      <th class="col-spec">Especificação</th>
                      <th class="col-measured">Medido / realizado</th>
                      <th class="col-datetime">Data/Hora</th>
                      <th class="col-result">Resultado</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${buildTestRows(tests)}
                  </tbody>
                </table>
              </section>
            </div>

            <footer class="cert-footer">
              <div class="cert-footer__content">
                <p>Certificado gerado eletronicamente pelo Minha DELPI com base nos dados do Protheus.</p>
                ${buildResponsibleFooter(detail)}
              </div>
            </footer>
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

    ${buildPrintFooterMeta(issuedAt, inspectionId)}
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

function scheduleCertificatePrint(targetWindow: Window, onDone?: () => void): void {
  let started = false;

  const triggerPrint = () => {
    if (started || targetWindow.closed) return;
    started = true;
    waitForImagesThenPrint(targetWindow, onDone);
  };

  targetWindow.addEventListener("load", triggerPrint, { once: true });
  window.setTimeout(triggerPrint, 1_000);
}

function openCertificatePrintWindow(html: string): Window | null {
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    return null;
  }

  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  return printWindow;
}

function printViaPrintFrame(html: string): boolean {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("title", "Certificado de qualidade");
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

  scheduleCertificatePrint(targetWindow, () => {
    window.setTimeout(() => iframe.remove(), 1_000);
  });

  return true;
}

export function printQualityCertificate(detail: InspecoesEntradaHistoricoDetalhe): PrintQualityCertificateResult {
  const logoUrl =
    typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : undefined;
  const html = buildQualityCertificateHtml(detail, logoUrl);

  const printWindow = openCertificatePrintWindow(html);
  if (printWindow) {
    scheduleCertificatePrint(printWindow);
    return { success: true };
  }

  if (printViaPrintFrame(html)) {
    return { success: true };
  }

  return {
    success: false,
    error: "Não foi possível abrir a janela de impressão. Verifique se o navegador não bloqueou pop-ups.",
  };
}
