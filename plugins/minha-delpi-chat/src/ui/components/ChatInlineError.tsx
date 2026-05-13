import { AlertTriangle, ChevronDown, RefreshCw, X } from "lucide-react";
import { useState } from "react";

import "./ChatInlineError.css";

type ChatInlineErrorProps = {
  message: string;
  details?: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
};

export function ChatInlineError({
  message,
  details,
  onRetry,
  onDismiss,
}: ChatInlineErrorProps) {
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  return (
    <aside className="mdc-chat-inline-error" role="alert">
      <div className="mdc-chat-inline-error__icon">
        <AlertTriangle size={18} aria-hidden="true" />
      </div>

      <div className="mdc-chat-inline-error__body">
        <div className="mdc-chat-inline-error__header">
          <div>
            <strong>Não consegui gerar a resposta agora.</strong>
            <p>{message}</p>
          </div>

          {onDismiss ? (
            <button
              type="button"
              className="mdc-chat-inline-error__close"
              onClick={onDismiss}
              aria-label="Fechar erro"
            >
              <X size={16} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        {(onRetry || details) ? (
          <div className="mdc-chat-inline-error__actions">
            {onRetry ? (
              <button type="button" onClick={onRetry}>
                <RefreshCw size={14} aria-hidden="true" />
                <span>Tentar novamente</span>
              </button>
            ) : null}

            {details ? (
              <button
                type="button"
                onClick={() => setIsDetailsOpen((current) => !current)}
                aria-expanded={isDetailsOpen}
              >
                <ChevronDown
                  size={14}
                  aria-hidden="true"
                  className={isDetailsOpen ? "is-open" : undefined}
                />
                <span>{isDetailsOpen ? "Ocultar detalhes" : "Ver detalhes"}</span>
              </button>
            ) : null}
          </div>
        ) : null}

        {details && isDetailsOpen ? (
          <pre className="mdc-chat-inline-error__details">{details}</pre>
        ) : null}
      </div>
    </aside>
  );
}
