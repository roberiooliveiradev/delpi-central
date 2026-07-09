import { resolveMermaidTheme } from "../hooks/useTransformometroDarkMode";

/** Largura alvo dos rótulos — alinhada ao editor BPMN (~168px). */
export const MERMAID_LABEL_WRAPPING_WIDTH = 156;

export function buildMermaidPreviewConfig(isDark: boolean): Record<string, unknown> {
  return {
    startOnLoad: false,
    // strict desativa htmlLabels e trunca rótulos longos em SVG.
    securityLevel: "sandbox",
    htmlLabels: true,
    theme: resolveMermaidTheme(isDark),
    flowchart: {
      wrappingWidth: MERMAID_LABEL_WRAPPING_WIDTH,
      useMaxWidth: false,
      padding: 12,
      nodeSpacing: 48,
      rankSpacing: 56,
    },
  };
}
