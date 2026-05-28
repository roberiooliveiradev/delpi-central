import { Bug, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { ModalPortal } from "./ModalPortal";
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

function ChatAdminDebugModal({
  title,
  json,
  onClose,
}: {
  title: string;
  json: string;
  onClose: () => void;
}) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    modalRef.current?.focus();
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <ModalPortal>
      <div
        className="mdc-chat-admin-debug-modal__backdrop"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={modalRef}
        tabIndex={-1}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <section className="mdc-chat-admin-debug-modal">
          <header className="mdc-chat-admin-debug-modal__header">
            <span className="mdc-chat-admin-debug-modal__title">{title}</span>
            <div className="mdc-chat-admin-debug-modal__toolbar">
              <CopyButton value={json} />
              <button
                type="button"
                className="mdc-chat-admin-debug-modal__close"
                onClick={onClose}
                aria-label="Fechar"
                title="Fechar"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
          </header>
          <pre className="mdc-chat-admin-debug-modal__body">{json}</pre>
        </section>
      </div>
    </ModalPortal>
  );
}

export function ChatAdminDebugPanel({ debug }: ChatAdminDebugPanelProps) {
  const json = useMemo(() => safeJson(debug ?? {}), [debug]);
  const [open, setOpen] = useState(false);

  if (!debug) return null;

  return (
    <section className="mdc-chat-admin-debug" aria-label="Diagnóstico (admin)">
      <button
        type="button"
        className="mdc-chat-admin-debug__open-btn"
        onClick={() => setOpen(true)}
        title="Abrir diagnóstico"
      >
        <Bug size={16} aria-hidden="true" />
        <span>Diagnóstico (admin)</span>
        <span className="mdc-chat-admin-debug__summary-hint">
          tools · RAG · prompt · LLM
        </span>
      </button>

      {open ? (
        <ChatAdminDebugModal
          title="Diagnóstico (admin)"
          json={json}
          onClose={() => setOpen(false)}
        />
      ) : null}
    </section>
  );
}

