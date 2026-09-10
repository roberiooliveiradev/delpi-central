import {
  Archive,
  CalendarClock,
  Cpu,
  FileCode,
  FilePenLine,
  FilePlus2,
  Link2,
  Link2Off,
  MoreHorizontal,
  Package,
  Pencil,
  Power,
  PowerOff,
  RefreshCw,
  TextCursorInput,
  Upload,
} from "lucide-react";
import { useEffect, useRef } from "react";

import {
  AnchoredPanelPortal,
  ContextMenuDivider,
  PpActionButton,
  PpContextMenuItem,
  PpHintAction,
  PpIconButton,
} from "../app/productionPulseUi";
import type { FirmwareListItem } from "../api/productionPulseApi";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import type { AdminEntityRef } from "../utils/adminHubUiState";
import { explicitFirmwareKey } from "../utils/firmwareLinkGraph";
import { isPublishedFirmware } from "../utils/hubOtaKpis";

const POPOVER_SURFACE = "delpi-ui-popover-surface";

function deviceStatusLabel(device: DeviceListItem): string {
  if (device.status === "online") return "● Online";
  if (device.status === "offline") return "● Offline";
  if (!device.enabled) return "● Inativo";
  return "● —";
}

function firmwareLifecycleLabel(firmware: FirmwareListItem | null | undefined): string {
  if (!firmware) return "—";
  if (isPublishedFirmware(firmware)) return "Publicado";
  if (firmware.lifecycle === "draft") return "Rascunho";
  return "Arquivado";
}

type EntitySummaryPopoverProps = {
  open: boolean;
  anchorEl: HTMLElement | null;
  entity: AdminEntityRef | null;
  device?: DeviceListItem | null;
  firmware?: FirmwareListItem | null;
  firmwareMeta?: {
    displayName: string;
    firmwareKey: string;
    version: string | null;
    linkedCount: number;
    outdatedCount: number;
  } | null;
  canManage: boolean;
  onClose: () => void;
  onInspect: () => void;
  onOpenMenu: () => void;
  onPrimary: () => void;
};

export function EntitySummaryPopover({
  open,
  anchorEl,
  entity,
  device,
  firmware,
  firmwareMeta,
  canManage,
  onClose,
  onInspect,
  onOpenMenu,
  onPrimary,
}: EntitySummaryPopoverProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLElement | null>(null);
  anchorRef.current = anchorEl;

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!entity) return null;

  const isDevice = entity.type === "device";
  const title = isDevice
    ? device?.name ?? "IoT"
    : firmwareMeta?.displayName || firmware?.displayName || firmwareMeta?.firmwareKey || "Firmware";

  return (
    <AnchoredPanelPortal
      open={open && Boolean(anchorEl)}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      className={`${POPOVER_SURFACE} pp-entity-summary`}
      density="compact"
      role="dialog"
      aria-label={isDevice ? `Resumo IoT: ${title}` : `Resumo firmware: ${title}`}
      preferredPlacement="right"
      allowFlip
      portalScopeClassName="dashboard-production-pulse"
      onDismiss={onClose}
    >
      {isDevice && device ? (
        <>
          <div className="pp-entity-summary__head">
            <div className="pp-entity-summary__identity">
              <Cpu size={18} aria-hidden="true" className="pp-entity-summary__glyph" />
              <div className="pp-entity-summary__titles">
                <strong className="pp-entity-summary__name">{device.name}</strong>
                <span className="pp-entity-summary__meta">IoT · {deviceStatusLabel(device)}</span>
              </div>
            </div>
            <PpHintAction hint={PP_HELP.hub.menuOpenDetails} ariaLabel="Ajuda: Menu de ações">
              <PpIconButton aria-label="Ações do IoT" onClick={onOpenMenu}>
                <MoreHorizontal size={16} aria-hidden="true" />
              </PpIconButton>
            </PpHintAction>
          </div>
          <div className="pp-entity-summary__body">
            <div className="pp-entity-summary__metric-strong">
              {typeof device.lastMetrics?.counter === "number"
                ? `${device.lastMetrics.counter} golpes`
                : "— golpes"}
            </div>
            <div className="pp-muted">
              +{device.periodDeltas?.day?.counter ?? 0} hoje · +
              {device.periodDeltas?.shift?.counter ?? 0} turno
            </div>
            <div className="pp-entity-summary__firmware-line">
              Firmware {device.installedFirmwareVersion ?? "—"}
              {firmwareMeta?.version ? ` → ${firmwareMeta.version}` : ""}
            </div>
          </div>
        </>
      ) : null}
      {!isDevice && (firmware || firmwareMeta) ? (
        <>
          <div className="pp-entity-summary__head">
            <div className="pp-entity-summary__identity">
              <FileCode size={18} aria-hidden="true" className="pp-entity-summary__glyph" />
              <div className="pp-entity-summary__titles">
                <strong className="pp-entity-summary__name">
                  {firmwareMeta?.displayName ||
                    firmware?.displayName ||
                    firmwareMeta?.firmwareKey ||
                    firmware?.firmwareKey ||
                    "Firmware"}
                </strong>
                <span className="pp-entity-summary__meta">
                  Firmware · v{firmwareMeta?.version || firmware?.version || "—"} ·{" "}
                  {firmwareLifecycleLabel(firmware)}
                </span>
              </div>
            </div>
            <PpHintAction hint={PP_HELP.hub.menuOpenDetails} ariaLabel="Ajuda: Menu de ações">
              <PpIconButton aria-label="Ações do firmware" onClick={onOpenMenu}>
                <MoreHorizontal size={16} aria-hidden="true" />
              </PpIconButton>
            </PpHintAction>
          </div>
          <div className="pp-entity-summary__body">
            <div>
              {firmwareMeta?.linkedCount ?? 0} IoT vinculado
              {(firmwareMeta?.linkedCount ?? 0) === 1 ? "" : "s"}
              {(firmwareMeta?.outdatedCount ?? 0) > 0
                ? ` · ⚠ ${firmwareMeta?.outdatedCount} desatual.`
                : ""}
            </div>
            {firmwareMeta?.firmwareKey || firmware?.firmwareKey ? (
              <div className="pp-muted pp-entity-summary__key">
                <code>{firmwareMeta?.firmwareKey || firmware?.firmwareKey}</code>
              </div>
            ) : null}
          </div>
        </>
      ) : null}
      <div className="pp-entity-summary__actions" role="group" aria-label="Ações rápidas">
        {canManage ? (
          <PpHintAction
            hint={isDevice ? PP_HELP.hub.menuOtaDeviceNow : PP_HELP.hub.menuOtaFamilyNow}
            ariaLabel={isDevice ? "Ajuda: Atualizar agora" : "Ajuda: Atualizar vinculados"}
          >
            <PpActionButton onClick={onPrimary}>
              <RefreshCw size={14} aria-hidden="true" />
              {isDevice ? "Atualizar" : "Atualizar vinculados"}
            </PpActionButton>
          </PpHintAction>
        ) : null}
        <PpHintAction hint={PP_HELP.hub.menuOpenDetails} ariaLabel="Ajuda: Ver detalhes">
          <PpActionButton variant="ghost" className="pp-entity-summary__details" onClick={onInspect}>
            Detalhes ›
          </PpActionButton>
        </PpHintAction>
      </div>
    </AnchoredPanelPortal>
  );
}

type EntityActionMenuProps = {
  open: boolean;
  anchorEl: HTMLElement | null;
  entity: AdminEntityRef | null;
  device?: DeviceListItem | null;
  firmware?: FirmwareListItem | null;
  canManage: boolean;
  onClose: () => void;
  onAction: (action: string) => void;
};

export function EntityActionMenu({
  open,
  anchorEl,
  entity,
  device,
  firmware,
  canManage,
  onClose,
  onAction,
}: EntityActionMenuProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLElement | null>(null);
  anchorRef.current = anchorEl;

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!entity || !canManage) return null;

  const run = (action: string) => {
    onAction(action);
    onClose();
  };

  return (
    <AnchoredPanelPortal
      open={open && Boolean(anchorEl)}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      className={`${POPOVER_SURFACE} pp-entity-menu`}
      density="compact"
      role="menu"
      aria-label="Menu de ações"
      preferredPlacement="bottom"
      allowFlip
      portalScopeClassName="dashboard-production-pulse"
      onDismiss={onClose}
    >
      {entity.type === "device" && device ? (
        <>
          <PpContextMenuItem
            label="Editar"
            icon={Pencil}
            hint={PP_HELP.hub.menuEditDevice}
            onSelect={() => run("edit")}
          />
          <PpContextMenuItem
            label="Renomear"
            icon={TextCursorInput}
            hint={PP_HELP.hub.menuRenameDevice}
            onSelect={() => run("rename")}
          />
          <ContextMenuDivider />
          <PpContextMenuItem
            label="Atualizar agora"
            icon={RefreshCw}
            hint={PP_HELP.hub.menuOtaDeviceNow}
            onSelect={() => run("ota-now")}
          />
          <PpContextMenuItem
            label="Agendar atualização…"
            icon={CalendarClock}
            hint={PP_HELP.hub.menuOtaDeviceSchedule}
            onSelect={() => run("ota-schedule")}
          />
          <ContextMenuDivider />
          <PpContextMenuItem
            label="Vincular firmware"
            icon={Link2}
            hint={PP_HELP.hub.startLinkFromDevice}
            onSelect={() => run("link")}
          />
          {explicitFirmwareKey(device) ? (
            <PpContextMenuItem
              label="Desvincular firmware"
              icon={Link2Off}
              hint={PP_HELP.hub.menuUnlinkFirmware}
              onSelect={() => run("unlink")}
            />
          ) : null}
          <ContextMenuDivider />
          {device.enabled ? (
            <PpContextMenuItem
              label="Desativar (soft delete)…"
              icon={PowerOff}
              hint={PP_HELP.hub.menuDisableDevice}
              destructive
              onSelect={() => run("disable")}
            />
          ) : (
            <PpContextMenuItem
              label="Reativar"
              icon={Power}
              hint={PP_HELP.hub.menuEnableDevice}
              onSelect={() => run("enable")}
            />
          )}
        </>
      ) : null}
      {entity.type === "firmware" && firmware ? (
        isPublishedFirmware(firmware) ? (
          <>
            <PpContextMenuItem
              label="Editar metadados"
              icon={FilePenLine}
              hint={PP_HELP.hub.menuEditFirmwareMeta}
              onSelect={() => run("edit")}
            />
            <PpContextMenuItem
              label="Criar nova versão"
              icon={FilePlus2}
              hint={PP_HELP.hub.menuNewFirmwareVersion}
              onSelect={() => run("new-version")}
            />
            <ContextMenuDivider />
            <PpContextMenuItem
              label="Vincular IoT"
              icon={Link2}
              hint={PP_HELP.hub.startLinkFromFirmware}
              onSelect={() => run("link")}
            />
            <PpContextMenuItem
              label="Atualizar vinculados agora"
              icon={RefreshCw}
              hint={PP_HELP.hub.menuOtaFamilyNow}
              onSelect={() => run("ota-now")}
            />
            <PpContextMenuItem
              label="Agendar atualização…"
              icon={CalendarClock}
              hint={PP_HELP.hub.menuOtaFamilySchedule}
              onSelect={() => run("ota-schedule")}
            />
            <ContextMenuDivider />
            <PpContextMenuItem
              label="Arquivar versão (soft delete)…"
              icon={Archive}
              hint={PP_HELP.hub.menuArchiveFirmware}
              destructive
              onSelect={() => run("archive")}
            />
          </>
        ) : (
          <>
            <PpContextMenuItem
              label="Editar"
              icon={Pencil}
              hint={PP_HELP.hub.menuEditFirmwareDraft}
              onSelect={() => run("edit")}
            />
            <PpContextMenuItem
              label="Anexar/alterar source"
              icon={FileCode}
              hint={PP_HELP.hub.menuAttachSource}
              onSelect={() => run("edit")}
            />
            <PpContextMenuItem
              label="Anexar binário"
              icon={Package}
              hint={PP_HELP.hub.menuAttachBinary}
              onSelect={() => run("edit")}
            />
            <PpContextMenuItem
              label="Publicar"
              icon={Upload}
              hint={PP_HELP.hub.menuPublishFirmware}
              onSelect={() => run("edit")}
            />
            <ContextMenuDivider />
            <PpContextMenuItem
              label="Vincular IoT"
              icon={Link2}
              hint={PP_HELP.hub.startLinkFromFirmware}
              onSelect={() => run("link")}
            />
          </>
        )
      ) : null}
    </AnchoredPanelPortal>
  );
}
