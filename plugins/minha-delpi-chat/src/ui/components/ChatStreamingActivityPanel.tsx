import { useEffect, useMemo, useState } from "react";

import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";

import "./ChatStreamingActivityPanel.css";

type ChatStreamingActivityPanelProps = {
  status: string | null;
  entries: ChatStreamActivityEntry[];
  isActive?: boolean;
};

type ActivityGroup = {
  key: string;
  label: string;
  items: ChatStreamActivityEntry[];
};

function resolveVerb(entry: ChatStreamActivityEntry): string {
  if (entry.verb?.trim()) {
    return entry.verb.trim();
  }

  const message = entry.message.trim();

  if (message.includes(":")) {
    return message.split(":")[0]?.trim() || "Processando";
  }

  return message.split(" ")[0] || "Processando";
}

function resolveTarget(entry: ChatStreamActivityEntry): string {
  if (entry.target?.trim()) {
    return entry.target.trim();
  }

  if (entry.path?.trim()) {
    return entry.path.trim();
  }

  const message = entry.message.trim();
  const colonIndex = message.indexOf(":");

  if (colonIndex >= 0) {
    return message.slice(colonIndex + 1).trim();
  }

  return message;
}

function groupEntries(entries: ChatStreamActivityEntry[]): ActivityGroup[] {
  const groups: ActivityGroup[] = [];
  const indexByKey = new Map<string, number>();

  for (const entry of entries) {
    const key = entry.group || entry.phase || "atividade";
    const label =
      entry.group ||
      (entry.phase === "think"
        ? "Pensar"
        : entry.phase === "plan"
          ? "Planejar novos passos"
          : entry.phase === "prepare"
            ? "Preparando"
            : entry.phase === "tools"
              ? "Consultando"
              : entry.phase === "rag"
                ? "Conhecimento"
                : entry.phase === "response"
                  ? "Respondendo"
                  : "Atividade");

    const existingIndex = indexByKey.get(key);

    if (existingIndex === undefined) {
      indexByKey.set(key, groups.length);
      groups.push({ key, label, items: [entry] });
      continue;
    }

    groups[existingIndex]?.items.push(entry);
  }

  return groups;
}

function ActivityRow({ entry }: { entry: ChatStreamActivityEntry }) {
  const verb = resolveVerb(entry);
  const target = resolveTarget(entry);
  const isActive = entry.state === "active";
  const levelClass =
    entry.level === "error"
      ? "is-error"
      : entry.level === "warning"
        ? "is-warning"
        : entry.level === "success"
          ? "is-success"
          : "";

  return (
    <li
      className={`mdc-chat-stream-activity__row ${levelClass}${isActive ? " is-active" : ""}`}
    >
      <span className="mdc-chat-stream-activity__verb">{verb}</span>
      <span className="mdc-chat-stream-activity__target" title={target}>
        {target}
      </span>
      {entry.statusCode ? (
        <span className="mdc-chat-stream-activity__http">{entry.statusCode}</span>
      ) : null}
      {entry.detail ? (
        <p className="mdc-chat-stream-activity__detail">{entry.detail}</p>
      ) : null}
    </li>
  );
}

export function ChatStreamingActivityPanel({
  status,
  entries,
  isActive = false,
}: ChatStreamingActivityPanelProps) {
  const hasIssues = useMemo(
    () => entries.some((entry) => entry.level === "warning" || entry.level === "error"),
    [entries],
  );

  const groups = useMemo(() => groupEntries(entries), [entries]);
  const [showLog, setShowLog] = useState(true);

  useEffect(() => {
    if (hasIssues || isActive) {
      setShowLog(true);
    }
  }, [hasIssues, isActive]);

  const headline = status?.trim() || "Processando sua solicitação...";
  const hasLog = entries.length > 0;

  return (
    <div className="mdc-chat-stream-activity" role="status" aria-live="polite">
      <p className="mdc-chat-stream-activity__summary">{headline}</p>

      {hasLog ? (
        <>
          <button
            type="button"
            className="mdc-chat-stream-activity__collapse"
            aria-expanded={showLog}
            onClick={() => setShowLog((current) => !current)}
          >
            {showLog ? "Ocultar etapas" : `Ver etapas (${entries.length})`}
          </button>

          {showLog ? (
            <div className="mdc-chat-stream-activity__groups">
              {groups.map((group) => (
                <section key={group.key} className="mdc-chat-stream-activity__group">
                  <h4 className="mdc-chat-stream-activity__group-title">{group.label}</h4>
                  <ul className="mdc-chat-stream-activity__rows">
                    {group.items.map((entry) => (
                      <ActivityRow key={entry.id} entry={entry} />
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          ) : null}
        </>
      ) : isActive ? (
        <p className="mdc-chat-stream-activity__waiting">
          <span className="mdc-chat-stream-activity__pulse" aria-hidden="true" />
          Aguardando etapas...
        </p>
      ) : null}
    </div>
  );
}
