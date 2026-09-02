import { useEffect, useState } from "react";
import { Eraser, Minus, Plus } from "lucide-react";

import { executeOperatorCommand, fetchOperatorDevice } from "../../api/productionPulseApi";
import { PpActionButton } from "../../app/productionPulseUi";
import { OperatorClearCounterModal } from "../modals/OperatorClearCounterModal";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import { OperatorBrandBar } from "./OperatorBrandBar";
import type { OperatorDeviceItem } from "../../types/operator";
import { PP_HELP } from "../../content/helpTooltips";
import { resolveDeviceActionMessage } from "../../utils/apiErrors";
import { navigateOperatorPlacementHub } from "../../utils/operatorNavigation";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import {
  formatMetricValue,
  metricUnit,
  primaryMetricKey,
} from "../../utils/detailDisplay";
import {
  metricDisplayLabel,
  resolveOperatorHeaderTitle,
} from "../../utils/operatorDisplay";
import { resolveOperatorRefreshIntervalMs } from "../../utils/operatorRefreshInterval";

type CounterPadSurfaceProps = {
  deviceId: string;
  branch: string;
  placementKey?: string;
  placementLabel?: string;
  initialDevice: OperatorDeviceItem;
};

export function CounterPadSurface({
  deviceId,
  branch,
  placementLabel,
  initialDevice,
}: CounterPadSurfaceProps) {
  const [device, setDevice] = useState(initialDevice);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clearOpen, setClearOpen] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);

  const metricKey = primaryMetricKey(device.lastMetrics, device.capabilities) ?? "counter";
  const metricValue = formatMetricValue(metricKey, device.lastMetrics[metricKey])
    .replace(` ${metricUnit(metricKey) ?? ""}`, "")
    .trim();
  const unit = metricUnit(metricKey);
  const commandsDisabled = busy || !device.online;

  useEffect(() => {
    const intervalMs = resolveOperatorRefreshIntervalMs(device.pollIntervalMs);
    const timer = window.setInterval(() => {
      fetchOperatorDevice(deviceId)
        .then(setDevice)
        .catch(() => undefined);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [device.pollIntervalMs, deviceId]);

  const applyMetrics = (metrics?: Record<string, number | string>) => {
    if (!metrics) return;
    setDevice((current) => ({
      ...current,
      lastMetrics: metrics,
      lastSeenAt: new Date().toISOString(),
      online: true,
      status: "online",
    }));
  };

  const runCommand = async (commandKey: string) => {
    setBusy(true);
    setError(null);
    try {
      const result = await executeOperatorCommand(deviceId, commandKey);
      if (!result.success) {
        setError(result.errorMessage ?? "Comando não concluído.");
        return;
      }
      applyMetrics(result.metrics);
    } catch (err) {
      setError(resolveDeviceActionMessage(err, "Erro ao enviar comando."));
    } finally {
      setBusy(false);
    }
  };

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

  const confirmClear = async () => {
    setClearLoading(true);
    setClearError(null);
    try {
      const result = await executeOperatorCommand(deviceId, "reset");
      if (!result.success) {
        setClearError(result.errorMessage ?? "Não foi possível zerar.");
        return;
      }
      applyMetrics(result.metrics);
      setClearOpen(false);
    } catch (err) {
      setClearError(resolveDeviceActionMessage(err, "Erro ao zerar contador."));
    } finally {
      setClearLoading(false);
    }
  };

  const statusLine = `${device.name} · ${formatRelativeTime(device.lastSeenAt)}`;

  return (
    <div className="pp-operator-surface pp-counter-pad">
      <OperatorBrandBar
        branch={branch}
        title={resolveOperatorHeaderTitle(device, placementLabel)}
        subtitle={statusLine}
        trailing={
          <PpActionButton
            variant="ghost"
            className="pp-operator-hero-btn"
            onClick={() => navigateOperatorPlacementHub(branch)}
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

      <div className="pp-counter-pad__workspace">
        <div className={`pp-counter-pad__stage${device.online ? "" : " pp-counter-pad__stage--muted"}`}>
          <p className="pp-counter-pad__value">{metricValue}</p>
          {unit ? <p className="pp-counter-pad__unit">{unit}</p> : null}
          <p className="pp-counter-pad__label">{metricDisplayLabel(device)}</p>
          <DeviceStatusBadge status={device.status} />
        </div>

        <div className="pp-counter-pad__controls">
          <div className="pp-counter-pad__pad-host">
            <div
              className={`pp-counter-pad__pad${commandsDisabled ? " pp-counter-pad__pad--disabled" : ""}`}
            >
              <PpActionButton
                variant="primary"
                className="pp-counter-pad__btn pp-counter-pad__btn--increment pp-counter-pad__btn--accent"
                disabled={commandsDisabled}
                onClick={() => void runCommand("increment")}
                title={PP_HELP.operator.counterIncrement}
              >
                <Plus size={32} aria-hidden="true" />
                <span className="pp-counter-pad__btn-label pp-counter-pad__btn-label--long">Aumentar golpe</span>
                <span className="pp-counter-pad__btn-label pp-counter-pad__btn-label--short">Aumentar</span>
              </PpActionButton>
              <PpActionButton
                variant="ghost"
                className="pp-counter-pad__btn pp-counter-pad__btn--decrement"
                disabled={commandsDisabled}
                onClick={() => void runCommand("decrement")}
                title={PP_HELP.operator.counterDecrement}
              >
                <Minus size={32} aria-hidden="true" />
                <span className="pp-counter-pad__btn-label">Diminuir</span>
              </PpActionButton>
              <PpActionButton
                variant="ghost"
                className="pp-counter-pad__btn pp-counter-pad__btn--clear pp-counter-pad__btn--warn"
                disabled={commandsDisabled}
                onClick={() => setClearOpen(true)}
                title={PP_HELP.operator.counterClear}
              >
                <Eraser size={32} aria-hidden="true" />
                <span className="pp-counter-pad__btn-label">Limpar</span>
              </PpActionButton>
            </div>
          </div>

          <div className="pp-counter-pad__sync">
            <PpActionButton
              variant="ghost"
              className="pp-counter-pad__sync-btn"
              onClick={() => void syncNow()}
              disabled={busy}
            >
              {busy ? "Sincronizando…" : "Sincronizar agora"}
            </PpActionButton>
          </div>
        </div>
      </div>

      <OperatorClearCounterModal
        open={clearOpen}
        loading={clearLoading}
        error={clearError}
        onConfirm={() => void confirmClear()}
        onClose={() => {
          if (clearLoading) return;
          setClearOpen(false);
          setClearError(null);
        }}
      />
    </div>
  );
}
