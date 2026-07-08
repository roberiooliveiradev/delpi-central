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

export type RasterSvgOptions = {
  width: number;
  height: number;
  backgroundColor?: string;
  scale?: number;
};

export function prepareSvgCloneForRasterExport(
  source: SVGSVGElement,
  width: number,
  height: number,
  backgroundColor = "#ffffff",
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

  const backdrop = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  backdrop.setAttribute("x", "0");
  backdrop.setAttribute("y", "0");
  backdrop.setAttribute("width", String(width));
  backdrop.setAttribute("height", String(height));
  backdrop.setAttribute("fill", backgroundColor);
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
      target.setAttribute(
        "style",
        existing ? `${existing};${declarations.join(";")}` : declarations.join(";"),
      );
    }
  });
}

/**
 * Rasteriza um SVG para data URL PNG (canvas).
 * Sem seletores CSS de domínio — o caller resolve width/height/fundo.
 */
export function rasterizeSvgElement(
  svg: SVGSVGElement,
  options: RasterSvgOptions,
): Promise<string | null> {
  const { width, height, backgroundColor = "#ffffff", scale = 2 } = options;
  const prepared = prepareSvgCloneForRasterExport(svg, width, height, backgroundColor);
  const svgString = new XMLSerializer().serializeToString(prepared);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);

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

export type ExportSvgPngOptions = RasterSvgOptions & {
  filename?: string;
  onError?: () => void;
};

/** Baixa PNG a partir de um SVG (data URL). */
export function exportSvgElementToPng(
  svg: SVGSVGElement,
  options: ExportSvgPngOptions,
): void {
  const { filename = "grafico", onError, ...rasterOptions } = options;

  void rasterizeSvgElement(svg, rasterOptions).then((dataUrl) => {
    if (!dataUrl) {
      onError?.();
      return;
    }

    const link = document.createElement("a");
    link.download = `${sanitizeFilename(filename)}.png`;
    link.href = dataUrl;
    link.click();
  });
}
