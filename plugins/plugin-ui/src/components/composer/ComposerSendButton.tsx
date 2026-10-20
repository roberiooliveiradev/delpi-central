import { Loader2, SendHorizontal } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import { HelpTooltip } from "../help/HelpTooltip";

export type ComposerSendButtonProps = {
  /** Busy/disabled when the host request is in flight. */
  loading?: boolean;
  /** Additional external gate (e.g. empty draft) — never the only authority. */
  disabled?: boolean;
  /** Visible label; may collapse to icon-only via CSS on narrow containers. */
  label?: string;
  /** Accessible name while sending (honest, indeterminate). */
  loadingLabel?: string;
  /** HelpTooltip content — product may override for context. */
  helpText?: string;
  className?: string;
};

/**
 * Primary send action of `MessageComposer`.
 *
 * Emits submit intent through the enclosing `<form>` only — it never
 * calls an API. Disabled while loading so a second click cannot
 * duplicate the request; loading feedback is indeterminate and honest
 * (no fake progress, no provider names).
 *
 * CSS: `styles/message-composer.css` (`.delpi-ui-message-composer__send`).
 */
export function ComposerSendButton({
  loading = false,
  disabled = false,
  label = "Enviar",
  loadingLabel = "Enviando…",
  helpText = "Enviar o texto escrito.",
  className,
}: ComposerSendButtonProps) {
  return (
    <HelpTooltip wrap content={loading ? loadingLabel : helpText}>
      <ActionButton
        type="submit"
        variant="primary"
        disabled={disabled || loading}
        aria-label={loading ? loadingLabel : label}
        className={[
          "delpi-ui-message-composer__send",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
      >
      {loading ? (
        <Loader2
          size={15}
          aria-hidden="true"
          className="delpi-ui-message-composer__send-spinner"
        />
      ) : (
        <SendHorizontal size={15} aria-hidden="true" />
      )}
      <span className="delpi-ui-message-composer__send-label">
        {loading ? loadingLabel : label}
      </span>
      </ActionButton>
    </HelpTooltip>
  );
}
