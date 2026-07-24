import {
  buildDelpiCableLabelBrandPanelHtml,
  buildDelpiCableLabelStyles,
  buildDelpiQualitySealSvg,
} from "@delpi/plugin-ui/index";

import type { Participant } from "../types";

export type PrintResult = { success: boolean; error?: string };

const QUALITY_SEAL_SVG = buildDelpiQualitySealSvg("APROVADO");

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
  return buildDelpiCableLabelStyles({
    extraCss: `
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
    `,
  });
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
      ${buildDelpiCableLabelBrandPanelHtml(QUALITY_SEAL_SVG)}
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
