import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createFirmwareUpdateJob,
  fetchDeviceFirmwareSources,
  fetchDeviceFirmwareUpdateStatus,
  fetchFirmwares,
  type DeviceFirmwareSources,
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

export function DeviceFirmwareTab({
  device,
  liveSnapshot,
  canManage,
  onUpdated,
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
    try {
      const next = await fetchDeviceFirmwareUpdateStatus(device.id);
      setOtaStatus(next);
    } catch {
      /* keep last */
    }
  }, [device.id]);

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
        const latest = items.find((item) => item.lifecycle === "published" && !item.archivedAt);
        setLatestPublishedVersion(latest?.version ?? null);
      })
      .catch(() => setLatestPublishedVersion(null));
  }, [device.driverKey, device.firmwareKey]);

  useEffect(() => {
    if (!otaStatus?.active && !isOtaStatusActive(otaStatus?.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshStatus();
      void refreshSources();
      onUpdated?.();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [otaStatus?.active, otaStatus?.status, refreshStatus, refreshSources, onUpdated]);

  const handleUpdateDevice = async () => {
    if (!canManage) return;
    setOtaBusy(true);
    setOtaMessage(null);
    try {
      const firmwares = await fetchFirmwares({
        firmwareKey: device.firmwareKey || device.driverKey,
        publishedOnly: true,
      });
      const latest = firmwares.find((item) => item.lifecycle === "published" && !item.archivedAt);
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
            <dt>Instalada (cadastro)</dt>
            <dd>{device.installedFirmwareVersion ?? "—"}</dd>
          </div>
          <div>
            <dt>Alvo</dt>
            <dd>{otaStatus?.toVersion ?? device.targetFirmwareVersion ?? sources?.targetVersion ?? "—"}</dd>
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
