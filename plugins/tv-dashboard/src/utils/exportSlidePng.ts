/** Export PNG do slide (4E.5) — html-to-image, padrão do monorepo. */

export type ExportSlidePngOptions = {
  fileName?: string;
  pixelRatio?: number;
  backgroundColor?: string;
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

export async function exportSlideElementToPng(
  element: HTMLElement,
  options: ExportSlidePngOptions = {},
): Promise<string> {
  const { toPng } = await import("html-to-image");
  const dataUrl = await toPng(element, {
    cacheBust: true,
    pixelRatio: options.pixelRatio ?? 2,
    backgroundColor: options.backgroundColor ?? "#ffffff",
    filter: (node) => {
      if (!(node instanceof HTMLElement)) return true;
      return !shouldSkipNode(node);
    },
  });
  const fileName = options.fileName ?? `slide-${Date.now()}.png`;
  downloadDataUrl(dataUrl, fileName);
  return dataUrl;
}

export function resolveSlideExportTarget(root: ParentNode | null | undefined): HTMLElement | null {
  if (!root) return null;
  const canvas = root.querySelector<HTMLElement>(".td-composer__canvas");
  if (canvas) return canvas;
  const preview = root.querySelector<HTMLElement>(".tdp-comunicado, .td-deck-stage__canvas, .tdp-native-screen");
  return preview;
}
