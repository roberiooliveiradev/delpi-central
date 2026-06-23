import { exportAlert } from "./exportAlert";
import { sanitizeFilename } from "./primitives";

const STYLE_PROPS = [
  "fill",
  "stroke",
  "stroke-width",
  "stroke-dasharray",
  "stroke-opacity",
  "fill-opacity",
  "opacity",
  "font-family",
  "font-size",
  "font-weight",
  "color",
] as const;

function readCssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();

  return value || fallback;
}

export function parseViewBoxSize(svg: SVGSVGElement): {
  width: number;
  height: number;
} | null {
  const viewBox = svg.getAttribute("viewBox");

  if (!viewBox) return null;

  const parts = viewBox.trim().split(/[\s,]+/).map((part) => Number(part));

  if (parts.length < 4) return null;

  const width = parts[2];
  const height = parts[3];

  if (
    !Number.isFinite(width) ||
    !Number.isFinite(height) ||
    width <= 0 ||
    height <= 0
  ) {
    return null;
  }

  return {
    width: Math.round(width),
    height: Math.round(height),
  };
}

function findChartSvg(container: HTMLElement): SVGSVGElement | null {
  const wrapper = container.querySelector<HTMLElement>(".recharts-wrapper");

  if (wrapper) {
    return wrapper.querySelector<SVGSVGElement>("svg");
  }

  return (
    container.querySelector<SVGSVGElement>("svg.recharts-surface") ??
    container.querySelector<SVGSVGElement>("svg")
  );
}

function resolveExportDimensions(
  container: HTMLElement,
  svg: SVGSVGElement,
): { width: number; height: number } {
  const fromViewBox = parseViewBoxSize(svg);

  if (fromViewBox) {
    return fromViewBox;
  }

  const wrapper = container.querySelector<HTMLElement>(".recharts-wrapper");
  const wrapperWidth = wrapper?.clientWidth ?? 0;
  const wrapperHeight = wrapper?.clientHeight ?? 0;

  if (wrapperWidth > 1 && wrapperHeight > 1) {
    return {
      width: Math.round(wrapperWidth),
      height: Math.round(wrapperHeight),
    };
  }

  const svgBounds = svg.getBoundingClientRect();

  if (svgBounds.width > 1 && svgBounds.height > 1) {
    return {
      width: Math.round(svgBounds.width),
      height: Math.round(svgBounds.height),
    };
  }

  const containerBounds = container.getBoundingClientRect();

  return {
    width: Math.max(1, Math.round(containerBounds.width) || 640),
    height: Math.max(1, Math.round(containerBounds.height) || 320),
  };
}

function stripClipPaths(root: SVGSVGElement): void {
  root.querySelectorAll("[clip-path]").forEach((node) => {
    node.removeAttribute("clip-path");
  });
}

export function resolveExportContainer(root: HTMLElement | null): HTMLElement | null {
  if (!root) return null;

  if (root.classList.contains("dc-chart-export-root")) {
    return root;
  }

  return root.querySelector<HTMLElement>(".dc-chart-export-root");
}

export function resolveChartExportTarget(root: HTMLElement | null): {
  container: HTMLElement;
  svg: SVGSVGElement;
  width: number;
  height: number;
} | null {
  const container = resolveExportContainer(root);

  if (!container) return null;

  const svg = findChartSvg(container);

  if (!svg) return null;

  const { width, height } = resolveExportDimensions(container, svg);

  return { container, svg, width, height };
}

function inlineSvgComputedStyles(source: Element, clone: Element): void {
  const sourceNodes = [source, ...Array.from(source.querySelectorAll("*"))];
  const cloneNodes = [clone, ...Array.from(clone.querySelectorAll("*"))];

  sourceNodes.forEach((node, index) => {
    const target = cloneNodes[index];

    if (!(node instanceof Element) || !(target instanceof Element)) {
      return;
    }

    const computed = window.getComputedStyle(node);
    const declarations: string[] = [];

    for (const prop of STYLE_PROPS) {
      const value = computed.getPropertyValue(prop);

      if (!value || value === "none" || value === "rgba(0, 0, 0, 0)") {
        continue;
      }

      declarations.push(`${prop}:${value}`);
    }

    if (declarations.length > 0) {
      const existing = target.getAttribute("style");
      target.setAttribute(
        "style",
        existing ? `${existing};${declarations.join(";")}` : declarations.join(";"),
      );
    }
  });
}

export function prepareSvgCloneForRasterExport(
  source: SVGSVGElement,
  width: number,
  height: number,
): SVGSVGElement {
  const clone = source.cloneNode(true) as SVGSVGElement;
  const viewBox = source.getAttribute("viewBox") ?? `0 0 ${width} ${height}`;
  const exportSize = parseViewBoxSize(source) ?? { width, height };

  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  clone.setAttribute("viewBox", viewBox);
  clone.setAttribute("width", String(exportSize.width));
  clone.setAttribute("height", String(exportSize.height));
  clone.removeAttribute("style");

  stripClipPaths(clone);
  inlineSvgComputedStyles(source, clone);

  clone.setAttribute("width", String(exportSize.width));
  clone.setAttribute("height", String(exportSize.height));
  clone.style.removeProperty("width");
  clone.style.removeProperty("height");
  clone.style.removeProperty("max-width");

  const background = readCssVar("--surface", readCssVar("--dc-card-bg", "#ffffff"));
  const backdrop = document.createElementNS("http://www.w3.org/2000/svg", "rect");

  backdrop.setAttribute("x", "0");
  backdrop.setAttribute("y", "0");
  backdrop.setAttribute("width", String(exportSize.width));
  backdrop.setAttribute("height", String(exportSize.height));
  backdrop.setAttribute("fill", background);
  clone.insertBefore(backdrop, clone.firstChild);

  return clone;
}

function rasterizeSvgChartElement(
  svg: SVGSVGElement,
  width: number,
  height: number,
): Promise<string | null> {
  const prepared = prepareSvgCloneForRasterExport(svg, width, height);
  const svgString = new XMLSerializer().serializeToString(prepared);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const scale = 2;
  const canvasWidth = width * scale;
  const canvasHeight = height * scale;

  return new Promise((resolve) => {
    const img = new Image();

    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      const ctx = canvas.getContext("2d");

      if (!ctx) {
        URL.revokeObjectURL(objectUrl);
        resolve(null);
        return;
      }

      ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);
      URL.revokeObjectURL(objectUrl);
      resolve(canvas.toDataURL("image/png"));
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(null);
    };

    img.src = objectUrl;
  });
}

async function rasterizeHtmlChartElement(
  container: HTMLElement,
): Promise<string | null> {
  const bounds = container.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width));
  const height = Math.max(1, Math.round(bounds.height));

  if (width < 2 || height < 2) {
    return null;
  }

  try {
    const { default: html2canvas } = await import("html2canvas");
    const background = readCssVar(
      "--surface",
      readCssVar("--dc-card-bg", "#ffffff"),
    );

    const canvas = await html2canvas(container, {
      backgroundColor: background,
      scale: 2,
      useCORS: true,
      logging: false,
      width,
      height,
    });

    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
}

export async function rasterizeChartElement(
  root: HTMLElement | null,
): Promise<string | null> {
  const container = resolveExportContainer(root);

  if (!container) {
    return null;
  }

  const svg = findChartSvg(container);

  if (svg) {
    const { width, height } = resolveExportDimensions(container, svg);
    return rasterizeSvgChartElement(svg, width, height);
  }

  return rasterizeHtmlChartElement(container);
}

export function exportChartElementToPng(
  root: HTMLElement | null,
  title: string,
): void {
  void rasterizeChartElement(root).then((dataUrl) => {
    if (!dataUrl) {
      exportAlert("Não encontrei o gráfico para exportar como PNG.");
      return;
    }

    const link = document.createElement("a");
    link.download = `${sanitizeFilename(title || "grafico")}.png`;
    link.href = dataUrl;
    link.click();
  });
}
