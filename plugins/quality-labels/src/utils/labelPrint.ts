import {
  buildDelpiCableLabelBrandPanelHtml,
  buildDelpiCableLabelStyles,
  buildDelpiQualitySealSvg,
} from "@delpi/plugin-ui/index";

import type { QualityLabel } from "../types/qualityLabels";

const RESULT_LABELS: Record<string, string> = {
  approved: "APROVADO",
  rejected: "REPROVADO",
  conditional: "CONDICIONAL",
};

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

function formatDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("pt-BR");
}

function buildLabelStyles(): string {
  return buildDelpiCableLabelStyles({
    extraCss: `
    .tag__product {
      font-size: 7.5pt;
      font-weight: 900;
      color: #000000;
      line-height: 1.05;
      letter-spacing: 0.2px;
    }
    .tag__meta {
      font-size: 5pt;
      font-weight: 700;
      color: #1f2937;
      line-height: 1.2;
    }
    `,
  });
}

function buildLabelHtml(label: QualityLabel, qrDataUrl: string): string {
  const topLabel = RESULT_LABELS[label.result] ?? "QUALIDADE";
  const productCode = escapeHtml(label.productCode);
  const op = escapeHtml(label.productionOrder);
  const date = escapeHtml(formatDate(label.inspectedAt));
  const brandPanel = buildDelpiCableLabelBrandPanelHtml(
    buildDelpiQualitySealSvg(topLabel),
    { footerHtml: `<div class="tag__product">${productCode}</div>` },
  );
  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>Etiqueta da Qualidade — ${productCode}</title>
    <style>${buildLabelStyles()}</style>
  </head>
  <body>
    <div class="tag">
      <div class="tag__panel tag__qr">
        <img src="${qrDataUrl}" alt="QR code da inspeção" />
        <div class="tag__caption">Aponte a câmera do celular</div>
        <div class="tag__meta">OP ${op} · ${date}</div>
      </div>
      <div class="tag__fold" aria-hidden="true"></div>
      ${brandPanel}
    </div>
    <p class="hint">
      Recorte na linha externa e dobre na faixa central em volta do cabo:
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
  iframe.setAttribute("title", "Etiqueta da Qualidade");
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

/** Monta e envia para impressão a etiqueta do cabo (QR + marca + selo). */
export async function printQualityLabel(label: QualityLabel, qrBlob: Blob): Promise<void> {
  const qrDataUrl = await blobToDataUrl(qrBlob);
  const html = buildLabelHtml(label, qrDataUrl);
  if (printViaIframe(html) || printViaWindow(html)) {
    return;
  }
  throw new Error(
    "Não foi possível abrir a impressão. Verifique se o navegador não bloqueou pop-ups.",
  );
}
