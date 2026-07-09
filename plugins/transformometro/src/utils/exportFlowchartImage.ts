import { getNodesBounds, getViewportForBounds, type Node } from "@xyflow/react";

const EXPORT_PADDING = 0.12;
const MIN_EXPORT_ZOOM = 0.08;
const MAX_EXPORT_ZOOM = 4;

export type ExportReactFlowDiagramOptions = {
  canvasRoot: HTMLElement;
  nodes: Node[];
  filename: string;
  pixelRatio?: number;
};

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Falha ao montar a imagem exportada."));
    image.src = src;
  });
}

async function mergeTransparentLayers(layers: string[]): Promise<string> {
  const images = await Promise.all(layers.map((layer) => loadImage(layer)));
  const canvas = document.createElement("canvas");
  canvas.width = images[0]?.naturalWidth ?? 1;
  canvas.height = images[0]?.naturalHeight ?? 1;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Canvas indisponível para exportação.");
  }

  for (const image of images) {
    context.drawImage(image, 0, 0);
  }

  return canvas.toDataURL("image/png");
}

function shouldIncludeExportNode(node: Node): boolean {
  if (!(node instanceof HTMLElement)) {
    return true;
  }

  const classList = node.classList;
  if (classList.contains("react-flow__background")) return false;
  if (classList.contains("react-flow__controls")) return false;
  if (classList.contains("react-flow__minimap")) return false;
  if (classList.contains("react-flow__panel")) return false;
  if (classList.contains("react-flow__handle")) return false;
  if (node.closest(".react-flow__controls")) return false;
  if (node.closest(".react-flow__minimap")) return false;

  return true;
}

function downloadDataUrl(dataUrl: string, filename: string) {
  const link = document.createElement("a");
  link.download = filename;
  link.href = dataUrl;
  link.click();
}

export async function exportReactFlowDiagramPng({
  canvasRoot,
  nodes,
  filename,
  pixelRatio = 2,
}: ExportReactFlowDiagramOptions): Promise<string> {
  if (!nodes.length) {
    throw new Error("Diagrama vazio.");
  }

  const reactFlow = canvasRoot.querySelector(".react-flow");
  if (!(reactFlow instanceof HTMLElement)) {
    throw new Error("Canvas do diagrama não encontrado.");
  }

  const viewportElement = reactFlow.querySelector(".react-flow__viewport");
  if (!(viewportElement instanceof HTMLElement)) {
    throw new Error("Viewport do diagrama não encontrado.");
  }

  const edgeLabelElement = reactFlow.querySelector(".react-flow__edgelabel-renderer");
  const editorRoot = canvasRoot.closest(".tm-diagram-editor");

  const bounds = getNodesBounds(nodes);
  const width = Math.max(Math.ceil(bounds.width * (1 + EXPORT_PADDING * 2)), 1);
  const height = Math.max(Math.ceil(bounds.height * (1 + EXPORT_PADDING * 2)), 1);
  const viewport = getViewportForBounds(
    bounds,
    width,
    height,
    MIN_EXPORT_ZOOM,
    MAX_EXPORT_ZOOM,
    EXPORT_PADDING
  );
  const exportTransform = `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`;
  const captureStyle = {
    width: `${width}px`,
    height: `${height}px`,
    transform: exportTransform,
    transformOrigin: "0 0",
  };

  editorRoot?.classList.add("tm-diagram-editor--exporting");

  try {
    const { toPng } = await import("html-to-image");
    const captureOptions = {
      cacheBust: true,
      pixelRatio,
      width,
      height,
      filter: shouldIncludeExportNode,
    };

    const viewportLayer = await toPng(viewportElement, {
      ...captureOptions,
      style: captureStyle,
    });

    const layers = [viewportLayer];

    if (edgeLabelElement instanceof HTMLElement) {
      const labelLayer = await toPng(edgeLabelElement, {
        ...captureOptions,
        style: captureStyle,
      });
      layers.push(labelLayer);
    }

    const dataUrl =
      layers.length > 1 ? await mergeTransparentLayers(layers) : viewportLayer;

    downloadDataUrl(dataUrl, filename);
    return dataUrl;
  } finally {
    editorRoot?.classList.remove("tm-diagram-editor--exporting");
  }
}
