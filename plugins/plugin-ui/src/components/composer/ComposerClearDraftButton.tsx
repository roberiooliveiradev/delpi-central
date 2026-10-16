import { X } from "lucide-react";
import { IconButton } from "../actions/IconButton";

export type ComposerClearDraftButtonProps = {
  onClear: () => void;
  disabled?: boolean;
  label?: string;
};

/** Explicit local draft discard only; no persistence, network, or conversation reset. */
export function ComposerClearDraftButton({
  onClear,
  disabled = false,
  label = "Limpar rascunho",
}: ComposerClearDraftButtonProps) {
  return (
    <IconButton
      className="delpi-ui-message-composer__clear"
      aria-label={label}
      disabled={disabled}
      onClick={onClear}
    >
      <X size={16} aria-hidden="true" />
    </IconButton>
  );
}
