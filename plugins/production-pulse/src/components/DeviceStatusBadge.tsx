import type { DeviceStatus } from "../types/device";
import { statusLabel } from "../utils/deviceDisplay";
import { preferLedVisualForConnectivity } from "../utils/deviceLedVisual";
import { DeviceLedBadge } from "./DeviceLedBadge";

type DeviceStatusBadgeProps = {
  status: DeviceStatus;
  /** Last known chip LED from live/poll; preferred over Pulse Online when device is online. */
  ledState?: string | null;
  /** When false, render LED without PpHintAction (compact surfaces). */
  withHint?: boolean;
};

/**
 * Pulse connectivity badge, or chip LED operational state when available.
 * disabled / no_binding / offline always use Pulse (avoid stale LED while unreachable).
 */
export function DeviceStatusBadge({
  status,
  ledState,
  withHint = true,
}: DeviceStatusBadgeProps) {
  const ledVisual = preferLedVisualForConnectivity(status, ledState);

  if (ledVisual) {
    if (withHint) {
      return <DeviceLedBadge ledState={ledVisual.ledState} />;
    }
    return (
      <span
        className={`pp-device-led ${ledVisual.colorClass} pp-led-pattern--${ledVisual.pattern}`}
        role="status"
        aria-label={`LED: ${ledVisual.label}`}
      >
        <span className="pp-device-led__dot" aria-hidden="true" />
        {ledVisual.label}
      </span>
    );
  }

  return (
    <span className={`pp-device-status pp-device-status--${status}`}>
      <span className="pp-device-status__dot" aria-hidden="true" />
      {statusLabel(status)}
    </span>
  );
}
