import { Loader2, Square } from "lucide-react";
import { ActionButton } from "../actions/ActionButton";

export type ComposerStopButtonProps = {
  stopping?: boolean;
  disabled?: boolean;
  onStop: () => void;
  stopLabel?: string;
  stoppingLabel?: string;
};

/** Controlled stop intent only: no API, AbortController or business cancellation. */
export function ComposerStopButton({
  stopping = false,
  disabled = false,
  onStop,
  stopLabel = "Interromper resposta",
  stoppingLabel = "Interrompendo…",
}: ComposerStopButtonProps) {
  return (
    <ActionButton
      type="button"
      variant="primary"
      disabled={disabled || stopping}
      onClick={onStop}
      aria-label={stopping ? stoppingLabel : stopLabel}
      className="delpi-ui-message-composer__send delpi-ui-message-composer__stop"
    >
      {stopping ? (
        <Loader2 size={15} aria-hidden="true" className="delpi-ui-message-composer__send-spinner" />
      ) : (
        <Square size={15} fill="currentColor" aria-hidden="true" />
      )}
      <span className="delpi-ui-message-composer__send-label">
        {stopping ? stoppingLabel : stopLabel}
      </span>
    </ActionButton>
  );
}
