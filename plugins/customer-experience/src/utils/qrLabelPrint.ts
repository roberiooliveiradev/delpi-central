import {
  buildDelpiCableLabelDocumentHtml,
  printDelpiDocumentHtml,
} from "@delpi/plugin-ui/index";

import type { Participant } from "../types";

export type PrintResult = { success: boolean; error?: string };

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

function buildLabelHtml(participant: Participant, qrDataUrl: string): string {
  const name = escapeHtml(participant.fullName);
  return buildDelpiCableLabelDocumentHtml({
    title: `Etiqueta QR — ${name}`,
    qrDataUrl,
    qrAlt: "QR code de agradecimento",
    qrFooterHtml: `<div class="tag__name">${name}</div>`,
    sealTopLabel: "APROVADO",
    hintHtml:
      "Recorte na linha externa e dobre na faixa central em volta do chicote: o QR code fica de um lado (frente) e a marca com o selo de qualidade do outro (verso).",
  });
}

/** Monta e envia para impressão a etiqueta do chicote (QR + marca + selo). */
export async function printQrLabel(participant: Participant, qrBlob: Blob): Promise<PrintResult> {
  try {
    const qrDataUrl = await blobToDataUrl(qrBlob);
    const html = buildLabelHtml(participant, qrDataUrl);
    if (printDelpiDocumentHtml(html, { iframeTitle: "Etiqueta QR" })) {
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
