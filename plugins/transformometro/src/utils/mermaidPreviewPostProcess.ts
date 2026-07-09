const LIGHT_CANVAS = "#f8fafc";
const DARK_CANVAS = "#111827";
const DARK_CLUSTER_FILL = "#1e293b";
const DARK_CLUSTER_STROKE = "#475569";
const DARK_LABEL_COLOR = "#e2e8f0";

function injectSvgClass(svg: string, className: string): string {
  if (svg.includes(`class="${className}"`) || svg.includes(`class='${className}'`)) {
    return svg;
  }
  return svg.replace(/<svg\b/, `<svg class="${className}"`);
}

function injectStyleBlock(svg: string, css: string): string {
  const block = `<style type="text/css"><![CDATA[${css}]]></style>`;
  if (svg.includes("<style")) {
    return svg.replace(/<style[^>]*>[\s\S]*?<\/style>/, block);
  }
  return svg.replace(/<svg([^>]*)>/, `<svg$1>${block}`);
}

function replaceRootBackgroundRect(svg: string, canvasColor: string): string {
  return svg.replace(
    /<rect\b([^>]*?)>/gi,
    (match, attrs: string) => {
      const isWhite =
        /fill\s*=\s*["']#(?:fff(?:fff)?|ffffff|f8fafc|f1f5f9|fefefe)["']/i.test(attrs) ||
        /class\s*=\s*["'][^"']*background[^"']*["']/i.test(attrs);
      if (!isWhite) return match;
      const withoutFill = attrs.replace(/\sfill\s*=\s*["'][^"']*["']/gi, "");
      return `<rect${withoutFill} fill="${canvasColor}">`;
    }
  );
}

export function postProcessMermaidPreviewSvg(svg: string, isDark: boolean): string {
  const trimmed = String(svg || "").trim();
  if (!trimmed) return trimmed;

  const canvas = isDark ? DARK_CANVAS : LIGHT_CANVAS;
  let output = injectSvgClass(trimmed, isDark ? "tm-mermaid-svg tm-mermaid-svg--dark" : "tm-mermaid-svg tm-mermaid-svg--light");
  output = replaceRootBackgroundRect(output, canvas);

  const themeCss = isDark
    ? `
svg.tm-mermaid-svg--dark {
  background-color: ${DARK_CANVAS} !important;
}
svg.tm-mermaid-svg--dark rect.background {
  fill: ${DARK_CANVAS} !important;
}
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
  color: ${DARK_LABEL_COLOR} !important;
}
svg.tm-mermaid-svg--dark .edgeLabel,
svg.tm-mermaid-svg--dark .edgeLabel rect {
  fill: ${DARK_CLUSTER_FILL} !important;
}
svg.tm-mermaid-svg--dark .edgeLabel span,
svg.tm-mermaid-svg--dark .edgeLabel foreignObject div {
  color: ${DARK_LABEL_COLOR} !important;
  background: transparent !important;
}
`
    : `
svg.tm-mermaid-svg--light {
  background-color: ${LIGHT_CANVAS} !important;
}
svg.tm-mermaid-svg--light foreignObject,
svg.tm-mermaid-svg--light foreignObject div {
  background: transparent !important;
}
`;

  output = injectStyleBlock(output, themeCss);

  return output;
}
