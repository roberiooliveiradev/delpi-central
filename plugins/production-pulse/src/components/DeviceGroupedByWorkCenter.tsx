import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import type { DeviceListItem } from "../types/device";
import type { DeviceGroup } from "../utils/deviceGrouping";
import { AnchorTypeBadge } from "./AnchorTypeBadge";
import { DeviceCard } from "./DeviceCard";
import { DeviceStatusBadge } from "./DeviceStatusBadge";
import { formatPrimaryMetric } from "../utils/deviceDisplay";

type DeviceGroupedByWorkCenterProps = {
  groups: DeviceGroup[];
  mobile?: boolean;
  pollingDeviceId: string | null;
  onPoll: (deviceId: string) => void;
  onOpenDevice?: (deviceId: string) => void;
};

function GroupSection({
  group,
  mobile,
  pollingDeviceId,
  onPoll,
  onOpenDevice,
}: {
  group: DeviceGroup;
  mobile?: boolean;
  pollingDeviceId: string | null;
  onPoll: (deviceId: string) => void;
  onOpenDevice?: (deviceId: string) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <section className="pp-placement-group">
      <button
        type="button"
        className="pp-placement-group__header"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        {open ? <ChevronDown size={18} aria-hidden="true" /> : <ChevronRight size={18} aria-hidden="true" />}
        <span className="pp-placement-group__title">{group.title}</span>
        {group.anchorType ? <AnchorTypeBadge anchorType={group.anchorType} /> : null}
        <span className="pp-placement-group__meta">
          {group.devices.length} device{group.devices.length === 1 ? "" : "s"} · {group.onlineCount} online
        </span>
      </button>
      {open ? (
        mobile ? (
          <div className="pp-placement-group__cards">
            {group.devices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                compact
                polling={pollingDeviceId === device.id}
                onPoll={onPoll}
                onOpen={onOpenDevice}
              />
            ))}
          </div>
        ) : (
          <div className="pp-placement-group__rows">
            {group.devices.map((device) => (
              <GroupedRow
                key={device.id}
                device={device}
                polling={pollingDeviceId === device.id}
                onPoll={onPoll}
                onOpen={onOpenDevice}
              />
            ))}
          </div>
        )
      ) : null}
    </section>
  );
}

function GroupedRow({
  device,
  polling,
  onPoll,
  onOpen,
}: {
  device: DeviceListItem;
  polling: boolean;
  onPoll: (deviceId: string) => void;
  onOpen?: (deviceId: string) => void;
}) {
  return (
    <div className="pp-placement-group__row">
      <button type="button" className="pp-device-link" onClick={() => onOpen?.(device.id)}>
        {device.name}
      </button>
      <span className="pp-tabular-nums">{formatPrimaryMetric(device)}</span>
      <DeviceStatusBadge status={device.status} />
      <button
        type="button"
        className="pp-row-action"
        disabled={polling}
        onClick={() => onPoll(device.id)}
        aria-label={`Atualizar ${device.name}`}
      >
        Poll
      </button>
    </div>
  );
}

export function DeviceGroupedByWorkCenter({
  groups,
  mobile,
  pollingDeviceId,
  onPoll,
  onOpenDevice,
}: DeviceGroupedByWorkCenterProps) {
  if (groups.length === 0) {
    return null;
  }

  return (
    <div className="pp-placement-groups">
      {groups.map((group) => (
        <GroupSection
          key={group.key}
          group={group}
          mobile={mobile}
          pollingDeviceId={pollingDeviceId}
          onPoll={onPoll}
          onOpenDevice={onOpenDevice}
        />
      ))}
    </div>
  );
}
