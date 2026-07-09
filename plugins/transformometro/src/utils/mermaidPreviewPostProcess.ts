const LIGHT_CANVAS = "#f8fafc";
const DARK_CANVAS = "#111827";
const DARK_CLUSTER_FILL = "#1e293b";
const DARK_CLUSTER_STROKE = "#475569";
const DARK_LABEL_COLOR = "#e2e8f0";

const LIGHT_FILL_VALUE =
  /#(?:fff(?:fff)?|ffffff|fefefe|f8fafc|f1f5f9|e2e8f0)\b|white\b/i;

type ViewBox = { x: number; y: number; width: number; height: number };

function parseViewBox(svg: string): ViewBox | null {
  const match = svg.match(/viewBox=["']([^"']+)["']/i);
  if (!match) return null;
  const parts = match[1].trim().split(/[\s,]+/).map(Number);
  if (parts.length !== 4 || parts.some(Number.isNaN)) return null;
  return { x: parts[0], y: parts[1], width: parts[2], height: parts[3] };
}

function injectSvgClass(svg: string, className: string): string {
  if (svg.includes(`class="${className}"`) || svg.includes(`class='${className}'`)) {
    return svg;
  }
  return svg.replace(/<svg\b/, `<svg class="${className}"`);
}

function setSvgCanvasStyle(svg: string, canvasColor: string, isDark: boolean): string {
  return svg.replace(/<svg([^>]*)>/i, (_match, attrs: string) => {
    let next = attrs.replace(/\sstyle=["'][^"']*["']/i, "");
    const colorScheme = isDark ? "dark" : "light";
    next += ` style="background-color:${canvasColor};color-scheme:${colorScheme};"`;
    return `<svg${next}>`;
  });
}

function appendStyleBlock(svg: string, css: string): string {
  const block = `<style type="text/css"><![CDATA[${css}]]></style>`;
  if (svg.includes(block)) return svg;
  return svg.replace(/<svg([^>]*)>/i, `<svg$1>${block}`);
}

function insertCanvasBackgroundRect(svg: string, canvasColor: string): string {
  if (svg.includes("tm-mermaid-canvas-bg")) return svg;
  const viewBox = parseViewBox(svg);
  if (!viewBox) return svg;

  const rect = [
    `<rect class="tm-mermaid-canvas-bg"`,
    `x="${viewBox.x}" y="${viewBox.y}"`,
    `width="${viewBox.width}" height="${viewBox.height}"`,
    `fill="${canvasColor}" stroke="none" pointer-events="none"/>`,
  ].join(" ");

  if (svg.includes("</style>")) {
    return svg.replace("</style>", `</style>${rect}`);
  }
  return svg.replace(/<svg([^>]*)>/i, `<svg$1>${rect}`);
}

function normalizeLightRectFills(svg: string, canvasColor: string, isDark: boolean): string {
  if (!isDark) return svg;

  return svg.replace(/<rect\b([^>]*?)\/?>/gi, (match, attrs: string) => {
    const isCanvasBg = /tm-mermaid-canvas-bg/.test(attrs);
    const targetColor = isCanvasBg ? canvasColor : DARK_CLUSTER_FILL;

    let nextAttrs = attrs;

    if (/\bfill\s*=\s*["'][^"']*["']/i.test(nextAttrs)) {
      nextAttrs = nextAttrs.replace(/\bfill\s*=\s*["']([^"']*)["']/i, (_fillMatch, fillValue: string) => {
        if (!LIGHT_FILL_VALUE.test(fillValue)) return `fill="${fillValue}"`;
        return `fill="${targetColor}"`;
      });
    }

    if (/\bstyle\s*=\s*["'][^"']*["']/i.test(nextAttrs)) {
      nextAttrs = nextAttrs.replace(/\bstyle\s*=\s*["']([^"']*)["']/i, (_styleMatch, styleValue: string) => {
        if (!/fill\s*:/i.test(styleValue)) return `style="${styleValue}"`;
        const nextStyle = styleValue.replace(/fill\s*:\s*[^;]+/gi, (fillRule: string) => {
          const color = fillRule.split(":")[1]?.trim() ?? "";
          if (!LIGHT_FILL_VALUE.test(color)) return fillRule;
          return `fill:${targetColor}`;
        });
        return `style="${nextStyle}"`;
      });
    }

    if (nextAttrs === attrs) return match;
    return `<rect${nextAttrs}>`;
  });
}

function buildThemeCss(isDark: boolean, canvasColor: string): string {
  if (!isDark) {
    return `
svg.tm-mermaid-svg--light { background-color: ${canvasColor} !important; }
svg.tm-mermaid-svg--light .tm-mermaid-canvas-bg { fill: ${canvasColor} !important; }
svg.tm-mermaid-svg--light foreignObject,
svg.tm-mermaid-svg--light foreignObject div {
  background: transparent !important;
}
`;
  }

  return `
svg.tm-mermaid-svg--dark {
  background-color: ${canvasColor} !important;
}
svg.tm-mermaid-svg--dark .tm-mermaid-canvas-bg,
svg.tm-mermaid-svg--dark rect.background {
  fill: ${canvasColor} !important;
}
svg.tm-mermaid-svg--dark .cluster > rect,
svg.tm-mermaid-svg--dark .cluster rect {
  fill: ${DARK_CLUSTER_FILL} !important;
  stroke: ${DARK_CLUSTER_STROKE} !important;
}
svg.tm-mermaid-svg--dark .cluster-label,
svg.tm-mermaid-svg--dark .cluster-label .nodeLabel,
svg.tm-mermaid-svg--dark .cluster-label span,
svg.tm-mermaid-svg--dark .cluster-label foreignObject div {
  color: ${DARK_LABEL_COLOR} !important;
  fill: ${DARK_LABEL_COLOR} !important;
  background: transparent !important;
}
svg.tm-mermaid-svg--dark foreignObject,
svg.tm-mermaid-svg--dark foreignObject div,
svg.tm-mermaid-svg--dark foreignObject span,
svg.tm-mermaid-svg--dark foreignObject p {
  background: transparent !important;
  background-color: transparent !important;
  color: ${DARK_LABEL_COLOR} !important;
}
svg.tm-mermaid-svg--dark .edgeLabel rect {
  fill: ${DARK_CLUSTER_FILL} !important;
}
svg.tm-mermaid-svg--dark .edgeLabel foreignObject div {
  color: ${DARK_LABEL_COLOR} !important;
  background: transparent !important;
}
svg.tm-mermaid-svg--dark .root > g > rect:first-of-type {
  fill: ${canvasColor} !important;
}
`;
}

export function postProcessMermaidPreviewSvg(svg: string, isDark: boolean): string {
  const trimmed = String(svg || "").trim();
  if (!trimmed) return trimmed;

  const canvas = isDark ? DARK_CANVAS : LIGHT_CANVAS;
  let output = injectSvgClass(
    trimmed,
    isDark ? "tm-mermaid-svg tm-mermaid-svg--dark" : "tm-mermaid-svg tm-mermaid-svg--light"
  );
  output = setSvgCanvasStyle(output, canvas, isDark);
  output = insertCanvasBackgroundRect(output, canvas);
  output = normalizeLightRectFills(output, canvas, isDark);
  output = appendStyleBlock(output, buildThemeCss(isDark, canvas));

  return output;
}
