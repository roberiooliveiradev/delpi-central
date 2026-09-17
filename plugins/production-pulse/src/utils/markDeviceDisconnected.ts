import type { DeviceListItem, DeviceStatus } from "../types/device";

/**
 * After a failed live/poll probe, keep the IoT visible but as disconnected.
 * Does not override disabled / no_binding ownership states.
 */
export function markDeviceDisconnected(device: DeviceListItem): DeviceListItem {
  if (device.status === "disabled" || device.status === "no_binding") {
    return device;
  }
  const status: DeviceStatus = "offline";
  return {
    ...device,
    status,
    online: false,
  };
}
