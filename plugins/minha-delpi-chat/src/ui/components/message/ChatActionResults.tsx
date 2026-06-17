import { useState } from "react";
import type { ChatToolCall } from "../../../data/api/chatTypes";

import "./ChatActionResults.css";

type ChatActionResultsProps = {
  toolCalls?: ChatToolCall[];
};

type ActionResultEntry = {
  key: string;
  label: string;
  statusCode?: number;
  ok?: boolean;
  path?: string;
  method?: string;
  responsePreview: string;
};

function isActionToolCall(toolCall: ChatToolCall): boolean {
  return toolCall.name === "execute_external_action";
}

function buildActionEntries(toolCalls: ChatToolCall[]): ActionResultEntry[] {
  return toolCalls
    .filter(isActionToolCall)
    .map((toolCall, index) => {
      const metadata = toolCall.metadata ?? {};
      const responsePreview =
        typeof metadata.responsePreview === "string"
          ? metadata.responsePreview.trim()
          : "";

      if (!responsePreview) {
        return null;
      }

      const actionId =
        typeof metadata.actionId === "string" ? metadata.actionId : undefined;
      const path = typeof metadata.path === "string" ? metadata.path : undefined;
      const method =
        typeof metadata.method === "string" ? metadata.method : undefined;
      const statusCode =
        typeof metadata.statusCode === "number" ? metadata.statusCode : undefined;
      const ok = typeof metadata.ok === "boolean" ? metadata.ok : undefined;

      return {
        key: `${actionId ?? toolCall.name ?? "action"}-${index}`,
        label: actionId ?? toolCall.name ?? "Action",
        statusCode,
        ok,
        path,
        method,
        responsePreview,
      };
    })
    .filter((entry) => entry !== null);
}

function CopyApiButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      className="mdc-chat-action-result-card__copy-btn"
      onClick={handleCopy}
      title="Copiar resposta da API"
    >
      {copied ? "✓ Copiado" : "Copiar"}
    </button>
  );
}

export function ChatActionResults({ toolCalls }: ChatActionResultsProps) {
  const entries = buildActionEntries(toolCalls ?? []);

  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="mdc-chat-action-results" aria-label="Respostas das actions">
      <details className="mdc-chat-action-results-details">
        <summary>
          <span>Resposta da API</span>
          <strong>{entries.length}</strong>
        </summary>

        <div className="mdc-chat-action-results-list">
          {entries.map((entry) => (
            <article className="mdc-chat-action-result-card" key={entry.key}>
              <div className="mdc-chat-action-result-card__header">
                <strong>{entry.label}</strong>
                <span>
                  {entry.method ? `${entry.method} ` : ""}
                  {entry.statusCode !== undefined ? entry.statusCode : "—"}
                  {entry.ok === false ? " · erro" : entry.ok === true ? " · ok" : ""}
                </span>
                <CopyApiButton text={entry.responsePreview} />
              </div>

              {entry.path ? (
                <p className="mdc-chat-action-result-card__path">{entry.path}</p>
              ) : null}

              <pre className="mdc-chat-action-result-card__body">
                {entry.responsePreview}
              </pre>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}
