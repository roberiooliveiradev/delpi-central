import { readMdcCssVar } from "../theme/mdcCssVars";

function sanitizeFilename(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);
}

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

export function resolveChartExportTarget(root: HTMLElement | null): {
  container: HTMLElement;
  svg: SVGSVGElement;
  width: number;
  height: number;
} | null {
  if (!root) {
    return null;
  }

  const container = root.classList.contains("mdc-rich-chart__container")
    ? root
    : root.querySelector<HTMLElement>(".mdc-rich-chart__container");

  if (!container) {
    return null;
  }

  const svg =
    container.querySelector<SVGSVGElement>("svg.recharts-surface") ??
    container.querySelector<SVGSVGElement>("svg");

  if (!svg) {
    return null;
  }

  const bounds = container.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width) || 640);
  const height = Math.max(1, Math.round(bounds.height) || 280);

  return { container, svg, width, height };
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

  const background = readMdcCssVar("--mdc-chart-export-bg", readMdcCssVar("--mdc-card-bg", "#ffffff"));
  const backdrop = document.createElementNS("http://www.w3.org/2000/svg", "rect");

  backdrop.setAttribute("x", "0");
  backdrop.setAttribute("y", "0");
  backdrop.setAttribute("width", String(width));
  backdrop.setAttribute("height", String(height));
  backdrop.setAttribute("fill", background);
  clone.insertBefore(backdrop, clone.firstChild);

  return clone;
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
      target.setAttribute("style", existing ? `${existing};${declarations.join(";")}` : declarations.join(";"));
    }
  });
}

export function exportChartElementToPng(
  root: HTMLElement | null,
  title: string,
): void {
  const target = resolveChartExportTarget(root);

  if (!target) {
    window.alert("Não encontrei o gráfico para exportar como PNG.");
    return;
  }

  const { svg, width, height } = target;
  const prepared = prepareSvgCloneForRasterExport(svg, width, height);
  const svgString = new XMLSerializer().serializeToString(prepared);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const scale = 2;

  const img = new Image();

  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = width * scale;
    canvas.height = height * scale;

    const ctx = canvas.getContext("2d");

    if (!ctx) {
      URL.revokeObjectURL(objectUrl);
      return;
    }

    ctx.scale(scale, scale);
    ctx.drawImage(img, 0, 0, width, height);

    const link = document.createElement("a");
    link.download = `${sanitizeFilename(title || "grafico")}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
    URL.revokeObjectURL(objectUrl);
  };

  img.onerror = () => {
    URL.revokeObjectURL(objectUrl);
    window.alert("Não foi possível gerar o PNG do gráfico. Tente expandir e exportar novamente.");
  };

  img.src = objectUrl;
}
