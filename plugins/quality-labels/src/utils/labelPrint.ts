import {
  buildDelpiCableLabelDocumentHtml,
  printDelpiDocumentHtml,
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

function buildLabelHtml(label: QualityLabel, qrDataUrl: string): string {
  const topLabel = RESULT_LABELS[label.result] ?? "QUALIDADE";
  const productCode = escapeHtml(label.productCode);
  const op = escapeHtml(label.productionOrder);
  const date = escapeHtml(formatDate(label.inspectedAt));
  return buildDelpiCableLabelDocumentHtml({
    title: `Etiqueta da Qualidade — ${productCode}`,
    qrDataUrl,
    qrAlt: "QR code da inspeção",
    qrFooterHtml: `<div class="tag__meta">OP ${op} · ${date}</div>`,
    sealTopLabel: topLabel,
    brandFooterHtml: `<div class="tag__product">${productCode}</div>`,
    hintHtml:
      "Recorte na linha externa e dobre na faixa central em volta do cabo: o QR code fica de um lado (frente) e a marca com o selo de qualidade do outro (verso).",
  });
}

/** Monta e envia para impressão a etiqueta do cabo (QR + marca + selo). */
export async function printQualityLabel(label: QualityLabel, qrBlob: Blob): Promise<void> {
  const qrDataUrl = await blobToDataUrl(qrBlob);
  const html = buildLabelHtml(label, qrDataUrl);
  if (printDelpiDocumentHtml(html, { iframeTitle: "Etiqueta da Qualidade" })) {
    return;
  }
  throw new Error(
    "Não foi possível abrir a impressão. Verifique se o navegador não bloqueou pop-ups.",
  );
}
