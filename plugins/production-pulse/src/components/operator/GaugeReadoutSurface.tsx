import { useEffect, useState } from "react";

import { fetchOperatorDevice } from "../../api/productionPulseApi";
import { PpActionButton } from "../../app/productionPulseUi";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import { OperatorBrandBar } from "./OperatorBrandBar";
import type { OperatorDeviceItem } from "../../types/operator";
import { resolveDeviceActionMessage } from "../../utils/apiErrors";
import { PP_HELP } from "../../content/helpTooltips";
import {
  productionPulseOperatorPath,
  productionPulseOperatorPlacementPath,
} from "../../constants/routes";
import { navigateProductionPulse } from "../../utils/navigation";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import { formatMetricValue, metricLabel, metricUnit } from "../../utils/detailDisplay";
import { resolveMetricThresholdLevel, gaugeThresholdAriaLabel } from "../../utils/gaugeThresholds";
import { resolveOperatorHeaderTitle } from "../../utils/operatorDisplay";

type GaugeReadoutSurfaceProps = {
  deviceId: string;
  branch: string;
  placementKey?: string;
  placementLabel?: string;
  initialDevice: OperatorDeviceItem;
};

export function GaugeReadoutSurface({
  deviceId,
  branch,
  placementKey,
  placementLabel,
  initialDevice,
}: GaugeReadoutSurfaceProps) {
  const [device, setDevice] = useState(initialDevice);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const intervalMs = Math.max(5000, (device.pollIntervalSeconds ?? 30) * 1000);
    const timer = window.setInterval(() => {
      fetchOperatorDevice(deviceId)
        .then(setDevice)
        .catch(() => undefined);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [device.pollIntervalSeconds, deviceId]);

  const syncNow = async () => {
    setBusy(true);
    setError(null);
    try {
      setDevice(await fetchOperatorDevice(deviceId));
    } catch (err) {
      setError(resolveDeviceActionMessage(err, "Erro ao sincronizar."));
    } finally {
      setBusy(false);
    }
  };

  const goBack = () => {
    if (placementKey) {
      navigateProductionPulse(productionPulseOperatorPlacementPath(placementKey, branch));
      return;
    }
    navigateProductionPulse(productionPulseOperatorPath(branch));
  };

  const metricKeys = device.capabilities?.metrics?.length
    ? device.capabilities.metrics
    : Object.keys(device.lastMetrics ?? {});

  return (
    <div className="pp-operator-surface pp-gauge-readout">
      <OperatorBrandBar
        branch={branch}
        title={resolveOperatorHeaderTitle(device, placementLabel)}
        subtitle={`${device.name} · ${formatRelativeTime(device.lastSeenAt)}`}
        trailing={
          <PpActionButton
            variant="ghost"
            className="pp-operator-hero-btn"
            onClick={goBack}
            title={PP_HELP.operator.changePlacement}
          >
            Trocar posto
          </PpActionButton>
        }
      />

      {!device.online ? (
        <div className="pp-operator-offline-banner" role="status">
          {PP_HELP.operator.offlineBanner}
        </div>
      ) : null}

      {error ? <p className="pp-detail-error">{error}</p> : null}

      <div className="pp-gauge-readout__grid">
        {metricKeys.map((key) => {
          const level = resolveMetricThresholdLevel(
            key,
            device.lastMetrics?.[key],
            device.capabilities?.thresholds,
          );
          const thresholdHint = gaugeThresholdAriaLabel(level);
          return (
            <div
              key={key}
              className={`pp-gauge-readout__tile${
                level === "warn"
                  ? " pp-gauge-readout__tile--warn"
                  : level === "danger"
                    ? " pp-gauge-readout__tile--danger"
                    : ""
              }`}
              aria-label={
                thresholdHint
                  ? `${metricLabel(key)}: ${formatMetricValue(key, device.lastMetrics?.[key])}. ${thresholdHint}`
                  : undefined
              }
            >
            <p className="pp-gauge-readout__value">
              {formatMetricValue(key, device.lastMetrics?.[key])
                .replace(` ${metricUnit(key) ?? ""}`, "")
                .trim()}
            </p>
            {metricUnit(key) ? <p className="pp-gauge-readout__unit">{metricUnit(key)}</p> : null}
            <p className="pp-gauge-readout__label">{metricLabel(key)}</p>
          </div>
          );
        })}
      </div>

      <div className="pp-gauge-readout__footer">
        <DeviceStatusBadge status={device.status} />
        <PpActionButton
          variant="ghost"
          className="pp-gauge-readout__sync-btn"
          onClick={() => void syncNow()}
          disabled={busy}
        >
          {busy ? "Atualizando…" : "Atualizar"}
        </PpActionButton>
      </div>
    </div>
  );
}
