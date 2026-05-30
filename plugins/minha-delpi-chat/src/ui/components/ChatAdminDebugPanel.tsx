import { Bug } from "lucide-react";
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

function formatTimingMs(value: unknown): string | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }

  return `${Math.round(value)} ms`;
}

function AdminTimingsSummary({ intelligence }: { intelligence: Record<string, unknown> }) {
  const timings = intelligence.timings as Record<string, unknown> | undefined;

  if (!timings || typeof timings !== "object") {
    return null;
  }

  const entries = Object.entries(timings)
    .map(([key, value]) => {
      const label = formatTimingMs(value);

      if (!label) {
        return null;
      }

      return { key, label };
    })
    .filter(Boolean) as Array<{ key: string; label: string }>;

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Timings do pipeline">
      {entries.map((entry) => (
        <span key={entry.key} className="mdc-chat-admin-debug__timing-chip">
          <strong>{entry.key.replace(/_ms$/, "")}</strong> {entry.label}
        </span>
      ))}
    </div>
  );
}

export function ChatAdminDebugPanel({ debug }: ChatAdminDebugPanelProps) {
  const json = useMemo(() => safeJson(debug ?? {}), [debug]);
  const intelligence = (debug?.intelligence as Record<string, unknown> | undefined) ?? null;
  const [open, setOpen] = useState(false);

  if (!debug) return null;

  return (
    <section className="mdc-chat-admin-debug" aria-label="Diagnóstico (admin)">
      <details
        className="mdc-chat-admin-debug__details"
        open={open}
        onToggle={(e) => {
          setOpen((e.currentTarget as HTMLDetailsElement).open);
        }}
      >
        <summary className="mdc-chat-admin-debug__open-btn" title="Ver diagnóstico">
          <Bug size={16} aria-hidden="true" />
          <span>Diagnóstico (admin)</span>
          <span className="mdc-chat-admin-debug__summary-hint">
            tools · RAG · prompt · timings
          </span>
        </summary>

        <div className="mdc-chat-admin-debug__content">
          {intelligence ? <AdminTimingsSummary intelligence={intelligence} /> : null}
          <div className="mdc-chat-admin-debug__toolbar">
            <CopyButton value={json} />
          </div>

          <pre className="mdc-chat-admin-debug__body">{json}</pre>
        </div>
      </details>
    </section>
  );
}

