import { useEffect, useId, useRef, useState } from "react";

import { useDelpiDarkMode } from "../hooks/useDelpiDarkMode";
import type { DiagramViewportControlLabels } from "../editor/DiagramViewportControls";
import { parseSvgWorldSize } from "../layout/diagramViewport";
import { buildMermaidPreviewConfig } from "./mermaidPreviewConfig";
import { postProcessMermaidPreviewSvg } from "./mermaidPreviewPostProcess";
import {
  cleanupMermaidRenderArtifacts,
  isMermaidErrorSvg,
  sanitizeMermaidRenderId,
  unwrapMermaidRenderSvg,
} from "./mermaidRenderSafety";
import { applyMermaidPreviewTheme } from "./mermaidPreviewTheme";
import { SvgDiagramViewport } from "./SvgDiagramViewport";

type DiagramMermaidPreviewProps = {
  code: string;
  className?: string;
  isDark?: boolean;
  renderingLabel?: string;
  errorFallback?: string;
  viewportLabels?: DiagramViewportControlLabels;
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
  viewportLabels,
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
          const svgMarkup = unwrapMermaidRenderSvg(result.svg);
          if (isMermaidErrorSvg(svgMarkup)) {
            setSvg("");
            setError(errorFallback);
            renderedKeyRef.current = "";
            return;
          }
          setSvg(postProcessMermaidPreviewSvg(svgMarkup, isDark));
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

  const themeClass = isDark ? "delpi-ui-bpmn-mermaid--dark" : "delpi-ui-bpmn-mermaid--light";

  if (error) {
    return (
      <div
        className={["delpi-ui-bpmn-mermaid delpi-ui-bpmn-mermaid--error", themeClass, className]
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
        className={["delpi-ui-bpmn-mermaid delpi-ui-bpmn-mermaid--loading", themeClass, className]
          .filter(Boolean)
          .join(" ")}
      >
        {renderingLabel}
      </div>
    );
  }

  const preview = (
    <div
      className={[
        "delpi-ui-bpmn-mermaid",
        themeClass,
        rendering ? "delpi-ui-bpmn-mermaid--rendering" : "",
        viewportLabels ? "delpi-ui-bpmn-mermaid--viewport-world" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );

  if (!viewportLabels) {
    return preview;
  }

  const world = parseSvgWorldSize(svg);
  return (
    <SvgDiagramViewport
      labels={viewportLabels}
      worldWidth={world.width}
      worldHeight={world.height}
      className="delpi-ui-bpmn-editor__mermaid-preview"
    >
      {preview}
    </SvgDiagramViewport>
  );
}
