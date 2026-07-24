import type { Participant } from "../types";
import delpiLogoSvg from "../assets/logoDelpi.svg?raw";

export type PrintResult = { success: boolean; error?: string };

/**
 * Wordmark Delpi sem o slogan "Conexões Elétricas".
 * Sanitiza o asset (mesmo legado com tagline) na hora da impressão.
 */
function delpiLogoMarkSvg(raw: string): string {
  return raw
    .replace(/<path[^>]*d="M25\.168 516\.792[\s\S]*?<\/path>\s*/g, "")
    .replace(/\bheight="547"\b/, 'height="440"')
    .replace(/\bviewBox="0 0 832 547"\b/, 'viewBox="0 0 832 440"');
}

const DELPI_LOGO_MARK_SVG = delpiLogoMarkSvg(delpiLogoSvg);

/**
 * Selo "Aprovado Qualidade" recriado em SVG (não há asset oficial no repo).
 * Troque este markup se a marca fornecer o selo definitivo.
 */
const QUALITY_SEAL_SVG = `
<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Selo Aprovado Qualidade">
  <circle cx="70" cy="70" r="66" fill="#ffffff" stroke="#000000" stroke-width="3.5" />
  <circle cx="70" cy="70" r="57" fill="none" stroke="#000000" stroke-width="1.25" />
  <g transform="translate(47,14) scale(1.75)" fill="#000000">
    <path d="M2 21h4V9H2v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
  </g>
  <text x="70" y="94" text-anchor="middle" font-family="Arial Black, Arial, Helvetica, sans-serif" font-weight="900" font-size="20" fill="#000000" letter-spacing="0.4">APROVADO</text>
  <text x="70" y="114" text-anchor="middle" font-family="Arial Black, Arial, Helvetica, sans-serif" font-weight="900" font-size="13.5" fill="#000000" letter-spacing="1.2">QUALIDADE</text>
</svg>`;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Falha ao ler a imagem do QR code."));
    reader.readAsDataURL(blob);
  });
}

function buildLabelStyles(): string {
  // Etiqueta no padrão da impressora: 100mm x 30mm.
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
      /* Padding lateral explícito — conteúdo afastado das bordas da mídia */
      padding: 1.2mm 5.5mm;
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
      max-width: 38mm;
      text-align: center;
    }
    .tag__qr img {
      width: 19mm;
      height: 19mm;
      display: block;
    }
    .tag__caption {
      font-size: 5.5pt;
      font-weight: 800;
      color: #013247;
      line-height: 1.15;
      max-width: 44mm;
    }
    .tag__name {
      font-size: 5pt;
      font-weight: 800;
      color: #000000;
      line-height: 1.15;
      max-width: 44mm;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    /* Zona central: espaço de dobra em volta do chicote (frente x verso) */
    .tag__fold {
      width: 8mm;
    }
    .tag__logo {
      width: 100%;
      max-height: 7mm;
      overflow: hidden;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }
    .tag__logo svg {
      width: 16mm;
      max-width: 100%;
      height: auto;
      display: block;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    /* Etiqueta monocromática: logo Delpi em preto */
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
    /* Impressão: só a etiqueta ocupa a mídia 100x30. */
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
        padding: 1.2mm 5.5mm;
      }
      .hint { display: none; }
    }
  `;
}

function buildLabelHtml(participant: Participant, qrDataUrl: string): string {
  const name = escapeHtml(participant.fullName);
  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>Etiqueta QR — ${name}</title>
    <style>${buildLabelStyles()}</style>
  </head>
  <body>
    <div class="tag">
      <div class="tag__panel tag__qr">
        <img src="${qrDataUrl}" alt="QR code de agradecimento" />
        <div class="tag__caption">Aponte a câmera do celular</div>
        <div class="tag__name">${name}</div>
      </div>
      <div class="tag__fold" aria-hidden="true"></div>
      <div class="tag__panel tag__brand">
        <div class="tag__logo">${DELPI_LOGO_MARK_SVG}</div>
        <div class="tag__seal">${QUALITY_SEAL_SVG}</div>
      </div>
    </div>
    <p class="hint">
      Recorte na linha externa e dobre na faixa central em volta do chicote:
      o QR code fica de um lado (frente) e a marca com o selo de qualidade do outro (verso).
    </p>
  </body>
</html>`;
}

function waitForImagesThenPrint(targetWindow: Window, onDone?: () => void): void {
  const images = Array.from(targetWindow.document.images);
  const runPrint = () => {
    targetWindow.focus();
    targetWindow.print();
    onDone?.();
  };
  if (images.length === 0) {
    window.setTimeout(runPrint, 120);
    return;
  }
  let ready = 0;
  const tryPrint = () => {
    ready += 1;
    if (ready >= images.length) window.setTimeout(runPrint, 150);
  };
  for (const image of images) {
    if (image.complete) tryPrint();
    else {
      image.addEventListener("load", tryPrint, { once: true });
      image.addEventListener("error", tryPrint, { once: true });
    }
  }
  window.setTimeout(runPrint, 1500);
}

function schedulePrint(targetWindow: Window, onDone?: () => void): void {
  let started = false;
  const trigger = () => {
    if (started || targetWindow.closed) return;
    started = true;
    waitForImagesThenPrint(targetWindow, onDone);
  };
  targetWindow.addEventListener("load", trigger, { once: true });
  window.setTimeout(trigger, 800);
}

function printViaWindow(html: string): boolean {
  const printWindow = window.open("", "_blank");
  if (!printWindow) return false;
  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  schedulePrint(printWindow);
  return true;
}

function printViaIframe(html: string): boolean {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("title", "Etiqueta QR");
  iframe.setAttribute(
    "style",
    ["position:fixed", "inset:0", "width:100%", "height:100%", "border:0", "z-index:99999", "background:#fff"].join(";"),
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
  schedulePrint(targetWindow, () => window.setTimeout(() => iframe.remove(), 1000));
  return true;
}

/** Monta e envia para impressão a etiqueta do chicote (QR + marca + selo). */
export async function printQrLabel(participant: Participant, qrBlob: Blob): Promise<PrintResult> {
  try {
    const qrDataUrl = await blobToDataUrl(qrBlob);
    const html = buildLabelHtml(participant, qrDataUrl);
    // iframe primeiro: imprime no contexto atual, sem abrir aba "about:blank".
    if (printViaIframe(html) || printViaWindow(html)) {
      return { success: true };
    }
    return {
      success: false,
      error: "Não foi possível abrir a impressão. Verifique se o navegador não bloqueou pop-ups.",
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Erro ao gerar a etiqueta." };
  }
}
