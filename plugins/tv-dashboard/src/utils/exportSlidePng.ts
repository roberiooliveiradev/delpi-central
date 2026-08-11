/** Export PNG/PDF do slide — html-to-image + jsPDF (aspecto do design). */

import { cssPxToMm, type ViewportPixelSize } from "./viewportPixelSize";

export type ExportSlideCaptureOptions = {
  pixelRatio?: number;
  backgroundColor?: string;
};

export type ExportSlidePngOptions = ExportSlideCaptureOptions & {
  fileName?: string;
};

export type ExportPdfFromPngOptions = {
  fileName?: string;
  /** Tamanho de design em px — define o formato físico da página (CSS 96 dpi → mm). */
  designSize: ViewportPixelSize;
};

function downloadDataUrl(dataUrl: string, fileName: string) {
  const link = document.createElement("a");
  link.download = fileName;
  link.href = dataUrl;
  link.click();
}

const MULTI_DOWNLOAD_GAP_MS = 120;

/** Dispara um download por PNG; intervalo curto evita o browser bloquear o segundo clique. */
export async function downloadPngDataUrls(
  pages: Array<{ dataUrl: string; fileName: string }>,
): Promise<void> {
  for (let index = 0; index < pages.length; index += 1) {
    const page = pages[index];
    downloadDataUrl(page.dataUrl, page.fileName);
    if (index < pages.length - 1) {
      await new Promise((resolve) => {
        window.setTimeout(resolve, MULTI_DOWNLOAD_GAP_MS);
      });
    }
  }
}

function shouldSkipNode(node: HTMLElement): boolean {
  if (node.classList?.contains("td-composer__stage-grid")) return true;
  if (node.classList?.contains("td-composer__stage-guide")) return true;
  if (node.classList?.contains("td-composer__smart-guide")) return true;
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

/** Converte px de design em mm (mesma base CSS 96 dpi das unidades do editor). */
export function designSizeToPdfFormatMm(designSize: ViewportPixelSize): [number, number] {
  return [cssPxToMm(designSize.width), cssPxToMm(designSize.height)];
}

/**
 * Monta PDF multi-página no aspecto do design (não A4 16:9).
 * Cada página recebe a imagem em tela cheia.
 */
export async function exportPngDataUrlsToPdf(
  pages: string[],
  options: ExportPdfFromPngOptions,
): Promise<void> {
  if (!pages.length) {
    throw new Error("Nenhuma página para exportar.");
  }
  const { jsPDF } = await import("jspdf");
  const [wMm, hMm] = designSizeToPdfFormatMm(options.designSize);
  const orientation = wMm >= hMm ? "landscape" : "portrait";
  const format: [number, number] = [wMm, hMm];
  const pdf = new jsPDF({
    orientation,
    unit: "mm",
    format,
  });
  pages.forEach((dataUrl, index) => {
    if (index > 0) pdf.addPage(format, orientation);
    pdf.addImage(dataUrl, "PNG", 0, 0, wMm, hMm);
  });
  const fileName = options.fileName ?? `playlist-${Date.now()}.pdf`;
  pdf.save(fileName);
}

export type ExportSlidePdfOptions = ExportSlideCaptureOptions &
  Partial<ExportPdfFromPngOptions> & {
    /** @deprecated Preferir designSize (aspecto do canvas). */
    orientation?: "landscape" | "portrait";
  };

/** Export PDF de uma página com a captura PNG do slide (aspecto do design). */
export async function exportSlideElementToPdf(
  element: HTMLElement,
  options: ExportSlidePdfOptions = {},
): Promise<string> {
  const dataUrl = await captureSlideElementToPngDataUrl(element, options);
  const designSize =
    options.designSize ??
    ({
      width: Math.max(1, Math.round(element.offsetWidth || element.clientWidth || 1920)),
      height: Math.max(1, Math.round(element.offsetHeight || element.clientHeight || 1080)),
    } satisfies ViewportPixelSize);
  await exportPngDataUrlsToPdf([dataUrl], {
    fileName: options.fileName ?? `slide-${Date.now()}.pdf`,
    designSize,
  });
  return dataUrl;
}

export function resolveSlideExportTarget(root: ParentNode | null | undefined): HTMLElement | null {
  if (!root) return null;
  const canvas = root.querySelector<HTMLElement>(".td-composer__canvas");
  if (canvas) return canvas;
  const preview = root.querySelector<HTMLElement>(
    ".tdp-comunicado, .td-deck-stage__canvas, .tdp-native-screen",
  );
  return preview;
}
