/** Export PNG do slide (4E.5) — html-to-image, padrão do monorepo. */

export type ExportSlideCaptureOptions = {
  pixelRatio?: number;
  backgroundColor?: string;
};

export type ExportSlidePngOptions = ExportSlideCaptureOptions & {
  fileName?: string;
};

function downloadDataUrl(dataUrl: string, fileName: string) {
  const link = document.createElement("a");
  link.download = fileName;
  link.href = dataUrl;
  link.click();
}

function shouldSkipNode(node: HTMLElement): boolean {
  if (node.classList?.contains("td-composer__stage-grid")) return true;
  if (node.classList?.contains("td-composer__stage-guide")) return true;
  if (node.classList?.contains("td-composer__marquee")) return true;
  if (node.classList?.contains("td-composer__block-handles")) return true;
  if (node.classList?.contains("td-deck-stage__rulers")) return true;
  if (node.getAttribute?.("data-export-ignore") != null) return true;
  return false;
}

/** Captura o elemento do palco como data URL PNG (sem download). */
export async function captureSlideElementToPngDataUrl(
  element: HTMLElement,
  options: ExportSlideCaptureOptions = {},
): Promise<string> {
  const { toPng } = await import("html-to-image");
  return toPng(element, {
    cacheBust: true,
    pixelRatio: options.pixelRatio ?? 2,
    backgroundColor: options.backgroundColor ?? "#ffffff",
    filter: (node) => {
      if (!(node instanceof HTMLElement)) return true;
      return !shouldSkipNode(node);
    },
  });
}

export async function exportSlideElementToPng(
  element: HTMLElement,
  options: ExportSlidePngOptions = {},
): Promise<string> {
  const dataUrl = await captureSlideElementToPngDataUrl(element, options);
  const fileName = options.fileName ?? `slide-${Date.now()}.png`;
  downloadDataUrl(dataUrl, fileName);
  return dataUrl;
}

export type ExportSlidePdfOptions = ExportSlideCaptureOptions & {
  fileName?: string;
  /** Landscape 16:9 (padrão TV) ou portrait. */
  orientation?: "landscape" | "portrait";
};

/** Export PDF de uma página com a captura PNG do slide. */
export async function exportSlideElementToPdf(
  element: HTMLElement,
  options: ExportSlidePdfOptions = {},
): Promise<string> {
  const dataUrl = await captureSlideElementToPngDataUrl(element, options);
  const { jsPDF } = await import("jspdf");
  const orientation = options.orientation ?? "landscape";
  const pdf = new jsPDF({
    orientation,
    unit: "mm",
    format: "a4",
  });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 8;
  const maxW = pageWidth - margin * 2;
  const maxH = pageHeight - margin * 2;
  // 16:9 fit
  const ratio = 16 / 9;
  let drawW = maxW;
  let drawH = drawW / ratio;
  if (drawH > maxH) {
    drawH = maxH;
    drawW = drawH * ratio;
  }
  const x = (pageWidth - drawW) / 2;
  const y = (pageHeight - drawH) / 2;
  pdf.addImage(dataUrl, "PNG", x, y, drawW, drawH);
  const fileName = options.fileName ?? `slide-${Date.now()}.pdf`;
  pdf.save(fileName);
  return dataUrl;
}

export function resolveSlideExportTarget(root: ParentNode | null | undefined): HTMLElement | null {
  if (!root) return null;
  const canvas = root.querySelector<HTMLElement>(".td-composer__canvas");
  if (canvas) return canvas;
  const preview = root.querySelector<HTMLElement>(".tdp-comunicado, .td-deck-stage__canvas, .tdp-native-screen");
  return preview;
}
