import { resolveMermaidTheme } from "../hooks/useTransformometroDarkMode";

/** Largura alvo dos rótulos — alinhada ao editor BPMN (~168px). */
export const MERMAID_LABEL_WRAPPING_WIDTH = 156;

export function buildMermaidPreviewConfig(isDark: boolean): Record<string, unknown> {
  const theme = resolveMermaidTheme(isDark);
  return {
    startOnLoad: false,
    // strict desativa htmlLabels e trunca rótulos longos em SVG.
    securityLevel: "sandbox",
    htmlLabels: true,
    theme,
    themeVariables:
      theme === "dark"
        ? {
            background: "#111827",
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
      padding: 12,
      nodeSpacing: 48,
      rankSpacing: 56,
    },
  };
}
