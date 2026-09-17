import { Factory, Radio, RefreshCw, RotateCcw } from "lucide-react";

import type { DeviceListItem } from "../../types/device";
import type { LivePollResult } from "../../types/detail";
import type { LiveConnectivityIssue } from "../../hooks/useDeviceDetail";
import { PP_HELP } from "../../content/helpTooltips";
import { PpActionButton, PpHintAction, PpSectionCard } from "../../app/productionPulseUi";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import {
  driverLabel,
  formatMetricValue,
  metricLabel,
  metricUnit,
  primaryMetricKey,
} from "../../utils/detailDisplay";
import { DetailStatusBanner } from "./DetailStatusBanner";

type DeviceMetricHeroProps = {
  device: DeviceListItem;
  liveSnapshot: LivePollResult | null;
  liveConnectivityIssue?: LiveConnectivityIssue | null;
  refreshing: boolean;
  canCommand: boolean;
  onRefreshLive: () => void;
  onPollNow: () => void;
  onReset: () => void;
  onFactoryReset?: () => void;
};

export function DeviceMetricHero({
  device,
  liveSnapshot,
  liveConnectivityIssue = null,
  refreshing,
  canCommand,
  onRefreshLive,
  onPollNow,
  onReset,
  onFactoryReset,
}: DeviceMetricHeroProps) {
  const metrics = liveSnapshot?.metrics ?? device.lastMetrics ?? {};
  const metricKey = primaryMetricKey(metrics, device.capabilities);
  const rawValue = metricKey ? metrics[metricKey] : null;
  const unit = metricKey ? metricUnit(metricKey) : undefined;
  const label = metricKey ? metricLabel(metricKey) : "Métrica";
  const recordedAt = liveSnapshot?.recordedAt ?? device.lastSeenAt;
  const supportsReset = device.capabilities?.commands?.includes("reset") ?? false;
  const supportsFactoryReset =
    device.capabilities?.commands?.includes("factory_reset") ?? false;
  const deviceOffline =
    device.status === "offline" || device.online === false || !device.enabled;
  const showConnectivityWarning = Boolean(liveConnectivityIssue) || deviceOffline;
  const warningMessage =
    liveConnectivityIssue?.message || PP_HELP.detail.liveOfflineFallback;
  const refreshLabel = refreshing
    ? PP_HELP.detail.pollNowLoading
    : PP_HELP.detail.refreshLiveAction;
  const pollLabel = refreshing
    ? PP_HELP.detail.pollNowLoading
    : PP_HELP.detail.pollNowAction;
  const commandsDisabled = refreshing || deviceOffline;

  return (
    <PpSectionCard title="Métricas ao vivo" hint={PP_HELP.detail.liveMetrics}>
      {showConnectivityWarning ? (
        <DetailStatusBanner
          variant="warning"
          title={PP_HELP.detail.liveOfflineTitle}
          message={`${warningMessage} ${PP_HELP.detail.liveShowingCache} ${formatRelativeTime(recordedAt)}.`}
        />
      ) : null}
      <div className="pp-metric-hero">
        <p className="pp-metric-hero__value">
          {metricKey
            ? formatMetricValue(metricKey, rawValue).replace(` ${unit ?? ""}`, "").trim()
            : "—"}
        </p>
        {unit ? <p className="pp-metric-hero__unit">{unit}</p> : null}
        <p className="pp-metric-hero__label">{label}</p>
        <p className="pp-detail-muted">
          {showConnectivityWarning
            ? `${PP_HELP.detail.liveCacheLabel}: ${formatRelativeTime(recordedAt)}`
            : `Última leitura: ${formatRelativeTime(recordedAt)}`}{" "}
          · Poll: {device.pollIntervalMs} ms · {driverLabel(device.driverKey)}
        </p>
        <div className="pp-metric-hero__actions">
          <PpHintAction
            hint={PP_HELP.detail.refreshLive}
            ariaLabel={`Ajuda: ${PP_HELP.detail.refreshLiveAction}`}
          >
            <PpActionButton
              variant="ghost"
              className="pp-metric-hero__btn pp-metric-hero__btn--accent"
              onClick={onRefreshLive}
              disabled={refreshing}
            >
              <RefreshCw
                size={16}
                aria-hidden
                className={refreshing ? "pp-spin" : undefined}
              />
              {refreshLabel}
            </PpActionButton>
          </PpHintAction>
          <PpHintAction
            hint={PP_HELP.detail.pollNow}
            ariaLabel={`Ajuda: ${PP_HELP.detail.pollNowAction}`}
          >
            <PpActionButton
              variant="ghost"
              className="pp-metric-hero__btn pp-metric-hero__btn--info"
              onClick={onPollNow}
              disabled={refreshing}
            >
              <Radio size={16} aria-hidden />
              {pollLabel}
            </PpActionButton>
          </PpHintAction>
          {supportsReset && canCommand ? (
            <PpHintAction
              hint={PP_HELP.detail.resetCounter}
              ariaLabel={`Ajuda: ${PP_HELP.detail.resetCounterAction}`}
            >
              <PpActionButton
                variant="ghost"
                className="pp-metric-hero__btn pp-metric-hero__btn--warning"
                onClick={onReset}
                disabled={commandsDisabled}
              >
                <RotateCcw size={16} aria-hidden />
                {PP_HELP.detail.resetCounterAction}
              </PpActionButton>
            </PpHintAction>
          ) : null}
          {supportsFactoryReset && canCommand && onFactoryReset ? (
            <PpHintAction
              hint={PP_HELP.detail.factoryReset}
              ariaLabel={`Ajuda: ${PP_HELP.detail.factoryResetAction}`}
            >
              <PpActionButton
                variant="ghost"
                className="pp-metric-hero__btn pp-metric-hero__btn--danger"
                onClick={onFactoryReset}
                disabled={commandsDisabled}
              >
                <Factory size={16} aria-hidden />
                {PP_HELP.detail.factoryResetAction}
              </PpActionButton>
            </PpHintAction>
          ) : null}
        </div>
      </div>
    </PpSectionCard>
  );
}
