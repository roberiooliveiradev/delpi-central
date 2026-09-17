import type { DeviceStatus } from "../../types/device";
import type { OperatorPlacement } from "../../types/operator";
import { AnchorTypeBadge } from "../AnchorTypeBadge";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import {
  formatByRoleSummary,
  formatPrimaryPreview,
  operatorPlacementTitle,
} from "../../utils/operatorDisplay";

type OperatorPlacementCardProps = {
  placement: OperatorPlacement;
  recent?: boolean;
  onSelect: (placement: OperatorPlacement) => void;
};

function resolvePlacementBadgeStatus(placement: OperatorPlacement): DeviceStatus {
  if (placement.primaryStatus) return placement.primaryStatus;
  if (placement.onlineCount > 0) return "online";
  if (placement.deviceCount > 0) return "offline";
  return "offline";
}

export function OperatorPlacementCard({
  placement,
  recent,
  onSelect,
}: OperatorPlacementCardProps) {
  const preview = formatPrimaryPreview(placement);
  const roleSummary = formatByRoleSummary(placement.byRole);
  const badgeStatus = resolvePlacementBadgeStatus(placement);

  return (
    <button
      type="button"
      className={`pp-operator-hub-card${recent ? " pp-operator-hub-card--recent" : ""}`}
      onClick={() => onSelect(placement)}
    >
      <div className="pp-operator-hub-card__header">
        <strong className="pp-operator-hub-card__title">{operatorPlacementTitle(placement)}</strong>
        <AnchorTypeBadge anchorType={placement.anchorType} />
      </div>
      <p className="pp-operator-hub-card__meta">{roleSummary}</p>
      <div className="pp-operator-hub-card__status">
        <DeviceStatusBadge
          status={badgeStatus}
          ledState={placement.primaryLedState}
          withHint={false}
        />
        {placement.deviceCount > 1 && placement.onlineCount > 0 ? (
          <span className="pp-operator-hub-card__status-extra">
            {placement.onlineCount}/{placement.deviceCount} online
          </span>
        ) : null}
      </div>
      {preview ? <p className="pp-operator-hub-card__preview">{preview}</p> : null}
      {recent ? <span className="pp-operator-hub-card__recent">Recente</span> : null}
    </button>
  );
}
