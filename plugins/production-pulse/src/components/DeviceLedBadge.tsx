import { PpHintAction } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import { resolveLedVisual, type DeviceLedState } from "../utils/deviceLedVisual";

type DeviceLedBadgeProps = {
  ledState: DeviceLedState | string;
};

export function DeviceLedBadge({ ledState }: DeviceLedBadgeProps) {
  const visual = resolveLedVisual(ledState);
  if (!visual) return null;

  return (
    <PpHintAction hint={PP_HELP.detail.ledState} ariaLabel={`Ajuda: LED ${visual.label}`}>
      <span
        className={`pp-device-led ${visual.colorClass} pp-led-pattern--${visual.pattern}`}
        role="status"
        aria-label={`LED: ${visual.label}`}
      >
        <span className="pp-device-led__dot" aria-hidden="true" />
        {visual.label}
      </span>
    </PpHintAction>
  );
}
