import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createFirmwareUpdateJob,
  fetchDeviceFirmwareUpdateStatus,
  fetchFirmwares,
  type DeviceFirmwareUpdateStatus,
} from "../../api/productionPulseApi";
import {
  PpActionButton,
  PpHintAction,
  PpOtaProgressBar,
  PpProgressTracker,
  PpSectionCard,
  PpStateBox,
} from "../../app/productionPulseUi";
import { productionPulseFirmwareLinksPath } from "../../constants/routes";
import { PP_HELP } from "../../content/helpTooltips";
import type { DeviceListItem } from "../../types/device";
import type { LivePollResult } from "../../types/detail";
import { navigateProductionPulse } from "../../utils/navigation";
import {
  formatOtaBytes,
  formatOtaProgressDisplay,
  isOtaStatusActive,
  otaOperationLabel,
  otaStatusLabel,
  resolveOtaProgressPercent,
} from "../../utils/otaStatusLabels";

type DeviceFirmwareTabProps = {
  device: DeviceListItem;
  liveSnapshot?: LivePollResult | null;
  canManage: boolean;
  onUpdated?: () => void;
};

const POLL_MS = 2500;

function stepState(
  status: string | null | undefined,
  step: "authorized" | "downloading" | "applying" | "updated",
): "complete" | "current" | "available" | "locked" | "error" {
  const s = (status || "").toLowerCase();
  if (s === "failed" && step === "updated") return "error";
  const order = ["authorized", "downloading", "applying", "updated"] as const;
  const idx = order.indexOf(step);
  let currentIdx = 0;
  if (s === "pending") currentIdx = -1;
  else if (s === "authorized") currentIdx = 0;
  else if (s === "downloading") currentIdx = 1;
  else if (s === "applying") currentIdx = 2;
  else if (s === "updated") currentIdx = 3;
  else if (s === "failed") currentIdx = 1;
  if (currentIdx < 0) return "locked";
  if (idx < currentIdx) return "complete";
  if (idx === currentIdx) return s === "failed" ? "error" : "current";
  return "available";
}

export function DeviceFirmwareTab({
  device,
  liveSnapshot,
  canManage,
  onUpdated,
}: DeviceFirmwareTabProps) {
  const source = (device.firmwareSource ?? "").trim() ? device.firmwareSource ?? "" : "";
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const [otaBusy, setOtaBusy] = useState(false);
  const [otaMessage, setOtaMessage] = useState<string | null>(null);
  const [otaStatus, setOtaStatus] = useState<DeviceFirmwareUpdateStatus | null>(null);

  const runningVersion =
    liveSnapshot?.firmwareVersion?.trim() ||
    device.installedFirmwareVersion ||
    "—";

  const refreshStatus = useCallback(async () => {
    try {
      const next = await fetchDeviceFirmwareUpdateStatus(device.id);
      setOtaStatus(next);
    } catch {
      /* keep last */
    }
  }, [device.id]);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    if (!otaStatus?.active && !isOtaStatusActive(otaStatus?.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshStatus();
      onUpdated?.();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [otaStatus?.active, otaStatus?.status, refreshStatus, onUpdated]);

  const handleCopy = async () => {
    if (!source) return;
    try {
      await navigator.clipboard.writeText(source);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("failed");
    }
  };

  const handleUpdateDevice = async () => {
    if (!canManage) return;
    setOtaBusy(true);
    setOtaMessage(null);
    try {
      const firmwares = await fetchFirmwares({
        firmwareKey: device.firmwareKey || device.driverKey,
      });
      const latest = firmwares.find((item) => item.publishedAt);
      if (!latest) {
        setOtaMessage(PP_HELP.ota.noPublishedFirmware);
        return;
      }
      await createFirmwareUpdateJob({
        firmwareId: latest.id,
        branch: device.branch,
        trigger: "manual",
        filter: {
          firmwareKey: latest.firmwareKey,
          onlyOutdated: true,
          deviceIds: [device.id],
        },
      });
      setOtaMessage(PP_HELP.ota.deviceJobCreated);
      await refreshStatus();
      onUpdated?.();
    } catch (err) {
      setOtaMessage(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
    } finally {
      setOtaBusy(false);
    }
  };

  const copyLabel =
    copyState === "copied"
      ? PP_HELP.detail.firmwareCopied
      : copyState === "failed"
        ? PP_HELP.detail.firmwareCopyFailed
        : PP_HELP.detail.firmwareCopy;

  const status = otaStatus?.status ?? null;
  const progress = resolveOtaProgressPercent({
    status,
    progressPercent: otaStatus?.progressPercent,
  });
  const progressDisplay = formatOtaProgressDisplay({
    status,
    progressPercent: otaStatus?.progressPercent,
  });
  const bytesLabel = formatOtaBytes(otaStatus?.bytesReceived, otaStatus?.bytesTotal);
  const showProgress = Boolean(status) && status !== "cancelled" && status !== "skipped";
  const showPercentBar = typeof progress === "number";

  const trackerSteps = useMemo(
    () => [
      {
        id: "authorized",
        label: PP_HELP.ota.status.authorized,
        state: stepState(status, "authorized"),
      },
      {
        id: "downloading",
        label: PP_HELP.ota.status.downloading,
        state: stepState(status, "downloading"),
      },
      {
        id: "applying",
        label: PP_HELP.ota.status.applying,
        state: stepState(status, "applying"),
      },
      {
        id: "updated",
        label: PP_HELP.ota.status.updated,
        state: stepState(status, "updated"),
      },
    ],
    [status],
  );

  return (
    <div className="pp-page-stack">
      <PpSectionCard title="Versão e atualização OTA" hint={PP_HELP.ota.deviceVersionCard}>
        <dl className="pp-definition-list">
          <div>
            <dt title={PP_HELP.ota.runningVersion}>Em execução</dt>
            <dd>
              <code>{runningVersion}</code>
            </dd>
          </div>
          <div>
            <dt>Instalada (cadastro)</dt>
            <dd>{device.installedFirmwareVersion ?? "—"}</dd>
          </div>
          <div>
            <dt>Alvo</dt>
            <dd>{otaStatus?.toVersion ?? device.targetFirmwareVersion ?? "—"}</dd>
          </div>
          <div>
            <dt>Família</dt>
            <dd>
              <code>{device.firmwareKey || device.driverKey}</code>
            </dd>
          </div>
        </dl>

        <p className="pp-muted" title={PP_HELP.ota.progressPhases}>
          <strong>Operação:</strong> {otaOperationLabel(status)}
          {status ? ` (${otaStatusLabel(status)})` : null}
          {otaStatus?.errorCode ? ` · ${otaStatus.errorCode}` : null}
        </p>

        {showProgress ? (
          <div className="pp-ota-progress-block">
            <PpProgressTracker steps={trackerSteps} density="compact" />
            <p className="pp-muted" title={PP_HELP.ota.awaitingChip}>
              <strong>Progresso:</strong> {progressDisplay}
              {bytesLabel ? ` · ${bytesLabel}` : null}
            </p>
            {showPercentBar ? (
              <PpOtaProgressBar
                value={progress ?? 0}
                label={PP_HELP.ota.downloadProgress}
                summary={bytesLabel ?? undefined}
              />
            ) : null}
          </div>
        ) : null}

        <div className="pp-form-actions">
          {canManage ? (
            <PpHintAction hint={PP_HELP.ota.deviceJobCreated} ariaLabel="Ajuda: Atualizar este device">
              <PpActionButton onClick={() => void handleUpdateDevice()} disabled={otaBusy}>
                {otaBusy ? "Disparando…" : "Atualizar este device"}
              </PpActionButton>
            </PpHintAction>
          ) : null}
          {otaStatus?.jobId ? (
            <PpActionButton
              variant="ghost"
              onClick={() =>
                navigateProductionPulse(productionPulseFirmwareLinksPath({ branch: device.branch }))
              }
            >
              Ver hub OTA
            </PpActionButton>
          ) : null}
        </div>
        {otaMessage ? <p className="pp-muted">{otaMessage}</p> : null}
      </PpSectionCard>

      {!source ? (
        <PpSectionCard title="Firmware (.ino)">
          <PpStateBox
            variant="empty"
            title="Sem sketch cadastrado"
            message={PP_HELP.detail.firmwareEmpty}
          />
        </PpSectionCard>
      ) : (
        <PpSectionCard
          title="Firmware (.ino)"
          actions={
            <PpActionButton variant="ghost" onClick={() => void handleCopy()}>
              {copyLabel}
            </PpActionButton>
          }
        >
          <pre className="pp-firmware-source" tabIndex={0}>
            {source}
          </pre>
        </PpSectionCard>
      )}
    </div>
  );
}
