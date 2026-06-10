import { useEffect, useId, useState } from "react";

import { resolveMermaidTheme, useMdcDarkMode } from "../theme/mdcCssVars";

type ChatMermaidBlockProps = {
  code: string;
};

type MermaidRenderer = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

let mermaidModulePromise: Promise<MermaidRenderer> | null = null;

function loadMermaidModule(): Promise<MermaidRenderer> {
  if (!mermaidModulePromise) {
    mermaidModulePromise = import("mermaid").then(
      (module) => module.default as MermaidRenderer,
    );
  }

  return mermaidModulePromise;
}

function initializeMermaid(mermaid: MermaidRenderer, isDark: boolean): void {
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: resolveMermaidTheme(isDark),
  });
}

function isMermaidErrorSvg(svg: string): boolean {
  const normalized = String(svg || "");

  return (
    /Syntax error/i.test(normalized) ||
    /class="error-icon"/i.test(normalized) ||
    /class='error-icon'/i.test(normalized)
  );
}

export function ChatMermaidBlock({ code }: ChatMermaidBlockProps) {
  const reactId = useId().replace(/:/g, "");
  const isDark = useMdcDarkMode();
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const diagram = String(code || "").trim();

    if (!diagram) {
      setSvg("");
      setError(null);

      return () => {
        cancelled = true;
      };
    }

    void loadMermaidModule()
      .then(async (mermaid) => {
        initializeMermaid(mermaid, isDark);
        const renderId = `mdc-mermaid-${reactId}-${Date.now()}`;
        const result = await mermaid.render(renderId, diagram);

        if (!cancelled) {
          if (isMermaidErrorSvg(result.svg)) {
            setSvg("");
            setError(
              "Não foi possível renderizar o diagrama Mermaid (sintaxe inválida).",
            );
            return;
          }

          setSvg(result.svg);
          setError(null);
        }
      })
      .catch((renderError: unknown) => {
        if (!cancelled) {
          setSvg("");
          setError(
            renderError instanceof Error
              ? renderError.message
              : "Não foi possível renderizar o diagrama Mermaid.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code, isDark, reactId]);

  if (error) {
    return (
      <div className="mdc-chat-mermaid mdc-chat-mermaid--error" role="alert">
        <pre className="mdc-chat-mermaid__fallback">
          <code>{code}</code>
        </pre>
        <p className="mdc-chat-mermaid__error">{error}</p>
      </div>
    );
  }

  if (!svg) {
    return <div className="mdc-chat-mermaid mdc-chat-mermaid--loading" aria-busy="true" />;
  }

  return (
    <div
      className="mdc-chat-mermaid"
      dangerouslySetInnerHTML={{ __html: svg }}
      aria-label="Diagrama Mermaid"
    />
  );
}
