import { getNodesBounds, getViewportForBounds, type Node } from "@xyflow/react";

const EXPORT_PADDING = 0.12;
const MIN_EXPORT_ZOOM = 0.08;
const MAX_EXPORT_ZOOM = 4;
const EXPORT_EDGE_STROKE = "#64748b";
const EXPORT_EDGE_WIDTH = "1.5";

export type ExportReactFlowDiagramOptions = {
  canvasRoot: HTMLElement;
  nodes: Node[];
  filename: string;
  pixelRatio?: number;
};

type StyleSnapshot = {
  element: Element;
  attributes: Map<string, string | null>;
  styleProperties: Map<string, string>;
};

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Falha ao montar a imagem exportada."));
    image.src = src;
  });
}

async function rasterizeSvgDataUrl(svgDataUrl: string): Promise<string> {
  const image = await loadImage(svgDataUrl);
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Canvas indisponível para exportação.");
  }
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0);
  return canvas.toDataURL("image/png");
}

function inlineEdgeTextExportStyles(root: HTMLElement, snapshots: StyleSnapshot[]) {
  root.querySelectorAll(".react-flow__edge-text").forEach((textNode) => {
    if (!(textNode instanceof SVGTextElement)) return;
    snapshotAttribute(textNode, "fill", "#334155", snapshots);
  });

  root.querySelectorAll(".react-flow__edge-textbg").forEach((backgroundNode) => {
    if (!(backgroundNode instanceof SVGElement)) return;
    snapshotAttribute(backgroundNode, "fill", "#ffffff", snapshots);
    snapshotAttribute(backgroundNode, "fill-opacity", "0.92", snapshots);
  });
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

function snapshotAttribute(element: Element, name: string, value: string, snapshots: StyleSnapshot[]) {
  let snapshot = snapshots.find((entry) => entry.element === element);
  if (!snapshot) {
    snapshot = { element, attributes: new Map(), styleProperties: new Map() };
    snapshots.push(snapshot);
  }
  if (!snapshot.attributes.has(name)) {
    snapshot.attributes.set(name, element.getAttribute(name));
  }
  element.setAttribute(name, value);
}

function snapshotStyleProperty(
  element: HTMLElement | SVGElement,
  name: string,
  value: string,
  snapshots: StyleSnapshot[]
) {
  let snapshot = snapshots.find((entry) => entry.element === element);
  if (!snapshot) {
    snapshot = { element, attributes: new Map(), styleProperties: new Map() };
    snapshots.push(snapshot);
  }
  if (!snapshot.styleProperties.has(name)) {
    snapshot.styleProperties.set(name, element.style.getPropertyValue(name));
  }
  element.style.setProperty(name, value);
}

function resolveExportStroke(element: Element): string {
  if (!(element instanceof SVGGraphicsElement)) {
    return EXPORT_EDGE_STROKE;
  }
  const computed = window.getComputedStyle(element);
  const stroke = computed.stroke?.trim();
  if (stroke && stroke !== "none" && !stroke.startsWith("var(")) {
    return stroke;
  }
  return EXPORT_EDGE_STROKE;
}

/** html-to-image não resolve stroke via CSS var no clone — inline antes da captura. */
function inlineSvgExportStyles(root: HTMLElement): () => void {
  const snapshots: StyleSnapshot[] = [];

  root.querySelectorAll(".react-flow__edge-path").forEach((path) => {
    if (!(path instanceof SVGPathElement)) return;
    const stroke = resolveExportStroke(path);
    snapshotAttribute(path, "stroke", stroke, snapshots);
    snapshotAttribute(path, "stroke-width", EXPORT_EDGE_WIDTH, snapshots);
    snapshotAttribute(path, "fill", "none", snapshots);
    snapshotStyleProperty(path, "stroke", stroke, snapshots);
    snapshotStyleProperty(path, "stroke-width", EXPORT_EDGE_WIDTH, snapshots);
    snapshotStyleProperty(path, "fill", "none", snapshots);
  });

  root.querySelectorAll("marker path, marker polygon, marker polyline").forEach((markerPart) => {
    if (!(markerPart instanceof SVGGraphicsElement)) return;
    const stroke = resolveExportStroke(markerPart);
    snapshotAttribute(markerPart, "stroke", stroke, snapshots);
    snapshotAttribute(markerPart, "fill", stroke, snapshots);
    snapshotStyleProperty(markerPart, "stroke", stroke, snapshots);
    snapshotStyleProperty(markerPart, "fill", stroke, snapshots);
  });

  inlineEdgeTextExportStyles(root, snapshots);

  return () => {
    for (const snapshot of snapshots) {
      for (const [name, value] of snapshot.attributes) {
        if (value === null) snapshot.element.removeAttribute(name);
        else snapshot.element.setAttribute(name, value);
      }
      if (snapshot.element instanceof HTMLElement || snapshot.element instanceof SVGElement) {
        for (const [name, value] of snapshot.styleProperties) {
          if (value) snapshot.element.style.setProperty(name, value);
          else snapshot.element.style.removeProperty(name);
        }
      }
    }
  };
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
  const restoreSvgStyles = inlineSvgExportStyles(viewportElement);

  try {
    const { toSvg } = await import("html-to-image");
    const captureOptions = {
      cacheBust: true,
      pixelRatio,
      width,
      height,
      filter: shouldIncludeExportNode,
    };

    const viewportSvg = await toSvg(viewportElement, {
      ...captureOptions,
      style: captureStyle,
    });
    const dataUrl = await rasterizeSvgDataUrl(viewportSvg);

    downloadDataUrl(dataUrl, filename);
    return dataUrl;
  } finally {
    restoreSvgStyles();
    editorRoot?.classList.remove("tm-diagram-editor--exporting");
  }
}
