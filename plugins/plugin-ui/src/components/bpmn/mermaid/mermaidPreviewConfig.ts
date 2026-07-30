import { resolveMermaidTheme } from "../hooks/useDelpiDarkMode";

/** Largura alvo dos rótulos — alinhada ao editor BPMN (~168px). */
export const MERMAID_LABEL_WRAPPING_WIDTH = 156;

/** Largura alvo dos rótulos de faixa/subgraph no preview Mermaid. */
export const MERMAID_LANE_LABEL_WRAPPING_WIDTH = 34;

export function buildMermaidPreviewThemeCss(isDark: boolean): string {
  if (!isDark) {
    return `
      svg { background-color: #f8fafc !important; }
      foreignObject div { background: transparent !important; }
      .cluster-label foreignObject div { white-space: normal !important; line-height: 1.25 !important; }
    `;
  }
  return `
    svg { background-color: #111827 !important; }
    rect.background { fill: #111827 !important; }
    .cluster rect { fill: #1e293b !important; stroke: #475569 !important; }
    .cluster-label, .cluster-label .nodeLabel, .cluster-label span,
    .cluster-label foreignObject div {
      color: #e2e8f0 !important;
      fill: #e2e8f0 !important;
      background: transparent !important;
      white-space: normal !important;
      line-height: 1.25 !important;
      text-align: left !important;
    }
    foreignObject, foreignObject div, foreignObject span, foreignObject p {
      background: transparent !important;
      color: #e2e8f0 !important;
    }
    .edgeLabel rect { fill: #1e293b !important; }
    .edgeLabel foreignObject div { color: #e2e8f0 !important; background: transparent !important; }
  `;
}

export function buildMermaidPreviewConfig(isDark: boolean): Record<string, unknown> {
  const theme = resolveMermaidTheme(isDark);
  return {
    startOnLoad: false,
    // strict desativa htmlLabels e trunca rótulos longos em SVG.
    securityLevel: "sandbox",
    htmlLabels: true,
    theme,
    themeCSS: buildMermaidPreviewThemeCss(isDark),
    themeVariables:
      theme === "dark"
        ? {
            background: "#111827",
            mainBkg: "#111827",
            secondBkg: "#1e293b",
            primaryColor: "#1e293b",
            primaryTextColor: "#e2e8f0",
            primaryBorderColor: "#64748b",
            lineColor: "#94a3b8",
            secondaryColor: "#1f2937",
            tertiaryColor: "#0f172a",
            clusterBkg: "#1e293b",
            clusterBorder: "#475569",
            titleColor: "#f8fafc",
            edgeLabelBackground: "#1e293b",
          }
        : {
            background: "#f8fafc",
            mainBkg: "#f8fafc",
            secondBkg: "#f1f5f9",
            primaryColor: "#ecfdf5",
            primaryTextColor: "#0f172a",
            primaryBorderColor: "#64748b",
            lineColor: "#64748b",
            clusterBkg: "#f1f5f9",
            clusterBorder: "#cbd5e1",
            titleColor: "#0f172a",
            edgeLabelBackground: "#ffffff",
          },
    flowchart: {
      wrappingWidth: MERMAID_LABEL_WRAPPING_WIDTH,
      useMaxWidth: false,
      padding: 16,
      nodeSpacing: 48,
      rankSpacing: 72,
      diagramPadding: 12,
      subGraphTitleMargin: { top: 10, bottom: 18 },
    },
  };
}
