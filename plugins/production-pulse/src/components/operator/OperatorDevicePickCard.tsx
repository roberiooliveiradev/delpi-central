import type { OperatorDeviceItem } from "../../types/operator";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import {
  operatorDevicePreview,
  operatorRoleBadgeLabel,
} from "../../utils/operatorDisplay";

type OperatorDevicePickCardProps = {
  device: OperatorDeviceItem;
  onSelect: (device: OperatorDeviceItem) => void;
};

export function OperatorDevicePickCard({ device, onSelect }: OperatorDevicePickCardProps) {
  return (
    <button type="button" className="pp-operator-pick-card" onClick={() => onSelect(device)}>
      <span className="pp-operator-pick-card__badge">{operatorRoleBadgeLabel(device.roleKey)}</span>
      <strong className="pp-operator-pick-card__name">{device.name}</strong>
      <div className="pp-operator-pick-card__footer">
        <DeviceStatusBadge status={device.status} />
        <span className="pp-operator-pick-card__metric">{operatorDevicePreview(device)}</span>
      </div>
    </button>
  );
}
