import type { OperatorPlacement } from "../../types/operator";
import { AnchorTypeBadge } from "../AnchorTypeBadge";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import {
  formatPlacementMeta,
  formatPrimaryPreview,
} from "../../utils/operatorDisplay";

type OperatorPlacementCardProps = {
  placement: OperatorPlacement;
  recent?: boolean;
  onSelect: (placement: OperatorPlacement) => void;
};

export function OperatorPlacementCard({
  placement,
  recent,
  onSelect,
}: OperatorPlacementCardProps) {
  const preview = formatPrimaryPreview(placement);

  return (
    <button
      type="button"
      className={`pp-operator-hub-card${recent ? " pp-operator-hub-card--recent" : ""}`}
      onClick={() => onSelect(placement)}
    >
      <div className="pp-operator-hub-card__header">
        <strong className="pp-operator-hub-card__title">{placement.placementLabel}</strong>
        <AnchorTypeBadge anchorType={placement.anchorType} />
      </div>
      <p className="pp-operator-hub-card__meta">{formatPlacementMeta(placement)}</p>
      {preview ? (
        <p className="pp-operator-hub-card__preview">{preview}</p>
      ) : (
        <p className="pp-operator-hub-card__preview">
          {placement.onlineCount > 0 ? (
            <DeviceStatusBadge status="online" />
          ) : (
            <DeviceStatusBadge status="offline" />
          )}
        </p>
      )}
      {recent ? <span className="pp-operator-hub-card__recent">Recente</span> : null}
    </button>
  );
}
