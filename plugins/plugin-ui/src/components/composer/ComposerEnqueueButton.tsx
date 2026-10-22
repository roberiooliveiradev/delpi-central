import { ListPlus } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import { HelpTooltip } from "../help/HelpTooltip";

export type ComposerEnqueueButtonProps = {
  /** External gates (empty draft, capture override) — never the only authority. */
  disabled?: boolean;
  onEnqueue: () => void;
  /** Accessible name + collapsed label. */
  label?: string;
  /** HelpTooltip content — product may override for context. */
  helpText?: string;
  className?: string;
};

/**
 * Doc 71 (F03-B) — "add to queue" affordance of `MessageComposer`,
 * rendered only while a turn is in flight and the host admits an
 * ephemeral conversation queue. Emits an enqueue INTENT via
 * `onEnqueue` (type="button" — never a form submit): the host decides
 * admission, ordering and dispatch. This button never calls an API,
 * never claims authority, and is absent when the host has no queue.
 *
 * CSS: `styles/message-composer.css` (`.delpi-ui-message-composer__enqueue`).
 */
export function ComposerEnqueueButton({
  disabled = false,
  onEnqueue,
  label = "Adicionar à fila",
  helpText = "Guardar esta pergunta na fila da conversa enquanto a resposta atual termina.",
  className,
}: ComposerEnqueueButtonProps) {
  return (
    <HelpTooltip wrap content={helpText}>
      <ActionButton
        type="button"
        variant="default"
        disabled={disabled}
        aria-label={label}
        onClick={onEnqueue}
        className={[
          "delpi-ui-message-composer__enqueue",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <ListPlus size={15} aria-hidden="true" />
        <span className="delpi-ui-message-composer__enqueue-label">
          {label}
        </span>
      </ActionButton>
    </HelpTooltip>
  );
}
