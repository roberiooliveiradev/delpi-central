import { useMemo, useState } from "react";

import "./ChatAdminDebugPanel.css";

type ChatAdminDebugPanelProps = {
  debug?: Record<string, unknown> | null;
};

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? "");
  }
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      className="mdc-chat-admin-debug__copy-btn"
      onClick={handleCopy}
      title="Copiar diagnóstico"
      type="button"
    >
      {copied ? "✓ Copiado" : "Copiar"}
    </button>
  );
}

export function ChatAdminDebugPanel({ debug }: ChatAdminDebugPanelProps) {
  const json = useMemo(() => safeJson(debug ?? {}), [debug]);

  if (!debug) return null;

  return (
    <section className="mdc-chat-admin-debug" aria-label="Diagnóstico (admin)">
      <details className="mdc-chat-admin-debug__details">
        <summary>
          <span>Diagnóstico (admin)</span>
          <span className="mdc-chat-admin-debug__summary-hint">
            tools · RAG · prompt · LLM
          </span>
        </summary>

        <div className="mdc-chat-admin-debug__toolbar">
          <CopyButton value={json} />
        </div>

        <pre className="mdc-chat-admin-debug__body">{json}</pre>
      </details>
    </section>
  );
}

