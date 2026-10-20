import { X } from "lucide-react";
import { IconButton } from "../actions/IconButton";
import { HelpTooltip } from "../help/HelpTooltip";

export type ComposerClearDraftButtonProps = {
  onClear: () => void;
  disabled?: boolean;
  label?: string;
  /** HelpTooltip content — product may override for context. */
  helpText?: string;
};

/** Explicit local draft discard only; no persistence, network, or conversation reset. */
export function ComposerClearDraftButton({
  onClear,
  disabled = false,
  label = "Limpar texto",
  helpText = "Limpar o texto do campo.",
}: ComposerClearDraftButtonProps) {
  return (
    <HelpTooltip wrap content={helpText}>
      <IconButton
        className="delpi-ui-message-composer__clear"
        aria-label={label}
        disabled={disabled}
        onClick={onClear}
      >
        <X size={16} aria-hidden="true" />
      </IconButton>
    </HelpTooltip>
  );
}
