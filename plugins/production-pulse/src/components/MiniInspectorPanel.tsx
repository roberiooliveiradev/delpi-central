import { useEffect, useState } from "react";

import {
  disableDevice,
  fetchDevice,
  replaceDevice,
  type FirmwareListItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpHostContainedDialog,
  PpNativeTextField,
  PpStateBox,
} from "../app/productionPulseUi";
import type { DeviceListItem } from "../types/device";
import type { AdminEntityRef } from "../utils/adminHubUiState";
import { AdminSidePanel } from "./AdminSidePanel";
import { OtaStatusIndicator } from "./ota/OtaStatusIndicator";

type MiniInspectorPanelProps = {
  open: boolean;
  entity: AdminEntityRef | null;
  device?: DeviceListItem | null;
  firmware?: FirmwareListItem | null;
  onClose: () => void;
  onEdit?: () => void;
};

export function MiniInspectorPanel({
  open,
  entity,
  device,
  firmware,
  onClose,
  onEdit,
}: MiniInspectorPanelProps) {
  if (!entity) return null;

  const title =
    entity.type === "device"
      ? device?.name ?? "IoT"
      : entity.type === "firmware"
        ? firmware?.displayName || firmware?.firmwareKey || "Firmware"
        : "Detalhe";

  return (
    <AdminSidePanel open={open} title={title} onClose={onClose}>
      {entity.type === "device" && device ? (
        <div className="pp-mini-inspector">
          <dl className="pp-mini-inspector__dl">
            <dt>Status</dt>
            <dd>{device.status}</dd>
            <dt>Versão instalada</dt>
            <dd>{device.installedFirmwareVersion ?? "—"}</dd>
            <dt>Versão disponível</dt>
            <dd>{device.targetFirmwareVersion ?? "—"}</dd>
            <dt>Última leitura</dt>
            <dd>{device.lastSeenAt ? new Date(device.lastSeenAt).toLocaleString() : "—"}</dd>
            <dt>Driver</dt>
            <dd>{device.driverKey}</dd>
            <dt>Filial</dt>
            <dd>{device.branch}</dd>
            <dt>Papel</dt>
            <dd>{device.roleKey}</dd>
            <dt>IP</dt>
            <dd>{device.ipAddress}</dd>
            <dt>Intervalo de leitura</dt>
            <dd>{device.pollIntervalMs} ms</dd>
            <dt>Golpes</dt>
            <dd>{String(device.lastMetrics?.counter ?? "—")}</dd>
            <dt>Hoje / turno</dt>
            <dd>
              +{device.periodDeltas?.day?.counter ?? 0} / +
              {device.periodDeltas?.shift?.counter ?? 0}
            </dd>
          </dl>
          {onEdit ? <PpActionButton onClick={onEdit}>Editar</PpActionButton> : null}
        </div>
      ) : null}
      {entity.type === "firmware" && firmware ? (
        <div className="pp-mini-inspector">
          <dl className="pp-mini-inspector__dl">
            <dt>Família</dt>
            <dd>
              <code>{firmware.firmwareKey}</code>
            </dd>
            <dt>Versão</dt>
            <dd>{firmware.version}</dd>
            <dt>Estado</dt>
            <dd>{firmware.lifecycle}</dd>
            <dt>Sketch</dt>
            <dd>{firmware.hasSource ? "Sim" : "Não"}</dd>
            <dt>Binário</dt>
            <dd>{firmware.hasArtifact ? "Sim" : "Não"}</dd>
            <dt>Publicado</dt>
            <dd>
              {firmware.publishedAt ? new Date(firmware.publishedAt).toLocaleString() : "—"}
            </dd>
          </dl>
          {onEdit ? <PpActionButton onClick={onEdit}>Abrir edição</PpActionButton> : null}
        </div>
      ) : null}
      {entity.type === "job" ? (
        <PpStateBox
          variant="empty"
          title="Job"
          message="Use o painel Jobs OTA para progresso e targets."
        />
      ) : null}
    </AdminSidePanel>
  );
}

type RenameDeviceDialogProps = {
  open: boolean;
  device: DeviceListItem | null;
  onClose: () => void;
  onRenamed: () => void;
};

export function RenameDeviceDialog({
  open,
  device,
  onClose,
  onRenamed,
}: RenameDeviceDialogProps) {
  const [name, setName] = useState(device?.name ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(device?.name ?? "");
    setError(null);
  }, [device]);

  const save = async () => {
    if (!device || !name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const full = await fetchDevice(device.id);
      await replaceDevice(device.id, {
        name: name.trim(),
        branch: full.branch,
        ipAddress: full.ipAddress,
        controllerCode: full.controllerCode ?? "",
        firmwareSource: full.firmwareSource ?? "",
        wifiSsid: full.wifiSsid ?? "",
        wifiPassword: "",
        debounceMs: full.debounceMs != null ? String(full.debounceMs) : "",
        apiToken: "",
        apiTokenSet: Boolean(full.apiTokenSet),
        driverKey: full.driverKey,
        pollIntervalMs: full.pollIntervalMs,
        enabled: full.enabled,
      });
      onRenamed();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao renomear.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <PpHostContainedDialog open={open} title="Renomear IoT" onClose={onClose}>
      <PpNativeTextField id="rename-iot" label="Nome" value={name} onChange={setName} />
      {error ? <PpStateBox variant="error" title="Erro" message={error} /> : null}
      <div className="pp-inline-actions">
        <PpActionButton variant="ghost" onClick={onClose}>
          Cancelar
        </PpActionButton>
        <PpActionButton disabled={busy || !name.trim()} onClick={() => void save()}>
          Salvar
        </PpActionButton>
      </div>
    </PpHostContainedDialog>
  );
}

type ConfirmDisableDialogProps = {
  open: boolean;
  device: DeviceListItem | null;
  onClose: () => void;
  onDone: () => void;
};

export function ConfirmDisableDialog({
  open,
  device,
  onClose,
  onDone,
}: ConfirmDisableDialogProps) {
  const [busy, setBusy] = useState(false);
  return (
    <PpHostContainedDialog open={open} title="Desativar IoT" onClose={onClose}>
      <p>Desativar {device?.name}? O dispositivo deixa de ser operado (soft-disable).</p>
      <div className="pp-inline-actions">
        <PpActionButton variant="ghost" onClick={onClose}>
          Voltar
        </PpActionButton>
        <PpActionButton
          disabled={busy || !device}
          onClick={() => {
            if (!device) return;
            setBusy(true);
            void disableDevice(device.id)
              .then(() => {
                onDone();
                onClose();
              })
              .finally(() => setBusy(false));
          }}
        >
          Desativar
        </PpActionButton>
      </div>
    </PpHostContainedDialog>
  );
}

export function OtaProgressSnippet(props: {
  status: string;
  progressPercent: number | null | undefined;
  errorCode?: string | null;
  deviceOnline?: boolean | null;
}) {
  return (
    <div className="pp-ota-progress-snippet">
      <OtaStatusIndicator
        status={props.status}
        errorCode={props.errorCode}
        deviceOnline={props.deviceOnline}
        progressPercent={props.progressPercent}
        density="compact"
      />
    </div>
  );
}
