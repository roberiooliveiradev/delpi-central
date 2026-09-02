import type { DeviceListItem } from "../types/device";
import { placementLabel } from "../utils/deviceDisplay";
import { AnchorTypeBadge } from "./AnchorTypeBadge";

type PlacementObjectDisplayProps = {
  device: DeviceListItem;
};

export function PlacementObjectDisplay({ device }: PlacementObjectDisplayProps) {
  if (!device.binding) {
    return <span className="pp-device-placement">—</span>;
  }

  if (device.binding.anchorType === "standalone") {
    return (
      <span className="pp-device-placement">
        <AnchorTypeBadge anchorType="standalone" />
      </span>
    );
  }

  return (
    <span className="pp-device-placement">
      <span>{placementLabel(device)}</span>
      <AnchorTypeBadge anchorType={device.binding.anchorType} />
    </span>
  );
}
