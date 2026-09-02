import { RefreshCw } from "lucide-react";

import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import {
  formatCounterPeriodDelta,
  formatPrimaryMetric,
  formatRelativeTime,
  placementLabel,
  roleLabel,
} from "../utils/deviceDisplay";
import { AnchorTypeBadge } from "./AnchorTypeBadge";
import { DeviceStatusBadge } from "./DeviceStatusBadge";

type DeviceCardProps = {
  device: DeviceListItem;
  compact?: boolean;
  polling?: boolean;
  onPoll?: (deviceId: string) => void;
  onOpen?: (deviceId: string) => void;
};

export function DeviceCard({
  device,
  compact = false,
  polling = false,
  onPoll,
  onOpen,
}: DeviceCardProps) {
  const standalone = device.binding?.anchorType === "standalone";
  const showPlacementRow = device.binding != null && !standalone;

  return (
    <article
      className={`pp-device-card${compact ? " pp-device-card--compact" : ""}`}
      onClick={() => onOpen?.(device.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen?.(device.id);
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="pp-device-card__header">
        <strong className="pp-device-card__title">{device.name}</strong>
        <div className="pp-device-card__header-aside">
          {standalone ? <AnchorTypeBadge anchorType="standalone" /> : null}
          <DeviceStatusBadge status={device.status} />
        </div>
      </div>
      {showPlacementRow ? (
        <div className="pp-device-card__placement">
          <span>{placementLabel(device)}</span>
          <AnchorTypeBadge anchorType={device.binding!.anchorType} />
        </div>
      ) : null}
      {!device.binding ? (
        <div className="pp-device-card__placement">
          <span>—</span>
        </div>
      ) : null}
      <p className="pp-device-card__meta">
        {roleLabel(device.roleKey)} ·{" "}
        <span className="pp-tabular-nums">{formatPrimaryMetric(device)}</span>
        {formatCounterPeriodDelta(device, "day") ? (
          <>
            {" "}
            ·{" "}
            <span className="pp-tabular-nums">
              {formatCounterPeriodDelta(device, "day")} hoje
            </span>
          </>
        ) : null}{" "}
        · há <span className="pp-tabular-nums">{formatRelativeTime(device.lastSeenAt)}</span>
      </p>
      {!compact ? (
        <div className="pp-device-card__actions">
          <button
            type="button"
            className="pp-device-card__ghost"
            onClick={(event) => {
              event.stopPropagation();
              onOpen?.(device.id);
            }}
          >
            Ver
          </button>
          <button
            type="button"
            className="pp-device-card__ghost"
            title={PP_HELP.panel.rowPoll}
            disabled={polling}
            onClick={(event) => {
              event.stopPropagation();
              onPoll?.(device.id);
            }}
          >
            <RefreshCw size={14} className={polling ? "pp-spin" : undefined} aria-hidden="true" />
            {PP_HELP.panel.rowPollAction}
          </button>
        </div>
      ) : null}
    </article>
  );
}

type DeviceCardListProps = {
  devices: DeviceListItem[];
  pollingDeviceId: string | null;
  onPoll: (deviceId: string) => void;
  onOpenDevice?: (deviceId: string) => void;
};

export function DeviceCardList({
  devices,
  pollingDeviceId,
  onPoll,
  onOpenDevice,
}: DeviceCardListProps) {
  return (
    <div className="pp-device-card-list">
      {devices.map((device) => (
        <DeviceCard
          key={device.id}
          device={device}
          polling={pollingDeviceId === device.id}
          onPoll={onPoll}
          onOpen={onOpenDevice}
        />
      ))}
    </div>
  );
}
