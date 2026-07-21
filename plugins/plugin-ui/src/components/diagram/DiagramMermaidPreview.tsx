import { useEffect, useId, useRef, useState } from "react";

import { useDelpiDarkMode } from "./hooks/useDelpiDarkMode";
import { buildMermaidPreviewConfig } from "./utils/mermaidPreviewConfig";
import { postProcessMermaidPreviewSvg } from "./utils/mermaidPreviewPostProcess";
import {
  cleanupMermaidRenderArtifacts,
  isMermaidErrorSvg,
  sanitizeMermaidRenderId,
} from "./utils/mermaidRenderSafety";
import { applyMermaidPreviewTheme } from "./utils/mermaidPreviewTheme";

type DiagramMermaidPreviewProps = {
  code: string;
  className?: string;
  isDark?: boolean;
  renderingLabel?: string;
  errorFallback?: string;
};

type MermaidRenderer = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

let mermaidModulePromise: Promise<MermaidRenderer> | null = null;
let mermaidInitializedForDark: boolean | null = null;

function loadMermaidModule(): Promise<MermaidRenderer> {
  if (!mermaidModulePromise) {
    mermaidModulePromise = import("mermaid").then(
      (module) => module.default as MermaidRenderer
    );
  }
  return mermaidModulePromise;
}

export function DiagramMermaidPreview({
  code,
  className,
  isDark: isDarkProp,
  renderingLabel = "…",
  errorFallback = "Render error.",
}: DiagramMermaidPreviewProps) {
  const reactId = sanitizeMermaidRenderId(useId());
  const isDarkFromHook = useDelpiDarkMode();
  const isDark = isDarkProp ?? isDarkFromHook;
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const renderedKeyRef = useRef("");

  useEffect(() => {
    const diagram = String(code || "").trim();
    const renderKey = `${isDark ? "dark" : "light"}:${diagram}`;

    if (!diagram) {
      renderedKeyRef.current = "";
      setSvg("");
      setError(null);
      setRendering(false);
      return;
    }

    if (renderKey === renderedKeyRef.current) {
      return;
    }

    let cancelled = false;
    setRendering(true);
    const renderId = sanitizeMermaidRenderId(`tm-mermaid-${reactId}-${Date.now()}`);

    loadMermaidModule()
      .then(async (mermaid) => {
        if (mermaidInitializedForDark !== isDark) {
          mermaid.initialize(buildMermaidPreviewConfig(isDark));
          mermaidInitializedForDark = isDark;
        }

        const themedDiagram = applyMermaidPreviewTheme(diagram, isDark);
        try {
          const result = await mermaid.render(renderId, themedDiagram);
          if (cancelled) return;
          if (isMermaidErrorSvg(result.svg)) {
            setSvg("");
            setError(errorFallback);
            renderedKeyRef.current = "";
            return;
          }
          setSvg(postProcessMermaidPreviewSvg(result.svg, isDark));
          setError(null);
          renderedKeyRef.current = renderKey;
        } finally {
          cleanupMermaidRenderArtifacts(renderId);
        }
      })
      .catch((err) => {
        cleanupMermaidRenderArtifacts(renderId);
        if (!cancelled) {
          setError(err instanceof Error ? err.message : errorFallback);
          setSvg("");
          renderedKeyRef.current = "";
        }
      })
      .finally(() => {
        if (!cancelled) {
          setRendering(false);
        }
      });

    return () => {
      cancelled = true;
      cleanupMermaidRenderArtifacts(renderId);
    };
  }, [code, errorFallback, isDark, reactId]);

  const themeClass = isDark ? "tm-diagram-mermaid--dark" : "tm-diagram-mermaid--light";

  if (error) {
    return (
      <div
        className={["tm-diagram-mermaid tm-diagram-mermaid--error", themeClass, className]
          .filter(Boolean)
          .join(" ")}
        role="alert"
      >
        {error}
      </div>
    );
  }

  if (!svg) {
    return (
      <div
        className={["tm-diagram-mermaid tm-diagram-mermaid--loading", themeClass, className]
          .filter(Boolean)
          .join(" ")}
      >
        {renderingLabel}
      </div>
    );
  }

  return (
    <div
      className={[
        "tm-diagram-mermaid",
        themeClass,
        rendering ? "tm-diagram-mermaid--rendering" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
