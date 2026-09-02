import type { DeviceListItem } from "../../types/device";
import type { LivePollResult } from "../../types/detail";
import { PP_HELP } from "../../content/helpTooltips";
import { PpActionButton, PpSectionCard } from "../../app/productionPulseUi";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import {
  driverLabel,
  formatMetricValue,
  metricLabel,
  metricUnit,
  primaryMetricKey,
} from "../../utils/detailDisplay";

type DeviceMetricHeroProps = {
  device: DeviceListItem;
  liveSnapshot: LivePollResult | null;
  refreshing: boolean;
  canCommand: boolean;
  onRefreshLive: () => void;
  onPollNow: () => void;
  onReset: () => void;
};

export function DeviceMetricHero({
  device,
  liveSnapshot,
  refreshing,
  canCommand,
  onRefreshLive,
  onPollNow,
  onReset,
}: DeviceMetricHeroProps) {
  const metrics = liveSnapshot?.metrics ?? device.lastMetrics ?? {};
  const metricKey = primaryMetricKey(metrics, device.capabilities);
  const rawValue = metricKey ? metrics[metricKey] : null;
  const unit = metricKey ? metricUnit(metricKey) : undefined;
  const label = metricKey ? metricLabel(metricKey) : "Métrica";
  const recordedAt = liveSnapshot?.recordedAt ?? device.lastSeenAt;
  const supportsReset = device.capabilities?.commands?.includes("reset") ?? false;

  return (
    <PpSectionCard title="Métricas ao vivo" hint={PP_HELP.detail.liveMetrics}>
      <div className="pp-metric-hero">
        <p className="pp-metric-hero__value">
          {metricKey ? formatMetricValue(metricKey, rawValue).replace(` ${unit ?? ""}`, "").trim() : "—"}
        </p>
        {unit ? <p className="pp-metric-hero__unit">{unit}</p> : null}
        <p className="pp-metric-hero__label">{label}</p>
        <p className="pp-detail-muted">
          Última leitura: {formatRelativeTime(recordedAt)} · Poll: {device.pollIntervalMs} ms ·{" "}
          {driverLabel(device.driverKey)}
        </p>
        <div className="pp-metric-hero__actions">
          <PpActionButton variant="ghost" onClick={onRefreshLive} disabled={refreshing}>
            {refreshing ? "Atualizando…" : "Atualizar"}
          </PpActionButton>
          <PpActionButton variant="ghost" onClick={onPollNow} disabled={refreshing}>
            Poll agora
          </PpActionButton>
          {supportsReset && canCommand ? (
            <PpActionButton variant="ghost" onClick={onReset} disabled={refreshing || !device.online}>
              Reset contador
            </PpActionButton>
          ) : null}
        </div>
      </div>
    </PpSectionCard>
  );
}
