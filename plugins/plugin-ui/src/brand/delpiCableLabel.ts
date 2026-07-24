import { DELPI_LOGO_MARK_SVG } from "./delpiLogoMark";

export { DELPI_LOGO_MARK_SVG };

/** Selo circular Aprovado/Qualidade (SVG) para etiquetas 100×30 mm. */
export function buildDelpiQualitySealSvg(topLabel: string): string {
  const safe = topLabel.replace(/[<>&"]/g, "");
  const topSize = safe.length > 9 ? 16 : 20;
  return `
<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Selo ${safe} Qualidade">
  <circle cx="70" cy="70" r="66" fill="#ffffff" stroke="#000000" stroke-width="3.5" />
  <circle cx="70" cy="70" r="57" fill="none" stroke="#000000" stroke-width="1.25" />
  <g transform="translate(47,14) scale(1.75)" fill="#000000">
    <path d="M2 21h4V9H2v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
  </g>
  <text x="70" y="94" text-anchor="middle" font-family="Arial Black, Arial, Helvetica, sans-serif" font-weight="900" font-size="${topSize}" fill="#000000" letter-spacing="0.4">${safe}</text>
  <text x="70" y="114" text-anchor="middle" font-family="Arial Black, Arial, Helvetica, sans-serif" font-weight="900" font-size="13.5" fill="#000000" letter-spacing="1.2">QUALIDADE</text>
</svg>`;
}

/**
 * CSS canônico da etiqueta cabo/chicote 100×30 mm.
 * Única fonte de verdade — MFEs não devem embutir CSS de etiqueta.
 */
export function buildDelpiCableLabelStyles(): string {
  return `
    @page { size: 100mm 30mm; margin: 0; }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: #013866;
      background: #ffffff;
    }
    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      padding: 4mm;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .tag {
      display: flex;
      align-items: stretch;
      justify-content: space-between;
      box-sizing: border-box;
      width: 100mm;
      height: 30mm;
      padding: 1.2mm 7mm;
      border: 0.3mm dashed #9fb1c1;
      overflow: hidden;
      background: #ffffff;
    }
    .tag__panel {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.35mm;
      padding: 0;
      width: auto;
      max-width: 36mm;
      text-align: center;
    }
    .tag__qr img {
      width: 18mm;
      height: 18mm;
      display: block;
    }
    .tag__caption {
      font-size: 5.5pt;
      font-weight: 800;
      color: #013247;
      line-height: 1.15;
      max-width: 36mm;
    }
    .tag__name {
      font-size: 5pt;
      font-weight: 800;
      color: #000000;
      line-height: 1.15;
      max-width: 36mm;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .tag__meta {
      font-size: 5pt;
      font-weight: 700;
      color: #1f2937;
      line-height: 1.2;
    }
    .tag__product {
      font-size: 7.5pt;
      font-weight: 900;
      color: #000000;
      line-height: 1.05;
      letter-spacing: 0.2px;
    }
    .tag__fold {
      width: 8mm;
      flex: 0 0 8mm;
    }
    .tag__logo {
      width: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .tag__logo svg {
      width: 16mm;
      max-width: 100%;
      height: auto;
      display: block;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .tag__logo svg path,
    .tag__logo svg rect {
      fill: #000000 !important;
    }
    .tag__seal svg {
      width: 15mm;
      height: 15mm;
      display: block;
    }
    .hint {
      margin-top: 4mm;
      font-size: 8pt;
      color: #64748b;
      text-align: center;
      max-width: 100mm;
    }
    @media print {
      html, body {
        width: 100mm;
        height: 30mm;
        padding: 0;
        margin: 0;
        display: block;
        overflow: hidden;
      }
      .tag {
        border: none;
        box-sizing: border-box;
        width: 100mm;
        height: 30mm;
        padding: 1.2mm 7mm;
      }
      .hint { display: none; }
    }
  `;
}

/** Painel da marca (logo + selo [+ rodapé opcional]) — markup HTML compartilhado. */
export function buildDelpiCableLabelBrandPanelHtml(
  sealSvg: string,
  options: { footerHtml?: string } = {},
): string {
  const footer = options.footerHtml?.trim()
    ? `\n        ${options.footerHtml.trim()}`
    : "";
  return `
      <div class="tag__panel tag__brand">
        <div class="tag__logo">${DELPI_LOGO_MARK_SVG}</div>
        <div class="tag__seal">${sealSvg}</div>${footer}
      </div>`;
}

export type DelpiCableLabelDocumentOptions = {
  title: string;
  qrDataUrl: string;
  qrAlt: string;
  /** Conteúdo abaixo da legenda (ex.: nome ou OP · data) — HTML já escapado. */
  qrFooterHtml: string;
  sealTopLabel: string;
  /** Rodapé do painel da marca (ex.: código do produto) — HTML já escapado. */
  brandFooterHtml?: string;
  hintHtml: string;
  caption?: string;
};

/**
 * Documento completo da etiqueta 100×30 mm (CSS + markup).
 * MFEs só passam dados — sem CSS local de etiqueta.
 */
export function buildDelpiCableLabelDocumentHtml(
  options: DelpiCableLabelDocumentOptions,
): string {
  const caption = options.caption?.trim() || "Aponte a câmera do celular";
  const brandPanel = buildDelpiCableLabelBrandPanelHtml(
    buildDelpiQualitySealSvg(options.sealTopLabel),
    options.brandFooterHtml
      ? { footerHtml: options.brandFooterHtml }
      : undefined,
  );
  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>${options.title}</title>
    <style>${buildDelpiCableLabelStyles()}</style>
  </head>
  <body>
    <div class="tag">
      <div class="tag__panel tag__qr">
        <img src="${options.qrDataUrl}" alt="${options.qrAlt}" />
        <div class="tag__caption">${caption}</div>
        ${options.qrFooterHtml}
      </div>
      <div class="tag__fold" aria-hidden="true"></div>
      ${brandPanel}
    </div>
    <p class="hint">${options.hintHtml}</p>
  </body>
</html>`;
}
