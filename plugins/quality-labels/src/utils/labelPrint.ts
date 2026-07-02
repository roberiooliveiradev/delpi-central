import type { QualityLabel } from "../types/qualityLabels";

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
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

function formatDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("pt-BR");
}

const RESULT_LABELS: Record<string, string> = {
  approved: "APROVADO",
  rejected: "REPROVADO",
  conditional: "CONDICIONAL",
};

function buildStyles(): string {
  return `
    @page { size: 90mm 50mm; margin: 0; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, Helvetica, sans-serif; color: #000; }
    .ql-label {
      width: 90mm; height: 50mm; padding: 4mm;
      display: flex; gap: 4mm; align-items: center;
      border: 0.3mm dashed #999;
    }
    .ql-label__qr { width: 34mm; height: 34mm; flex: 0 0 auto; }
    .ql-label__qr img { width: 100%; height: 100%; }
    .ql-label__info { flex: 1; min-width: 0; }
    .ql-label__seal {
      display: inline-block; padding: 1mm 3mm; border: 0.4mm solid #000;
      border-radius: 2mm; font-size: 3.4mm; font-weight: 800; letter-spacing: 0.4mm;
      margin-bottom: 2mm;
    }
    .ql-label__product { font-size: 4mm; font-weight: 800; margin: 0 0 1mm; }
    .ql-label__desc { font-size: 3mm; margin: 0 0 2mm; line-height: 1.25; }
    .ql-label__row { font-size: 2.8mm; margin: 0.5mm 0; }
    .ql-label__row b { font-weight: 700; }
  `;
}

function buildHtml(label: QualityLabel, qrDataUrl: string): string {
  const seal = RESULT_LABELS[label.result] ?? "QUALIDADE";
  return `
    <div class="ql-label">
      <div class="ql-label__qr"><img src="${qrDataUrl}" alt="QR" /></div>
      <div class="ql-label__info">
        <span class="ql-label__seal">${escapeHtml(seal)} · QUALIDADE</span>
        <p class="ql-label__product">${escapeHtml(label.productCode)}</p>
        <p class="ql-label__desc">${escapeHtml(label.productDescription)}</p>
        <p class="ql-label__row"><b>OP:</b> ${escapeHtml(label.productionOrder)}</p>
        <p class="ql-label__row"><b>Inspeção:</b> ${escapeHtml(formatDate(label.inspectedAt))}</p>
        <p class="ql-label__row"><b>Inspetor:</b> ${escapeHtml(label.inspectorName)}</p>
      </div>
    </div>
  `;
}

export async function printQualityLabel(label: QualityLabel, qrBlob: Blob): Promise<void> {
  const qrDataUrl = await blobToDataUrl(qrBlob);
  const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8" />
    <title>Etiqueta ${escapeHtml(label.productCode)}</title>
    <style>${buildStyles()}</style></head>
    <body>${buildHtml(label, qrDataUrl)}</body></html>`;

  const iframe = document.createElement("iframe");
  iframe.style.position = "fixed";
  iframe.style.right = "0";
  iframe.style.bottom = "0";
  iframe.style.width = "0";
  iframe.style.height = "0";
  iframe.style.border = "0";
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow?.document;
  if (!doc) {
    document.body.removeChild(iframe);
    return;
  }

  doc.open();
  doc.write(html);
  doc.close();

  const trigger = () => {
    iframe.contentWindow?.focus();
    iframe.contentWindow?.print();
    window.setTimeout(() => {
      document.body.removeChild(iframe);
    }, 1000);
  };

  const img = doc.querySelector("img");
  if (img && !img.complete) {
    img.addEventListener("load", () => window.setTimeout(trigger, 100));
    img.addEventListener("error", () => window.setTimeout(trigger, 100));
  } else {
    window.setTimeout(trigger, 200);
  }
}
