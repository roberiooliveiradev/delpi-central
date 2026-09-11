import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createFirmwareUpdateJob,
  fetchDeviceFirmwareSources,
  fetchDeviceFirmwareUpdateStatus,
  fetchFirmwares,
  type DeviceFirmwareSources,
  type DeviceFirmwareUpdateStatus,
  type FirmwareUpdateTarget,
} from "../../api/productionPulseApi";
import {
  PpActionButton,
  PpHintAction,
  PpProgressTracker,
  PpSectionCard,
  PpStateBox,
} from "../../app/productionPulseUi";
import { OtaTargetProgress } from "../ota/OtaTargetProgress";
import { productionPulseFirmwareLinksPath } from "../../constants/routes";
import { PP_HELP } from "../../content/helpTooltips";
import type { DeviceListItem } from "../../types/device";
import type { LivePollResult } from "../../types/detail";
import { latestPublishedFirmwareForFamily } from "../../utils/latestPublishedFirmware";
import { navigateProductionPulse } from "../../utils/navigation";
import {
  isOtaStatusActive,
  otaOperationLabel,
  otaStatusLabel,
} from "../../utils/otaStatusLabels";
import {
  otaActiveNoticeId,
  otaJobCreatedNoticeId,
  pushResolvedProductionPulseNotice,
} from "../../utils/pushResolvedNotice";
import { resolveProductionPulseError } from "../../utils/apiErrors";

type OperationalNotice = {
  id?: string;
  variant?: "error" | "warning" | "info" | "success";
  title?: string;
  message: string;
};

type DeviceFirmwareTabProps = {
  device: DeviceListItem;
  liveSnapshot?: LivePollResult | null;
  canManage: boolean;
  onUpdated?: () => void;
  /** Prefer hub monitor target when embedded in Admin Hub. */
  hubOtaTarget?: FirmwareUpdateTarget | null;
  /** Skip local status polling when hub monitor owns refresh. */
  suppressLocalPoll?: boolean;
  onOperationalNotice?: (notice: OperationalNotice) => void;
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

function SourceBlock({
  title,
  hint,
  block,
  emptyMessage,
  legacyBadge,
}: {
  title: string;
  hint: string;
  block: { available: boolean; sourceText?: string | null; version?: string | null; reason?: string | null };
  emptyMessage: string;
  legacyBadge?: boolean;
}) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const source = (block.sourceText ?? "").trim();

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

  const copyLabel =
    copyState === "copied"
      ? PP_HELP.detail.firmwareCopied
      : copyState === "failed"
        ? PP_HELP.detail.firmwareCopyFailed
        : PP_HELP.detail.firmwareCopy;

  return (
    <PpSectionCard
      title={title}
      hint={hint}
      actions={
        source ? (
          <PpActionButton variant="ghost" onClick={() => void handleCopy()}>
            {copyLabel}
          </PpActionButton>
        ) : undefined
      }
    >
      {legacyBadge ? (
        <p className="pp-lifecycle-badge pp-lifecycle-badge--legacy">{PP_HELP.detail.firmwareLegacyBadge}</p>
      ) : null}
      {!block.available || !source ? (
        <PpStateBox variant="empty" title="Indisponível" message={emptyMessage} />
      ) : (
        <>
          {block.version ? (
            <p className="pp-muted">
              Versão <code>{block.version}</code>
            </p>
          ) : null}
          <pre className="pp-firmware-source" tabIndex={0}>
            {source}
          </pre>
        </>
      )}
    </PpSectionCard>
  );
}

function statusFromHubTarget(
  target: FirmwareUpdateTarget,
): DeviceFirmwareUpdateStatus {
  return {
    active: isOtaStatusActive(target.status),
    jobId: target.jobId,
    targetId: target.id,
    status: target.status,
    fromVersion: target.fromVersion,
    toVersion: target.toVersion,
    errorCode: target.errorCode,
    bytesReceived: target.bytesReceived,
    bytesTotal: target.bytesTotal,
    progressPercent: target.progressPercent,
    updatedAt: target.updatedAt,
    wakeStatus: target.wakeStatus,
    wakeAttemptedAt: target.wakeAttemptedAt,
    wakeAcknowledgedAt: target.wakeAcknowledgedAt,
    wakeErrorCode: target.wakeErrorCode,
    target,
  };
}

export function DeviceFirmwareTab({
  device,
  liveSnapshot,
  canManage,
  onUpdated,
  hubOtaTarget,
  suppressLocalPoll = false,
  onOperationalNotice,
}: DeviceFirmwareTabProps) {
  const [sources, setSources] = useState<DeviceFirmwareSources | null>(null);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [otaBusy, setOtaBusy] = useState(false);
  const [otaMessage, setOtaMessage] = useState<string | null>(null);
  const [otaStatus, setOtaStatus] = useState<DeviceFirmwareUpdateStatus | null>(null);
  const [latestPublishedVersion, setLatestPublishedVersion] = useState<string | null>(null);

  const runningVersion =
    liveSnapshot?.firmwareVersion?.trim() ||
    device.installedFirmwareVersion ||
    "—";

  const refreshSources = useCallback(async () => {
    try {
      const next = await fetchDeviceFirmwareSources(device.id);
      setSources(next);
      setSourcesError(null);
    } catch (err) {
      setSourcesError(err instanceof Error ? err.message : PP_HELP.detail.firmwareSourcesFailed);
    }
  }, [device.id]);

  const refreshStatus = useCallback(async () => {
    if (hubOtaTarget) return;
    try {
      const next = await fetchDeviceFirmwareUpdateStatus(device.id);
      setOtaStatus(next);
    } catch {
      /* keep last */
    }
  }, [device.id, hubOtaTarget]);

  useEffect(() => {
    void refreshSources();
    void refreshStatus();
  }, [refreshSources, refreshStatus]);

  useEffect(() => {
    void fetchFirmwares({
      firmwareKey: device.firmwareKey || device.driverKey,
      publishedOnly: true,
    })
      .then((items) => {
        const latest = latestPublishedFirmwareForFamily(
          items,
          device.firmwareKey || device.driverKey,
        );
        setLatestPublishedVersion(latest?.version ?? null);
      })
      .catch(() => setLatestPublishedVersion(null));
  }, [device.driverKey, device.firmwareKey]);

  const effectiveStatus = hubOtaTarget
    ? statusFromHubTarget(hubOtaTarget)
    : otaStatus;

  useEffect(() => {
    if (suppressLocalPoll || hubOtaTarget) return;
    if (!effectiveStatus?.active && !isOtaStatusActive(effectiveStatus?.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshStatus();
      void refreshSources();
      onUpdated?.();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [
    effectiveStatus?.active,
    effectiveStatus?.status,
    hubOtaTarget,
    onUpdated,
    refreshSources,
    refreshStatus,
    suppressLocalPoll,
  ]);

  const emitNotice = (notice: OperationalNotice) => {
    if (onOperationalNotice) {
      onOperationalNotice(notice);
      return;
    }
    setOtaMessage(notice.message);
  };

  const handleUpdateDevice = async () => {
    if (!canManage) return;
    setOtaBusy(true);
    setOtaMessage(null);
    try {
      const firmwares = await fetchFirmwares({
        firmwareKey: device.firmwareKey || device.driverKey,
        publishedOnly: true,
      });
      const latest = latestPublishedFirmwareForFamily(
        firmwares,
        device.firmwareKey || device.driverKey,
      );
      if (!latest) {
        emitNotice({
          variant: "warning",
          title: PP_HELP.ota.noEligibleTitle,
          message: PP_HELP.ota.noPublishedFirmware,
        });
        return;
      }
      const job = await createFirmwareUpdateJob({
        firmwareId: latest.id,
        branch: device.branch,
        trigger: "manual",
        filter: {
          firmwareKey: latest.firmwareKey,
          onlyOutdated: true,
          deviceIds: [device.id],
        },
      });
      emitNotice({
        id: otaJobCreatedNoticeId(job.id),
        variant: "success",
        title: PP_HELP.ota.updateStartedTitle,
        message: PP_HELP.ota.deviceJobCreated,
      });
      await refreshStatus();
      onUpdated?.();
    } catch (err) {
      if (onOperationalNotice) {
        const resolved = resolveProductionPulseError(err);
        pushResolvedProductionPulseNotice(
          (notice) => {
            onOperationalNotice(
              typeof notice === "string" ? { message: notice } : notice,
            );
            return typeof notice === "string" ? notice : notice.message;
          },
          err,
          {
            id:
              resolved.code === "openTargetExists"
                ? otaActiveNoticeId(device.id)
                : undefined,
          },
        );
      } else {
        setOtaMessage(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
      }
    } finally {
      setOtaBusy(false);
    }
  };

  const status = effectiveStatus?.status ?? null;
  const showProgress = Boolean(status) && status !== "cancelled" && status !== "skipped";
  const trackerCurrentStepId = useMemo(() => {
    const s = (status || "").toLowerCase();
    if (s === "pending" || s === "authorized") return "authorized";
    if (s === "downloading") return "downloading";
    if (s === "applying") return "applying";
    if (s === "updated" || s === "failed") return "updated";
    return "authorized";
  }, [status]);

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

  const installedEmptyMessage =
    sources?.installedSource.reason === "missing_version"
      ? PP_HELP.detail.firmwareInstalledMissingVersion
      : sources?.installedSource.reason === "version_not_in_catalog"
        ? PP_HELP.detail.firmwareInstalledNotInCatalog
        : PP_HELP.detail.firmwareInstalledNoSource;

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
            <dt title={PP_HELP.detail.chipHealthPreviousVersion}>Anterior (no chip)</dt>
            <dd>
              <code>
                {liveSnapshot?.previousFirmwareVersion?.trim() || "—"}
              </code>
            </dd>
          </div>
          <div>
            <dt title={PP_HELP.detail.chipHealthLastOtaTarget}>Último alvo OTA (chip)</dt>
            <dd>
              <code>{liveSnapshot?.lastOtaTargetVersion?.trim() || "—"}</code>
            </dd>
          </div>
          <div>
            <dt>Instalada (cadastro)</dt>
            <dd>{device.installedFirmwareVersion ?? "—"}</dd>
          </div>
          <div>
            <dt>Alvo</dt>
            <dd>
              {effectiveStatus?.toVersion ??
                device.targetFirmwareVersion ??
                sources?.targetVersion ??
                "—"}
            </dd>
          </div>
          <div>
            <dt>Última publicada</dt>
            <dd>{latestPublishedVersion ?? "—"}</dd>
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
        </p>

        {showProgress ? (
          <div className="pp-ota-progress-block">
            <PpProgressTracker
              steps={trackerSteps}
              currentStepId={trackerCurrentStepId}
              density="compact"
            />
            <OtaTargetProgress
              status={status}
              errorCode={effectiveStatus?.errorCode}
              deviceOnline={device.status === "online"}
              wakeStatus={effectiveStatus?.wakeStatus}
              progressPercent={effectiveStatus?.progressPercent}
              bytesReceived={effectiveStatus?.bytesReceived}
              bytesTotal={effectiveStatus?.bytesTotal}
              updatedAt={effectiveStatus?.updatedAt}
            />
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
          {effectiveStatus?.jobId ? (
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
        {otaMessage && !onOperationalNotice ? <p className="pp-muted">{otaMessage}</p> : null}
      </PpSectionCard>

      {sourcesError ? <PpStateBox variant="error" title="Sketch" message={sourcesError} /> : null}

      {sources ? (
        <>
          <SourceBlock
            title="Sketch instalado"
            hint={PP_HELP.detail.firmwareInstalledSource}
            block={sources.installedSource}
            emptyMessage={installedEmptyMessage}
          />
          {sources.targetSource ? (
            <SourceBlock
              title="Sketch alvo"
              hint={PP_HELP.detail.firmwareTargetSource}
              block={sources.targetSource}
              emptyMessage={PP_HELP.detail.firmwareTargetNoSource}
            />
          ) : null}
          {sources.legacySource ? (
            <SourceBlock
              title="Sketch legado do dispositivo"
              hint={PP_HELP.detail.firmwareLegacySource}
              block={sources.legacySource}
              emptyMessage={PP_HELP.detail.firmwareEmpty}
              legacyBadge
            />
          ) : null}
        </>
      ) : (
        <PpStateBox variant="loading" title="Carregando sketches…" />
      )}
    </div>
  );
}
