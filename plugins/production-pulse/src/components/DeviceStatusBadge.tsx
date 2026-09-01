import type { DeviceStatus } from "../types/device";
import { statusLabel } from "../utils/deviceDisplay";

type DeviceStatusBadgeProps = {
  status: DeviceStatus;
};

export function DeviceStatusBadge({ status }: DeviceStatusBadgeProps) {
  return (
    <span className={`pp-device-status pp-device-status--${status}`}>
      <span className="pp-device-status__dot" aria-hidden="true" />
      {statusLabel(status)}
    </span>
  );
}
