import type { SyntheticEvent } from "react";
import { RefreshCw } from "lucide-react";

import { PpActionButton, PpDataRecordCard } from "../app/productionPulseUi";
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
  onOpen?: (deviceId: string) => void;
  onPoll?: (deviceId: string) => void;
};

function deviceCardSubtitle(device: DeviceListItem): string | undefined {
  if (!device.binding) return "Sem amarração";
  if (device.binding.anchorType === "standalone") {
    return device.ipAddress;
  }
  const label = placementLabel(device);
  return label === "—" ? device.ipAddress : label;
}

function stopCardActivation(event: SyntheticEvent) {
  event.stopPropagation();
}

export function DeviceCard({
  device,
  compact = false,
  polling = false,
  onOpen,
  onPoll,
}: DeviceCardProps) {
  const standalone = device.binding?.anchorType === "standalone";
  const dayDelta = formatCounterPeriodDelta(device, "day");
  const metricValue = formatPrimaryMetric(device);

  const openDevice = () => onOpen?.(device.id);

  return (
    <div
      className="pp-device-card-hit"
      role="button"
      tabIndex={0}
      aria-label={device.name}
      onClick={openDevice}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openDevice();
        }
      }}
    >
      <PpDataRecordCard
        title={device.name}
        subtitle={deviceCardSubtitle(device)}
        status={
          <>
            {standalone ? <AnchorTypeBadge anchorType="standalone" /> : null}
            <DeviceStatusBadge status={device.status} />
          </>
        }
        fields={[
          {
            id: "role",
            label: "Papel",
            value: roleLabel(device.roleKey),
          },
          {
            id: "metric",
            label: "Métrica",
            value: (
              <>
                <span className="pp-tabular-nums">{metricValue}</span>
                {dayDelta ? (
                  <span className="pp-device-card-metric-delta">
                    {" "}
                    · <span className="pp-tabular-nums">{dayDelta}</span> hoje
                  </span>
                ) : null}
              </>
            ),
          },
          {
            id: "lastSeen",
            label: "Última leitura",
            value: (
              <span className="pp-tabular-nums" title={device.lastSeenAt ?? undefined}>
                {formatRelativeTime(device.lastSeenAt)}
              </span>
            ),
          },
        ]}
        context={
          compact ? undefined : (
            <div
              className="pp-device-card-actions"
              onClick={stopCardActivation}
              onKeyDown={stopCardActivation}
            >
              <PpActionButton variant="ghost" onClick={() => onOpen?.(device.id)}>
                {PP_HELP.panel.cardOpenDetail}
              </PpActionButton>
              <PpActionButton
                variant="ghost"
                title={PP_HELP.panel.rowPoll}
                disabled={polling}
                onClick={() => onPoll?.(device.id)}
              >
                <RefreshCw size={14} className={polling ? "pp-spin" : undefined} aria-hidden="true" />
                {PP_HELP.panel.rowPollAction}
              </PpActionButton>
            </div>
          )
        }
      />
    </div>
  );
}

type DeviceCardListProps = {
  devices: DeviceListItem[];
  loading?: boolean;
  pollingDeviceId: string | null;
  onOpenDevice?: (deviceId: string) => void;
  onPoll: (deviceId: string) => void;
};

export function DeviceCardList({
  devices,
  loading = false,
  pollingDeviceId,
  onOpenDevice,
  onPoll,
}: DeviceCardListProps) {
  return (
    <section className="pp-device-card-panel" aria-label="Dispositivos">
      <header className="pp-device-table__header">
        <h2 className="pp-device-table__title">Dispositivos</h2>
        <span className="pp-device-table__count">{devices.length} dispositivo(s)</span>
      </header>
      {loading ? <p className="pp-device-card-panel__loading">Carregando…</p> : null}
      {!loading && devices.length === 0 ? (
        <p className="pp-device-card-panel__empty">Nenhum dispositivo encontrado.</p>
      ) : null}
      <div className="pp-device-card-list">
        {devices.map((device) => (
          <DeviceCard
            key={device.id}
            device={device}
            polling={pollingDeviceId === device.id}
            onOpen={onOpenDevice}
            onPoll={onPoll}
          />
        ))}
      </div>
    </section>
  );
}
