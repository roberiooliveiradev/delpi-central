import { useEffect, useState } from "react";
import { Eraser, Minus, Plus } from "lucide-react";

import { executeOperatorCommand, fetchOperatorDevice } from "../../api/productionPulseApi";
import { PpActionButton } from "../../app/productionPulseUi";
import { OperatorClearCounterModal } from "../modals/OperatorClearCounterModal";
import { DeviceStatusBadge } from "../DeviceStatusBadge";
import { OperatorBrandBar } from "./OperatorBrandBar";
import type { OperatorDeviceItem } from "../../types/operator";
import { PP_HELP } from "../../content/helpTooltips";
import {
  productionPulseOperatorPath,
  productionPulseOperatorPlacementPath,
} from "../../constants/routes";
import { useViewportBucket } from "../../hooks/useViewportBucket";
import { navigateProductionPulse } from "../../utils/navigation";
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
  placementKey,
  placementLabel,
  initialDevice,
}: CounterPadSurfaceProps) {
  const viewport = useViewportBucket();
  const portraitStack = viewport === "mobile";
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
    const intervalMs = Math.max(5000, (device.pollIntervalSeconds ?? 30) * 1000);
    const timer = window.setInterval(() => {
      fetchOperatorDevice(deviceId)
        .then(setDevice)
        .catch(() => undefined);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [device.pollIntervalSeconds, deviceId]);

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
      setError(err instanceof Error ? err.message : "Erro ao enviar comando.");
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
      setError(err instanceof Error ? err.message : "Erro ao sincronizar.");
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
      setClearError(err instanceof Error ? err.message : "Erro ao zerar contador.");
    } finally {
      setClearLoading(false);
    }
  };

  const goBack = () => {
    if (placementKey) {
      navigateProductionPulse(productionPulseOperatorPlacementPath(placementKey, branch));
      return;
    }
    navigateProductionPulse(productionPulseOperatorPath(branch));
  };

  const statusLine = `${device.name} · ${formatRelativeTime(device.lastSeenAt)}`;

  return (
    <div className="pp-operator-surface pp-counter-pad">
      <OperatorBrandBar
        branch={branch}
        title={resolveOperatorHeaderTitle(device, placementLabel)}
        subtitle={statusLine}
        trailing={
          <PpActionButton variant="ghost" className="pp-operator-brand-bar__btn" onClick={goBack}>
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

      <div className={`pp-counter-pad__stage${device.online ? "" : " pp-counter-pad__stage--muted"}`}>
        <p className="pp-counter-pad__value">{metricValue}</p>
        {unit ? <p className="pp-counter-pad__unit">{unit}</p> : null}
        <p className="pp-counter-pad__label">{metricDisplayLabel(device)}</p>
        <DeviceStatusBadge status={device.status} />
      </div>

      <div
        className={`pp-counter-pad__pad${portraitStack ? " pp-counter-pad__pad--stack" : ""}${commandsDisabled ? " pp-counter-pad__pad--disabled" : ""}`}
      >
        {portraitStack ? (
          <>
            <PpActionButton
              variant="primary"
              className="pp-counter-pad__btn pp-counter-pad__btn--primary-full"
              disabled={commandsDisabled}
              onClick={() => void runCommand("increment")}
              title={PP_HELP.operator.counterIncrement}
            >
              <Plus size={28} aria-hidden="true" /> Aumentar golpe
            </PpActionButton>
            <div className="pp-counter-pad__row">
              <PpActionButton
                variant="ghost"
                className="pp-counter-pad__btn"
                disabled={commandsDisabled}
                onClick={() => void runCommand("decrement")}
                title={PP_HELP.operator.counterDecrement}
              >
                <Minus size={24} aria-hidden="true" /> Diminuir
              </PpActionButton>
              <PpActionButton
                variant="ghost"
                className="pp-counter-pad__btn pp-counter-pad__btn--warn"
                disabled={commandsDisabled}
                onClick={() => setClearOpen(true)}
                title={PP_HELP.operator.counterClear}
              >
                <Eraser size={24} aria-hidden="true" /> Limpar
              </PpActionButton>
            </div>
          </>
        ) : (
          <>
            <PpActionButton
              variant="ghost"
              className="pp-counter-pad__btn"
              disabled={commandsDisabled}
              onClick={() => void runCommand("decrement")}
              title={PP_HELP.operator.counterDecrement}
            >
              <Minus size={32} aria-hidden="true" />
              <span>Diminuir</span>
            </PpActionButton>
            <PpActionButton
              variant="ghost"
              className="pp-counter-pad__btn pp-counter-pad__btn--warn"
              disabled={commandsDisabled}
              onClick={() => setClearOpen(true)}
              title={PP_HELP.operator.counterClear}
            >
              <Eraser size={32} aria-hidden="true" />
              <span>Limpar</span>
            </PpActionButton>
            <PpActionButton
              variant="primary"
              className="pp-counter-pad__btn pp-counter-pad__btn--accent"
              disabled={commandsDisabled}
              onClick={() => void runCommand("increment")}
              title={PP_HELP.operator.counterIncrement}
            >
              <Plus size={32} aria-hidden="true" />
              <span>Aumentar</span>
            </PpActionButton>
          </>
        )}
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
