import { Loader2, Square } from "lucide-react";
import { ActionButton } from "../actions/ActionButton";
import { HelpTooltip } from "../help/HelpTooltip";

export type ComposerStopButtonProps = {
  stopping?: boolean;
  disabled?: boolean;
  onStop: () => void;
  /** Visible label — compact ("Interromper"). */
  stopLabel?: string;
  /** Full accessible name while cancelable. */
  ariaLabel?: string;
  /** Visible label while stopping. */
  stoppingLabel?: string;
  /** Full accessible name while stopping. */
  stoppingAriaLabel?: string;
};

/** Controlled stop intent only: no API, AbortController or business cancellation. */
export function ComposerStopButton({
  stopping = false,
  disabled = false,
  onStop,
  stopLabel = "Interromper",
  ariaLabel = "Interromper resposta em andamento",
  stoppingLabel = "Interrompendo…",
  stoppingAriaLabel = "Interrompendo resposta…",
}: ComposerStopButtonProps) {
  return (
    <HelpTooltip
      wrap
      content={stopping ? stoppingAriaLabel : ariaLabel}
    >
      <ActionButton
        type="button"
        variant="primary"
        disabled={disabled || stopping}
        onClick={onStop}
        aria-label={stopping ? stoppingAriaLabel : ariaLabel}
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
    </HelpTooltip>
  );
}
