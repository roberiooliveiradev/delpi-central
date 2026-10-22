import { useId, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  ChevronUp,
  CircleDashed,
  ListOrdered,
  Lock,
  X,
} from "lucide-react";

import { IconButton } from "../actions/IconButton";
import { HelpTooltip } from "../help/HelpTooltip";

/**
 * Doc 71 (F03-A) — compact conversation queue surface, positioned
 * immediately above the composer. RENDER-ONLY: every callback is a
 * user intent forwarded to the host; this component never imports
 * backend, scheduler, storage or authorization policy, and never
 * claims a mutation succeeded — the owner confirms order/removal.
 */
export type ConversationQueueItemStatus = "queued" | "blocked";

export type ConversationQueueItem = {
  /** Opaque owner-supplied id; the UI never interprets it. */
  id: string;
  /** Presentation title supplied by the consumer — never model-inferred. */
  label: string;
  ordinal: number;
  status: ConversationQueueItemStatus;
  /** Honest reason for a blocked/disabled state, received — not inferred. */
  reason?: string;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  canRemove?: boolean;
};

export type ConversationQueueProps = {
  items: readonly ConversationQueueItem[];
  expanded?: boolean;
  loading?: boolean;
  unavailable?: boolean;
  error?: string | null;
  onExpandedChange?: (expanded: boolean) => void;
  onMoveUp?: (itemId: string) => void;
  onMoveDown?: (itemId: string) => void;
  onRemove?: (itemId: string) => void;
  className?: string;
};

function queueCountLabel(count: number): string {
  return count === 1
    ? "1 solicitação aguardando"
    : `${count} solicitações aguardando`;
}

export function ConversationQueue({
  items,
  expanded,
  loading = false,
  unavailable = false,
  error = null,
  onExpandedChange,
  onMoveUp,
  onMoveDown,
  onRemove,
  className,
}: ConversationQueueProps) {
  const listId = useId();
  const [innerExpanded, setInnerExpanded] = useState(false);
  const isExpanded = expanded ?? innerExpanded;

  // CQ-V01: no confirmed pendings and no honest state → no surface,
  // no reserved height above the composer.
  const hasSurface =
    items.length > 0 || loading || unavailable || error !== null;
  if (!hasSurface) return null;

  const toggle = () => {
    const next = !isExpanded;
    if (expanded === undefined) setInnerExpanded(next);
    onExpandedChange?.(next);
  };

  const nextQueued = items.find((item) => item.status === "queued");
  const stateNotice = error ?? (unavailable
    ? "Fila temporariamente indisponível."
    : loading
      ? "Carregando fila…"
      : null);
  const collapsible = items.length > 0;

  return (
    <section
      className={["delpi-ui-conversation-queue", className]
        .filter(Boolean)
        .join(" ")}
      aria-label="Fila de solicitações da conversa"
    >
      <button
        type="button"
        className="delpi-ui-conversation-queue__header"
        onClick={collapsible ? toggle : undefined}
        aria-expanded={collapsible ? isExpanded : undefined}
        aria-controls={collapsible ? listId : undefined}
        disabled={!collapsible}
      >
        <ListOrdered size={16} aria-hidden="true" />
        <span className="delpi-ui-conversation-queue__count">
          {collapsible ? queueCountLabel(items.length) : "Fila da conversa"}
        </span>
        {collapsible && !isExpanded && nextQueued ? (
          <span className="delpi-ui-conversation-queue__next" title={nextQueued.label}>
            · Próxima: {nextQueued.label}
          </span>
        ) : null}
        {collapsible ? (
          isExpanded ? (
            <ChevronUp size={16} aria-hidden="true" />
          ) : (
            <ChevronDown size={16} aria-hidden="true" />
          )
        ) : null}
      </button>

      {stateNotice ? (
        <div
          className="delpi-ui-conversation-queue__notice"
          role={error ? "alert" : undefined}
        >
          {stateNotice}
        </div>
      ) : null}

      {collapsible && isExpanded ? (
        <ol
          id={listId}
          className="delpi-ui-conversation-queue__body"
          aria-label="Solicitações pendentes"
        >
          {items.map((item) => {
            const blocked = item.status === "blocked";
            return (
              <li key={item.id} className="delpi-ui-conversation-queue__item">
                <span
                  className="delpi-ui-conversation-queue__marker"
                  aria-hidden="true"
                >
                  {blocked ? (
                    <Lock size={13} />
                  ) : (
                    <CircleDashed size={13} />
                  )}
                </span>
                <span className="delpi-ui-conversation-queue__ordinal">
                  {item.ordinal}.
                </span>
                <span
                  className="delpi-ui-conversation-queue__label"
                  title={item.label}
                >
                  {item.label}
                </span>
                {blocked ? (
                  <span className="delpi-ui-conversation-queue__blocked">
                    Bloqueado{item.reason ? ` — ${item.reason}` : ""}
                  </span>
                ) : null}
                <span className="delpi-ui-conversation-queue__controls">
                  <HelpTooltip
                    wrap
                    content={`Mover "${item.label}" para cima`}
                  >
                    <IconButton
                      aria-label={`Mover "${item.label}" para cima`}
                      disabled={!item.canMoveUp || !onMoveUp}
                      onClick={() => onMoveUp?.(item.id)}
                    >
                      <ArrowUp size={14} aria-hidden="true" />
                    </IconButton>
                  </HelpTooltip>
                  <HelpTooltip
                    wrap
                    content={`Mover "${item.label}" para baixo`}
                  >
                    <IconButton
                      aria-label={`Mover "${item.label}" para baixo`}
                      disabled={!item.canMoveDown || !onMoveDown}
                      onClick={() => onMoveDown?.(item.id)}
                    >
                      <ArrowDown size={14} aria-hidden="true" />
                    </IconButton>
                  </HelpTooltip>
                  <HelpTooltip
                    wrap
                    content={`Remover "${item.label}" da fila`}
                  >
                    <IconButton
                      aria-label={`Remover "${item.label}" da fila`}
                      disabled={!item.canRemove || !onRemove}
                      onClick={() => onRemove?.(item.id)}
                    >
                      <X size={14} aria-hidden="true" />
                    </IconButton>
                  </HelpTooltip>
                </span>
              </li>
            );
          })}
          {loading ? (
            <li
              className="delpi-ui-conversation-queue__notice"
              aria-live="polite"
            >
              Atualizando fila…
            </li>
          ) : null}
        </ol>
      ) : null}
    </section>
  );
}
