import { useEffect, useId, useState } from "react";

import { useTransformometroDarkMode } from "../../hooks/useTransformometroDarkMode";
import { buildMermaidPreviewConfig } from "../../utils/mermaidPreviewConfig";
import { postProcessMermaidPreviewSvg } from "../../utils/mermaidPreviewPostProcess";
import { applyMermaidPreviewTheme } from "../../utils/mermaidPreviewTheme";

type DiagramMermaidPreviewProps = {
  code: string;
  className?: string;
};

type MermaidRenderer = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

let mermaidModulePromise: Promise<MermaidRenderer> | null = null;

function loadMermaidModule(): Promise<MermaidRenderer> {
  if (!mermaidModulePromise) {
    mermaidModulePromise = import("mermaid").then(
      (module) => module.default as MermaidRenderer
    );
  }
  return mermaidModulePromise;
}

export function DiagramMermaidPreview({ code, className }: DiagramMermaidPreviewProps) {
  const reactId = useId();
  const isDark = useTransformometroDarkMode();
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const diagram = String(code || "").trim();
    if (!diagram) {
      setSvg("");
      setError(null);
      return;
    }

    const themedDiagram = applyMermaidPreviewTheme(diagram, isDark);

    let cancelled = false;
    loadMermaidModule()
      .then(async (mermaid) => {
        mermaid.initialize(buildMermaidPreviewConfig(isDark));
        const renderId = `tm-mermaid-${reactId}-${Date.now()}`;
        const result = await mermaid.render(renderId, themedDiagram);
        if (!cancelled) {
          setSvg(postProcessMermaidPreviewSvg(result.svg, isDark));
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao renderizar Mermaid.");
          setSvg("");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code, isDark, reactId]);

  if (error) {
    return (
      <div className={["tm-diagram-mermaid tm-diagram-mermaid--error", className].filter(Boolean).join(" ")}>
        {error}
      </div>
    );
  }

  if (!svg) {
    return (
      <div className={["tm-diagram-mermaid tm-diagram-mermaid--loading", className].filter(Boolean).join(" ")}>
        Gerando preview…
      </div>
    );
  }

  return (
    <div
      className={[
        "tm-diagram-mermaid",
        isDark ? "tm-diagram-mermaid--dark" : "tm-diagram-mermaid--light",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
