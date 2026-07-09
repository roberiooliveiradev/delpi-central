import { getNodesBounds, getViewportForBounds, type Node } from "@xyflow/react";

import { LANE_CANVAS_WIDTH } from "./diagramSwimlanes";
import { getDiagramExportNodes } from "./diagramViewFit";

const EXPORT_PADDING = 0.12;
const MIN_EXPORT_ZOOM = 0.08;
const MAX_EXPORT_ZOOM = 4;
const EXPORT_EDGE_WIDTH = "1.5";
const FALLBACK_TEXT_COLOR = "#334155";
const FALLBACK_EDGE_STROKE = "#64748b";
const FALLBACK_EDGE_TEXT_BG = "#ffffff";

const HTML_LABEL_SELECTORS = [
  ".tm-diagram-node__label",
  ".tm-diagram-node__external-label",
  ".tm-diagram-inline-edit__display",
  ".tm-diagram-lane__label",
] as const;

type ExportPalette = {
  textColor: string;
  edgeTextColor: string;
  edgeTextBg: string;
  edgeStroke: string;
};

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

function isUsableColor(value: string | undefined | null): value is string {
  if (!value) return false;
  const normalized = value.trim().toLowerCase();
  return normalized !== "none" && normalized !== "transparent" && normalized !== "rgba(0, 0, 0, 0)";
}

function buildExportPalette(canvasRoot: HTMLElement, viewport: HTMLElement): ExportPalette {
  const labelSample =
    viewport.querySelector(".tm-diagram-node__label") ??
    viewport.querySelector(".tm-diagram-node__external-label") ??
    viewport.querySelector(".tm-diagram-inline-edit__display") ??
    viewport.querySelector(".tm-diagram-lane__label");

  const textColor =
    labelSample instanceof HTMLElement
      ? window.getComputedStyle(labelSample).color
      : window.getComputedStyle(canvasRoot).color;

  const edgeTextSample = viewport.querySelector(".react-flow__edge-text");
  const edgeTextColor =
    edgeTextSample instanceof SVGTextElement
      ? window.getComputedStyle(edgeTextSample).fill
      : textColor;

  const edgeBgSample = viewport.querySelector(".react-flow__edge-textbg");
  const nodeSample = viewport.querySelector(".tm-diagram-node");
  const edgeTextBg =
    edgeBgSample instanceof SVGElement
      ? window.getComputedStyle(edgeBgSample).fill
      : nodeSample instanceof HTMLElement
        ? window.getComputedStyle(nodeSample).backgroundColor
        : window.getComputedStyle(canvasRoot).backgroundColor;

  const edgePathSample = viewport.querySelector(".react-flow__edge-path");
  const edgeStroke =
    edgePathSample instanceof SVGPathElement
      ? resolveExportStroke(edgePathSample, FALLBACK_EDGE_STROKE)
      : FALLBACK_EDGE_STROKE;

  return {
    textColor: isUsableColor(textColor) ? textColor : FALLBACK_TEXT_COLOR,
    edgeTextColor: isUsableColor(edgeTextColor) ? edgeTextColor : isUsableColor(textColor) ? textColor : FALLBACK_TEXT_COLOR,
    edgeTextBg: isUsableColor(edgeTextBg) ? edgeTextBg : FALLBACK_EDGE_TEXT_BG,
    edgeStroke,
  };
}

function inlineHtmlLabelExportStyles(
  root: HTMLElement,
  snapshots: StyleSnapshot[],
  palette: ExportPalette
) {
  for (const selector of HTML_LABEL_SELECTORS) {
    root.querySelectorAll(selector).forEach((element) => {
      if (!(element instanceof HTMLElement)) return;
      const color = window.getComputedStyle(element).color;
      snapshotStyleProperty(
        element,
        "color",
        isUsableColor(color) ? color : palette.textColor,
        snapshots
      );
    });
  }
}

function inlineEdgeTextExportStyles(
  root: HTMLElement,
  snapshots: StyleSnapshot[],
  palette: ExportPalette
) {
  root.querySelectorAll(".react-flow__edge-text").forEach((textNode) => {
    if (!(textNode instanceof SVGTextElement)) return;
    const fill = isUsableColor(window.getComputedStyle(textNode).fill)
      ? window.getComputedStyle(textNode).fill
      : palette.edgeTextColor;
    snapshotAttribute(textNode, "fill", fill, snapshots);
    snapshotStyleProperty(textNode, "fill", fill, snapshots);
  });

  root.querySelectorAll(".react-flow__edge-textbg").forEach((backgroundNode) => {
    if (!(backgroundNode instanceof SVGElement)) return;
    const fill = isUsableColor(window.getComputedStyle(backgroundNode).fill)
      ? window.getComputedStyle(backgroundNode).fill
      : palette.edgeTextBg;
    snapshotAttribute(backgroundNode, "fill", fill, snapshots);
    snapshotAttribute(backgroundNode, "fill-opacity", "0.92", snapshots);
    snapshotStyleProperty(backgroundNode, "fill", fill, snapshots);
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

function resolveExportStroke(element: Element, fallback: string): string {
  if (!(element instanceof SVGGraphicsElement)) {
    return fallback;
  }
  const computed = window.getComputedStyle(element);
  const stroke = computed.stroke?.trim();
  if (isUsableColor(stroke) && !stroke.startsWith("var(")) {
    return stroke;
  }
  return fallback;
}

/** html-to-image não resolve stroke/fill via CSS var no clone — inline antes da captura. */
function inlineExportStyles(viewport: HTMLElement, canvasRoot: HTMLElement): () => void {
  const snapshots: StyleSnapshot[] = [];
  const palette = buildExportPalette(canvasRoot, viewport);

  viewport.querySelectorAll(".react-flow__edge-path").forEach((path) => {
    if (!(path instanceof SVGPathElement)) return;
    const stroke = resolveExportStroke(path, palette.edgeStroke);
    snapshotAttribute(path, "stroke", stroke, snapshots);
    snapshotAttribute(path, "stroke-width", EXPORT_EDGE_WIDTH, snapshots);
    snapshotAttribute(path, "fill", "none", snapshots);
    snapshotStyleProperty(path, "stroke", stroke, snapshots);
    snapshotStyleProperty(path, "stroke-width", EXPORT_EDGE_WIDTH, snapshots);
    snapshotStyleProperty(path, "fill", "none", snapshots);
  });

  viewport.querySelectorAll("marker path, marker polygon, marker polyline").forEach((markerPart) => {
    if (!(markerPart instanceof SVGGraphicsElement)) return;
    const stroke = resolveExportStroke(markerPart, palette.edgeStroke);
    snapshotAttribute(markerPart, "stroke", stroke, snapshots);
    snapshotAttribute(markerPart, "fill", stroke, snapshots);
    snapshotStyleProperty(markerPart, "stroke", stroke, snapshots);
    snapshotStyleProperty(markerPart, "fill", stroke, snapshots);
  });

  inlineHtmlLabelExportStyles(viewport, snapshots, palette);
  inlineEdgeTextExportStyles(viewport, snapshots, palette);

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

function injectExportSwimlaneBackdrop(viewport: HTMLElement, nodes: Node[]): () => void {
  const laneNodes = nodes.filter((node) => node.type === "lane");
  if (!laneNodes.length) {
    return () => undefined;
  }

  const container = document.createElement("div");
  container.className = "tm-diagram-export-swimlane-backdrop";
  container.setAttribute("aria-hidden", "true");

  for (const lane of laneNodes) {
    const data = lane.data as { height?: number; toneClass?: string };
    const band = document.createElement("div");
    band.className = ["tm-diagram-swimlane-backdrop__band", data.toneClass ?? ""]
      .filter(Boolean)
      .join(" ");
    band.style.top = `${lane.position.y}px`;
    band.style.left = "0";
    band.style.width = `${LANE_CANVAS_WIDTH}px`;
    band.style.height = `${data.height ?? 168}px`;
    container.appendChild(band);
  }

  viewport.insertBefore(container, viewport.firstChild);
  return () => {
    container.remove();
  };
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

  const bounds = getNodesBounds(getDiagramExportNodes(nodes));
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
  const restoreExportStyles = inlineExportStyles(viewportElement, canvasRoot);
  const removeExportBackdrop = injectExportSwimlaneBackdrop(viewportElement, nodes);

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
    removeExportBackdrop();
    restoreExportStyles();
    editorRoot?.classList.remove("tm-diagram-editor--exporting");
  }
}
