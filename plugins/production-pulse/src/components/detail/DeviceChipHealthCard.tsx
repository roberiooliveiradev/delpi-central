import { PpSectionCard } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import type { DeviceChipHealth } from "../../types/detail";

type DeviceChipHealthCardProps = {
  health: DeviceChipHealth | null | undefined;
};

function formatUptime(ms: number | undefined): string | null {
  if (ms == null || !Number.isFinite(ms) || ms < 0) return null;
  const totalSec = Math.floor(ms / 1000);
  const hours = Math.floor(totalSec / 3600);
  const minutes = Math.floor((totalSec % 3600) / 60);
  const seconds = totalSec % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export function hasChipHealth(health: DeviceChipHealth | null | undefined): boolean {
  if (!health) return false;
  return (
    health.firmwareVersion != null ||
    health.uptimeMs != null ||
    health.freeHeap != null ||
    health.rssi != null ||
    health.wifiConnected != null
  );
}

export function DeviceChipHealthCard({ health }: DeviceChipHealthCardProps) {
  if (!hasChipHealth(health)) return null;

  const uptime = formatUptime(
    typeof health?.uptimeMs === "number" ? health.uptimeMs : undefined,
  );
  const wifiLabel =
    health?.wifiConnected == null
      ? null
      : health.wifiConnected
        ? PP_HELP.detail.chipHealthWifiOnline
        : PP_HELP.detail.chipHealthWifiOffline;

  return (
    <PpSectionCard title={PP_HELP.detail.chipHealthTitle} hint={PP_HELP.detail.chipHealth}>
      <dl className="pp-chip-health">
        {health?.firmwareVersion ? (
          <div className="pp-chip-health__row">
            <dt>{PP_HELP.detail.chipHealthVersion}</dt>
            <dd>{health.firmwareVersion}</dd>
          </div>
        ) : null}
        {uptime ? (
          <div className="pp-chip-health__row">
            <dt>{PP_HELP.detail.chipHealthUptime}</dt>
            <dd>{uptime}</dd>
          </div>
        ) : null}
        {health?.rssi != null ? (
          <div className="pp-chip-health__row">
            <dt>{PP_HELP.detail.chipHealthRssi}</dt>
            <dd>{health.rssi} dBm</dd>
          </div>
        ) : null}
        {health?.freeHeap != null ? (
          <div className="pp-chip-health__row">
            <dt>{PP_HELP.detail.chipHealthHeap}</dt>
            <dd>{new Intl.NumberFormat("pt-BR").format(Number(health.freeHeap))} B</dd>
          </div>
        ) : null}
        {wifiLabel ? (
          <div className="pp-chip-health__row">
            <dt>{PP_HELP.detail.chipHealthWifi}</dt>
            <dd>{wifiLabel}</dd>
          </div>
        ) : null}
      </dl>
    </PpSectionCard>
  );
}
