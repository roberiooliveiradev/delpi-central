import {
  buildDelpiCableLabelDocumentHtml,
  buildDelpiCableLabelLabeledCodeHtml,
  printDelpiDocumentHtml,
  resolveDelpiCableLabelCustomerValue,
} from "@delpi/plugin-ui/index";

import { getCertificate } from "../api/qualityLabelsApi";
import type { Certificate, QualityLabel } from "../types/qualityLabels";

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

async function loadCertificateForPrint(labelId: string): Promise<Certificate | null> {
  try {
    return await getCertificate(labelId);
  } catch {
    return null;
  }
}

function buildLabelHtml(
  label: QualityLabel,
  qrDataUrl: string,
  certificate: Certificate | null,
): string {
  const topLabel = RESULT_LABELS[label.result] ?? "QUALIDADE";
  const productCode = label.productCode;
  const op = escapeHtml(label.productionOrder);
  const date = escapeHtml(formatDate(label.inspectedAt));
  const customerValue = resolveDelpiCableLabelCustomerValue({
    customerItem: certificate?.customerItem ?? label.customerItem,
    customerItemRev: certificate?.customerItemRev ?? label.customerItemRev,
    customerReference: label.customerReference,
  });
  const customerHtml = buildDelpiCableLabelLabeledCodeHtml(
    "customer",
    "CLIENTE",
    customerValue,
  );
  const productHtml = buildDelpiCableLabelLabeledCodeHtml(
    "product",
    "DELPI",
    productCode,
  );
  return buildDelpiCableLabelDocumentHtml({
    title: `Etiqueta da Qualidade — ${escapeHtml(productCode)}`,
    qrDataUrl,
    qrAlt: "QR code da inspeção",
    caption: "",
    qrFooterHtml: `${customerHtml}<div class="tag__meta">OP ${op} · ${date}</div>`,
    sealTopLabel: topLabel,
    brandFooterHtml: productHtml,
    hintHtml:
      "Recorte na linha externa e dobre na faixa central em volta do cabo: o QR (frente) mostra a referência do cliente; nome e código do desenho aparecem ao ler o QR. O verso traz a marca, o selo e o código Delpi.",
  });
}

/** Monta e envia para impressão a etiqueta do cabo (QR + marca + selo). */
export async function printQualityLabel(label: QualityLabel, qrBlob: Blob): Promise<void> {
  const [qrDataUrl, certificate] = await Promise.all([
    blobToDataUrl(qrBlob),
    loadCertificateForPrint(label.id),
  ]);
  const html = buildLabelHtml(label, qrDataUrl, certificate);
  if (printDelpiDocumentHtml(html, { iframeTitle: "Etiqueta da Qualidade" })) {
    return;
  }
  throw new Error(
    "Não foi possível abrir a impressão. Verifique se o navegador não bloqueou pop-ups.",
  );
}
