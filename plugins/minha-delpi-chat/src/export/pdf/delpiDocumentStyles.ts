/** Estilos compartilhados do documento certificado DELPI (impressão / PDF). */
export function buildDelpiDocumentStyles(): string {
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
    .cert-table--dense th,
    .cert-table--dense td {
      padding: 2px 4px;
      line-height: 1.25;
      font-size: 7.5pt;
    }
    .cert-table--dense th {
      font-size: 6.5pt;
      letter-spacing: 0.03em;
    }
    .cert-table--inspection th,
    .cert-table--inspection td {
      font-size: 7pt;
    }
    .cert-cell--nowrap {
      white-space: nowrap;
    }
    .cert-cell--numeric {
      text-align: center;
      vertical-align: top;
    }
    .cert-cell--wrap {
      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
      hyphens: auto;
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
      break-inside: auto;
      page-break-inside: auto;
    }
    .cert-table tbody tr:nth-child(even) td { background: var(--cert-gray-50); }
    .cert-status--error { color: var(--cert-red); font-weight: 700; }
    .cert-status--ok { color: var(--cert-green); font-weight: 700; }
    .cert-chart-image {
      display: block;
      max-width: 100%;
      height: auto;
      margin: 0 auto;
      border: 1px solid var(--cert-gray-200);
      border-radius: 4px;
    }
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

export function buildDelpiBrandBarHtml(className: string): string {
  return `
    <div class="${className}" aria-hidden="true">
      <span></span><span></span><span></span><span></span>
    </div>
  `;
}
