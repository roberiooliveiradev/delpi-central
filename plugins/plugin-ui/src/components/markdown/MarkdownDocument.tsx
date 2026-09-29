/**
 * `MarkdownDocumentView` — document-grade markdown article renderer.
 *
 * Renders the segments produced by `buildMarkdownDocumentModel`: sanitized
 * GFM HTML, fenced code blocks (language label + copy + internal scroll) and
 * Mermaid diagrams (lazy-loaded, sandboxed render + pan/zoom viewport).
 *
 * This is a presentation read-model: `content_md`/markdown source is never
 * mutated here, and Mermaid blocks are illustrative document content — never
 * an alternative authority for canonical diagram data.
 */
import { Check, Copy, Eye, FileCode2 } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import { DiagramMermaidPreview } from "../bpmn/mermaid/DiagramMermaidPreview";
import type { DiagramViewportControlLabels } from "../bpmn/editor/DiagramViewportControls";
import type {
  MarkdownDocumentModel,
  MarkdownDocumentSegment,
} from "./markdownDocumentModel";

export type MarkdownDocumentLabels = {
  codeBlockLabel: string;
  copyCode: string;
  codeCopied: string;
  mermaidFigureLabel: string;
  mermaidIllustrativeHint: string;
  mermaidViewSource: string;
  mermaidRendering: string;
  mermaidError: string;
  mermaidViewport: DiagramViewportControlLabels;
};

export const MARKDOWN_DOCUMENT_LABELS_PT: MarkdownDocumentLabels = {
  codeBlockLabel: "Bloco de código",
  copyCode: "Copiar código",
  codeCopied: "Copiado",
  mermaidFigureLabel: "Diagrama Mermaid",
  mermaidIllustrativeHint: "Diagrama ilustrativo deste documento.",
  mermaidViewSource: "Ver código-fonte",
  mermaidRendering: "Renderizando diagrama…",
  mermaidError: "Não foi possível renderizar este diagrama.",
  mermaidViewport: {
    zoomLabel: "Zoom do diagrama",
    zoomIn: "Ampliar",
    zoomOut: "Reduzir",
    zoomInHint: "Aproxima o diagrama",
    zoomOutHint: "Afasta o diagrama",
    zoomFit: "Ajustar",
    zoomFitHint: "Ajusta o diagrama à área visível",
    zoomReset: "100%",
    zoomResetHint: "Restaura o zoom em 100%",
  },
};

async function copyTextToClipboard(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // fallback abaixo
  }
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "absolute";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}

function MarkdownCodeBlock({
  code,
  lang,
  labels,
}: {
  code: string;
  lang: string;
  labels: MarkdownDocumentLabels;
}) {
  const [copied, setCopied] = useState(false);
  const onCopy = useCallback(async () => {
    if (await copyTextToClipboard(code)) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    }
  }, [code]);

  return (
    <div className="delpi-ui-md-doc__code" aria-label={labels.codeBlockLabel}>
      <div className="delpi-ui-md-doc__code-bar">
        <span className="delpi-ui-md-doc__code-lang">
          <FileCode2 size={13} aria-hidden="true" />
          {lang || "text"}
        </span>
        <button
          type="button"
          className="delpi-ui-md-doc__code-copy"
          onClick={onCopy}
          aria-label={labels.copyCode}
        >
          {copied ? (
            <Check size={13} aria-hidden="true" />
          ) : (
            <Copy size={13} aria-hidden="true" />
          )}
          {copied ? labels.codeCopied : labels.copyCode}
        </button>
      </div>
      <pre className="delpi-ui-md-doc__code-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function MarkdownMermaidBlock({
  code,
  labels,
}: {
  code: string;
  labels: MarkdownDocumentLabels;
}) {
  return (
    <figure
      className="delpi-ui-md-doc__mermaid"
      aria-label={labels.mermaidFigureLabel}
    >
      <DiagramMermaidPreview
        code={code}
        renderingLabel={labels.mermaidRendering}
        errorFallback={labels.mermaidError}
        viewportLabels={labels.mermaidViewport}
      />
      <figcaption className="delpi-ui-md-doc__mermaid-caption">
        {labels.mermaidIllustrativeHint}
        <details className="delpi-ui-md-doc__mermaid-source">
          <summary>
            <Eye size={13} aria-hidden="true" />
            {labels.mermaidViewSource}
          </summary>
          <MarkdownCodeBlock code={code} lang="mermaid" labels={labels} />
        </details>
      </figcaption>
    </figure>
  );
}

function MarkdownDocumentSegmentView({
  segment,
  labels,
}: {
  segment: MarkdownDocumentSegment;
  labels: MarkdownDocumentLabels;
}) {
  if (segment.type === "code") {
    return (
      <MarkdownCodeBlock code={segment.code} lang={segment.lang} labels={labels} />
    );
  }
  if (segment.type === "mermaid") {
    return <MarkdownMermaidBlock code={segment.code} labels={labels} />;
  }
  return (
    <div
      className="delpi-ui-md-doc__segment"
      dangerouslySetInnerHTML={{ __html: segment.html }}
    />
  );
}

export type MarkdownDocumentViewProps = {
  model: MarkdownDocumentModel;
  labels?: MarkdownDocumentLabels;
  className?: string;
};

export function MarkdownDocumentView({
  model,
  labels = MARKDOWN_DOCUMENT_LABELS_PT,
  className,
}: MarkdownDocumentViewProps) {
  const segments = useMemo(() => model.segments, [model]);
  return (
    <div className={["delpi-ui-md-doc", className].filter(Boolean).join(" ")}>
      {segments.map((segment, index) => (
        <MarkdownDocumentSegmentView
          key={index}
          segment={segment}
          labels={labels}
        />
      ))}
    </div>
  );
}
