import { exportAlert } from "./exportAlert";
import { sanitizeFilename } from "./primitives";

const STYLE_PROPS = [
  "fill",
  "stroke",
  "stroke-width",
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

export function resolveChartExportTarget(root: HTMLElement | null): {
  container: HTMLElement;
  svg: SVGSVGElement;
  width: number;
  height: number;
} | null {
  if (!root) return null;

  const container = root.classList.contains("dc-chart-export-root")
    ? root
    : root.querySelector<HTMLElement>(".dc-chart-export-root");

  if (!container) return null;

  const svg =
    container.querySelector<SVGSVGElement>("svg.recharts-surface") ??
    container.querySelector<SVGSVGElement>("svg");

  if (!svg) return null;

  const bounds = container.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width) || 640);
  const height = Math.max(1, Math.round(bounds.height) || 320);

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

  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));

  if (!clone.getAttribute("viewBox")) {
    const viewBox = source.getAttribute("viewBox");

    if (viewBox) {
      clone.setAttribute("viewBox", viewBox);
    } else {
      clone.setAttribute("viewBox", `0 0 ${width} ${height}`);
    }
  }

  inlineSvgComputedStyles(source, clone);

  const background = readCssVar("--surface", readCssVar("--dc-card-bg", "#ffffff"));
  const backdrop = document.createElementNS("http://www.w3.org/2000/svg", "rect");

  backdrop.setAttribute("x", "0");
  backdrop.setAttribute("y", "0");
  backdrop.setAttribute("width", String(width));
  backdrop.setAttribute("height", String(height));
  backdrop.setAttribute("fill", background);
  clone.insertBefore(backdrop, clone.firstChild);

  return clone;
}

export function rasterizeChartElement(root: HTMLElement | null): Promise<string | null> {
  const target = resolveChartExportTarget(root);

  if (!target) {
    return Promise.resolve(null);
  }

  const { svg, width, height } = target;
  const prepared = prepareSvgCloneForRasterExport(svg, width, height);
  const svgString = new XMLSerializer().serializeToString(prepared);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const scale = 2;

  return new Promise((resolve) => {
    const img = new Image();

    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width * scale;
      canvas.height = height * scale;

      const ctx = canvas.getContext("2d");

      if (!ctx) {
        URL.revokeObjectURL(objectUrl);
        resolve(null);
        return;
      }

      ctx.scale(scale, scale);
      ctx.drawImage(img, 0, 0, width, height);
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
