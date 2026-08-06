import { useMemo, useState } from "react";

import "./ChatSelectionPendingPanel.css";

export type ChatSelectionEvidence = {
  shape?: string;
  columns?: string[];
  rows?: unknown[][];
  truncated?: boolean;
};

export type ChatSelectionCandidate = {
  id: string;
  label: string;
  score?: number | null;
  reason?: string | null;
  operationId?: string | null;
  path?: string | null;
  query?: string | null;
  evidence?: ChatSelectionEvidence | null;
};

export type ChatSelectionPending = {
  kind?: string;
  multiSelect?: boolean;
  prompt?: string;
  candidates?: ChatSelectionCandidate[];
  confirmLabel?: string;
  cancelLabel?: string;
  resume?: {
    mode?: string;
    action?: string;
  };
};

function buildResumeQuery(selected: ChatSelectionCandidate[]): string {
  const ids = selected
    .map((item) => String(item.operationId || item.id || "").trim())
    .filter(Boolean);
  if (ids.length === 1 && selected[0]?.query) {
    return String(selected[0].query).trim();
  }
  if (ids.length === 0) {
    return "";
  }
  return `adicione no slide as fontes: ${ids.join(", ")}`;
}

export function ChatSelectionPendingPanel({
  pending,
  onUseQuery,
}: {
  pending: ChatSelectionPending | null | undefined;
  onUseQuery?: (query: string) => void;
}) {
  const candidates = useMemo(
    () =>
      (pending?.candidates ?? []).filter(
        (item): item is ChatSelectionCandidate =>
          Boolean(item && String(item.id || item.operationId || "").trim()),
      ),
    [pending],
  );

  const multiSelect = pending?.multiSelect !== false;
  const [selectedIds, setSelectedIds] = useState<string[]>(() =>
    multiSelect ? [] : candidates[0] ? [String(candidates[0].id)] : [],
  );

  if (!pending || !onUseQuery || candidates.length === 0) {
    return null;
  }

  const toggle = (id: string) => {
    setSelectedIds((prev) => {
      if (!multiSelect) {
        return [id];
      }
      return prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
    });
  };

  const selected = candidates.filter((item) => selectedIds.includes(String(item.id)));
  const resumeQuery = buildResumeQuery(selected);

  return (
    <div
      className="mdc-chat-selection-pending"
      role="group"
      aria-label="Seleção de candidatos"
    >
      {pending.prompt ? (
        <p className="mdc-chat-selection-pending__prompt">{pending.prompt}</p>
      ) : null}
      <ul className="mdc-chat-selection-pending__list">
        {candidates.map((candidate) => {
          const id = String(candidate.id);
          const checked = selectedIds.includes(id);
          const evidence = candidate.evidence;
          const hasTable =
            evidence &&
            evidence.shape === "table" &&
            Array.isArray(evidence.columns) &&
            evidence.columns.length > 0;
          return (
            <li key={id} className="mdc-chat-selection-pending__item">
              <label className="mdc-chat-selection-pending__label">
                <input
                  type="checkbox"
                  className="mdc-chat-selection-pending__checkbox"
                  checked={checked}
                  onChange={() => toggle(id)}
                  aria-label={candidate.label}
                />
                <span className="mdc-chat-selection-pending__title">
                  {candidate.label}
                </span>
              </label>
              {candidate.reason ? (
                <p className="mdc-chat-selection-pending__reason">{candidate.reason}</p>
              ) : null}
              {hasTable ? (
                <div className="mdc-chat-selection-pending__evidence">
                  <table>
                    <thead>
                      <tr>
                        {evidence!.columns!.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(evidence!.rows ?? []).slice(0, 5).map((row, rowIdx) => (
                        <tr key={rowIdx}>
                          {(Array.isArray(row) ? row : [row]).map((cell, cellIdx) => (
                            <td key={cellIdx}>{String(cell ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {evidence?.truncated ? (
                    <span className="mdc-chat-selection-pending__truncated">
                      Amostra truncada
                    </span>
                  ) : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
      <div className="mdc-chat-selection-pending__actions">
        <button
          type="button"
          className="mdc-chat-selection-pending__btn mdc-chat-selection-pending__btn--confirm"
          disabled={!resumeQuery}
          onClick={() => {
            if (resumeQuery) {
              onUseQuery(resumeQuery);
            }
          }}
        >
          {pending.confirmLabel || "Adicionar selecionadas"}
        </button>
        <button
          type="button"
          className="mdc-chat-selection-pending__btn mdc-chat-selection-pending__btn--cancel"
          onClick={() => onUseQuery("cancelar esta seleção")}
        >
          {pending.cancelLabel || "Cancelar"}
        </button>
      </div>
    </div>
  );
}
