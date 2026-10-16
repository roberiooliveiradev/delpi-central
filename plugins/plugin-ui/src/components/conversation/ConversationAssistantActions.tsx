import { useRef, useState, type ReactElement } from "react";
import {
  Check,
  Copy,
  MoreHorizontal,
  RefreshCw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

import { IconButton } from "../actions/IconButton";
import { HintAction } from "../help/HintAction";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { MessageActionBar } from "./MessageActionBar";

export type ConversationAssistantFeedbackValue = "positive" | "negative" | null;

export type ConversationAssistantMoreAction = {
  id: string;
  label: string;
  onSelect: () => void;
  disabled?: boolean;
};

export type ConversationAssistantActionsLabels = {
  group?: string;
  copy?: string;
  copied?: string;
  feedbackPositive?: string;
  feedbackNegative?: string;
  regenerate?: string;
  more?: string;
};

const DEFAULT_LABELS: Required<ConversationAssistantActionsLabels> = {
  group: "Ações da resposta",
  copy: "Copiar resposta",
  copied: "Resposta copiada",
  feedbackPositive: "Útil",
  feedbackNegative: "Não útil",
  regenerate: "Refazer resposta",
  more: "Mais opções",
};

export type ConversationAssistantActionsProps = {
  /** Plain readable text already prepared by the host (never recomputed here). */
  copyText: string;
  /** When false, copy control is disabled. Default: true when copyText is non-empty. */
  copyEnabled?: boolean;
  onCopySuccess?: () => void;
  onCopyError?: () => void;

  feedbackValue?: ConversationAssistantFeedbackValue;
  /**
   * When true and `onFeedbackChange` is provided, feedback is interactive.
   * Without a callback the controls stay visible but disabled (prepared UI).
   */
  feedbackEnabled?: boolean;
  onFeedbackChange?: (value: ConversationAssistantFeedbackValue) => void;

  regenerateEnabled?: boolean;
  onRegenerate?: () => void;

  /** Contextual actions — "Mais opções" renders only when non-empty. */
  moreActions?: readonly ConversationAssistantMoreAction[];

  disabled?: boolean;
  loading?: boolean;
  className?: string;
  labels?: ConversationAssistantActionsLabels;
};

/**
 * Complete conversational assistant action strip for message responses.
 *
 * Presentation-only composition over `MessageActionBar` + `IconButton`.
 * Owns clipboard UI feedback for a host-supplied `copyText`. Does not own
 * AuthZ, persistence, regeneration capability, or domain policy — the host
 * supplies availability and callbacks.
 */
export function ConversationAssistantActions({
  copyText,
  copyEnabled,
  onCopySuccess,
  onCopyError,
  feedbackValue = null,
  feedbackEnabled = false,
  onFeedbackChange,
  regenerateEnabled = false,
  onRegenerate,
  moreActions = [],
  disabled = false,
  loading = false,
  className,
  labels,
}: ConversationAssistantActionsProps) {
  const L = { ...DEFAULT_LABELS, ...labels };
  const [copied, setCopied] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreAnchorRef = useRef<HTMLDivElement>(null);
  const morePanelRef = useRef<HTMLDivElement>(null);

  const canCopy =
    (copyEnabled ?? copyText.length > 0) && !disabled && !loading;
  const feedbackInteractive =
    Boolean(onFeedbackChange) && feedbackEnabled && !disabled && !loading;
  const canRegenerate =
    Boolean(onRegenerate) && regenerateEnabled && !disabled && !loading;
  const showMore = moreActions.length > 0;

  function handleCopy() {
    if (!canCopy) return;
    try {
      const write = navigator.clipboard?.writeText(copyText);
      if (!write) {
        onCopyError?.();
        return;
      }
      void write
        .then(() => {
          setCopied(true);
          onCopySuccess?.();
          window.setTimeout(() => setCopied(false), 1500);
        })
        .catch(() => {
          onCopyError?.();
        });
    } catch {
      onCopyError?.();
    }
  }

  function handleFeedback(next: "positive" | "negative") {
    if (!feedbackInteractive || !onFeedbackChange) return;
    onFeedbackChange(feedbackValue === next ? null : next);
  }

  function withHint(hint: string, control: ReactElement) {
    return (
      <HintAction hint={hint} ariaLabel={hint} placement="top">
        {control}
      </HintAction>
    );
  }

  return (
    <MessageActionBar
      className={[
        "delpi-ui-conversation-assistant-actions",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      align="start"
      aria-label={L.group}
    >
      {withHint(
        copied ? L.copied : L.copy,
        <IconButton
          aria-label={copied ? L.copied : L.copy}
          disabled={!canCopy}
          onClick={handleCopy}
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
        </IconButton>,
      )}

      {withHint(
        L.feedbackPositive,
        <IconButton
          aria-label={L.feedbackPositive}
          pressed={feedbackValue === "positive"}
          disabled={!feedbackInteractive}
          onClick={() => handleFeedback("positive")}
        >
          <ThumbsUp size={13} />
        </IconButton>,
      )}

      {withHint(
        L.feedbackNegative,
        <IconButton
          aria-label={L.feedbackNegative}
          pressed={feedbackValue === "negative"}
          disabled={!feedbackInteractive}
          onClick={() => handleFeedback("negative")}
        >
          <ThumbsDown size={13} />
        </IconButton>,
      )}

      {withHint(
        L.regenerate,
        <IconButton
          aria-label={L.regenerate}
          disabled={!canRegenerate}
          onClick={() => {
            if (canRegenerate) onRegenerate?.();
          }}
        >
          <RefreshCw size={13} />
        </IconButton>,
      )}

      {showMore ? (
        <div
          className="delpi-ui-conversation-assistant-actions__more"
          ref={moreAnchorRef}
        >
          {withHint(
            L.more,
            <IconButton
              aria-label={L.more}
              aria-expanded={moreOpen}
              aria-haspopup="menu"
              disabled={disabled || loading}
              onClick={() => setMoreOpen((open) => !open)}
            >
              <MoreHorizontal size={13} />
            </IconButton>,
          )}
          {moreOpen ? (
            <AnchoredPanelPortal
              open={moreOpen}
              anchorRef={moreAnchorRef}
              panelRef={morePanelRef}
              variant="bare"
              className="delpi-ui-conversation-assistant-actions__menu"
              role="menu"
              aria-label={L.more}
              preferredPlacement="top"
              horizontalAlign="start"
              onDismiss={() => setMoreOpen(false)}
            >
              {moreActions.map((action) => (
                <button
                  key={action.id}
                  type="button"
                  role="menuitem"
                  className="delpi-ui-conversation-assistant-actions__menu-item"
                  disabled={action.disabled || disabled || loading}
                  onClick={() => {
                    setMoreOpen(false);
                    action.onSelect();
                  }}
                >
                  {action.label}
                </button>
              ))}
            </AnchoredPanelPortal>
          ) : null}
        </div>
      ) : null}
    </MessageActionBar>
  );
}
