import { useState } from "react";

import {
  createFirmwareUpdateJob,
  fetchFirmwares,
} from "../../api/productionPulseApi";
import { PpActionButton, PpSectionCard, PpStateBox } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import type { DeviceListItem } from "../../types/device";

type DeviceFirmwareTabProps = {
  device: DeviceListItem;
  canManage: boolean;
  onUpdated?: () => void;
};

export function DeviceFirmwareTab({ device, canManage, onUpdated }: DeviceFirmwareTabProps) {
  const source = (device.firmwareSource ?? "").trim() ? device.firmwareSource ?? "" : "";
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const [otaBusy, setOtaBusy] = useState(false);
  const [otaMessage, setOtaMessage] = useState<string | null>(null);

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

  return (
    <div className="pp-page-stack">
      <PpSectionCard title="Versão OTA" hint={PP_HELP.ota.deviceVersionCard}>
        <dl className="pp-definition-list">
          <div>
            <dt>Família</dt>
            <dd>
              <code>{device.firmwareKey || device.driverKey}</code>
            </dd>
          </div>
          <div>
            <dt>Instalada</dt>
            <dd>{device.installedFirmwareVersion ?? "—"}</dd>
          </div>
          <div>
            <dt>Alvo</dt>
            <dd>{device.targetFirmwareVersion ?? "—"}</dd>
          </div>
        </dl>
        {canManage ? (
          <PpActionButton onClick={() => void handleUpdateDevice()} disabled={otaBusy}>
            {otaBusy ? "Disparando…" : "Atualizar este device"}
          </PpActionButton>
        ) : null}
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
