import { useEffect, useId, useState } from "react";

type ChatMermaidBlockProps = {
  code: string;
};

type MermaidRenderer = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

let mermaidModulePromise: Promise<MermaidRenderer> | null = null;

function loadMermaid(): Promise<MermaidRenderer> {
  if (!mermaidModulePromise) {
    mermaidModulePromise = import("mermaid").then((module) => {
      const mermaid = module.default as MermaidRenderer;

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "dark",
      });

      return mermaid;
    });
  }

  return mermaidModulePromise;
}

export function ChatMermaidBlock({ code }: ChatMermaidBlockProps) {
  const reactId = useId().replace(/:/g, "");
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

    void loadMermaid()
      .then(async (mermaid) => {
        const renderId = `mdc-mermaid-${reactId}-${Date.now()}`;
        const result = await mermaid.render(renderId, diagram);

        if (!cancelled) {
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
  }, [code, reactId]);

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
