import {
  Archive,
  CalendarClock,
  FileCode,
  FilePenLine,
  FilePlus2,
  Link2Off,
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
  ContextMenuItem,
  PpActionButton,
  PpHintAction,
} from "../app/productionPulseUi";
import type { FirmwareListItem } from "../api/productionPulseApi";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import type { AdminEntityRef } from "../utils/adminHubUiState";
import { isPublishedFirmware } from "../utils/hubOtaKpis";

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

  return (
    <AnchoredPanelPortal
      open={open && Boolean(anchorEl)}
      anchorRef={anchorRef}
      panelRef={panelRef}
      preferredPlacement="right"
      allowFlip
      portalScopeClassName="dashboard-production-pulse"
      onDismiss={onClose}
    >
      <div ref={panelRef} className="pp-entity-summary" role="dialog" aria-label="Resumo">
        {isDevice && device ? (
          <>
            <div className="pp-entity-summary__head">
              <strong>{device.name}</strong>
              <PpActionButton variant="ghost" aria-haspopup="menu" onClick={onOpenMenu}>
                ⋯
              </PpActionButton>
            </div>
            <div className="pp-muted">
              {device.status === "online"
                ? "● Online"
                : device.status === "offline"
                  ? "● Offline"
                  : device.enabled
                    ? "● —"
                    : "● Inativo"}
            </div>
            <div className="pp-entity-summary__body">
              <div>
                Golpes:{" "}
                {typeof device.lastMetrics?.counter === "number"
                  ? device.lastMetrics.counter
                  : "—"}
              </div>
              <div>
                Hoje: +{device.periodDeltas?.day?.counter ?? 0} · Turno: +
                {device.periodDeltas?.shift?.counter ?? 0}
              </div>
              <div>Firmware: {device.installedFirmwareVersion ?? "—"}</div>
              <div>Disponível: {firmwareMeta?.version ?? "—"}</div>
            </div>
          </>
        ) : null}
        {!isDevice && (firmware || firmwareMeta) ? (
          <>
            <div className="pp-entity-summary__head">
              <strong>{firmwareMeta?.displayName || firmware?.displayName || "Firmware"}</strong>
              <PpActionButton variant="ghost" aria-haspopup="menu" onClick={onOpenMenu}>
                ⋯
              </PpActionButton>
            </div>
            <div className="pp-muted">{firmwareMeta?.firmwareKey || firmware?.firmwareKey}</div>
            <div className="pp-entity-summary__body">
              <div>Versão: {firmwareMeta?.version || firmware?.version || "—"}</div>
              <div>Vinculados: {firmwareMeta?.linkedCount ?? 0}</div>
              <div>Desatualizados: {firmwareMeta?.outdatedCount ?? 0}</div>
              {firmware ? (
                <div>
                  Estado:{" "}
                  {isPublishedFirmware(firmware)
                    ? "Publicado"
                    : firmware.lifecycle === "draft"
                      ? "Rascunho"
                      : "Arquivado"}
                </div>
              ) : null}
            </div>
          </>
        ) : null}
        <div className="pp-entity-summary__actions">
          {canManage ? (
            <PpHintAction
              hint={isDevice ? PP_HELP.hub.menuOtaDeviceNow : PP_HELP.hub.menuOtaFamilyNow}
              ariaLabel={isDevice ? "Ajuda: Atualizar agora" : "Ajuda: Atualizar vinculados"}
            >
              <PpActionButton onClick={onPrimary}>
                {isDevice ? "Atualizar agora" : "Atualizar vinculados"}
              </PpActionButton>
            </PpHintAction>
          ) : null}
          <PpHintAction hint={PP_HELP.hub.menuOpenDetails} ariaLabel="Ajuda: Ver detalhes">
            <PpActionButton variant="ghost" onClick={onInspect}>
              Ver detalhes
            </PpActionButton>
          </PpHintAction>
        </div>
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
    // Ação primeiro: openConfirm/openModal definem openLayer.
    // onClose só limpa se ainda estivermos no menu (não clobber confirm/modal).
    onAction(action);
    onClose();
  };

  return (
    <AnchoredPanelPortal
      open={open && Boolean(anchorEl)}
      anchorRef={anchorRef}
      panelRef={panelRef}
      preferredPlacement="bottom"
      allowFlip
      portalScopeClassName="dashboard-production-pulse"
      onDismiss={onClose}
    >
      <div ref={panelRef} className="pp-entity-menu" role="menu">
        {entity.type === "device" && device ? (
          <>
            <ContextMenuItem
              label="Editar"
              icon={Pencil}
              hint={PP_HELP.hub.menuEditDevice}
              onSelect={() => run("edit")}
            />
            <ContextMenuItem
              label="Renomear"
              icon={TextCursorInput}
              hint={PP_HELP.hub.menuRenameDevice}
              onSelect={() => run("rename")}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label="Atualizar agora"
              icon={RefreshCw}
              hint={PP_HELP.hub.menuOtaDeviceNow}
              onSelect={() => run("ota-now")}
            />
            <ContextMenuItem
              label="Agendar atualização…"
              icon={CalendarClock}
              hint={PP_HELP.hub.menuOtaDeviceSchedule}
              onSelect={() => run("ota-schedule")}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label="Desvincular firmware"
              icon={Link2Off}
              hint={PP_HELP.hub.menuUnlinkFirmware}
              onSelect={() => run("unlink")}
            />
            <ContextMenuDivider />
            {device.enabled ? (
              <ContextMenuItem
                label="Desativar (soft delete)…"
                icon={PowerOff}
                hint={PP_HELP.hub.menuDisableDevice}
                destructive
                onSelect={() => run("disable")}
              />
            ) : (
              <ContextMenuItem
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
              <ContextMenuItem
                label="Editar metadados"
                icon={FilePenLine}
                hint={PP_HELP.hub.menuEditFirmwareMeta}
                onSelect={() => run("edit")}
              />
              <ContextMenuItem
                label="Criar nova versão"
                icon={FilePlus2}
                hint={PP_HELP.hub.menuNewFirmwareVersion}
                onSelect={() => run("new-version")}
              />
              <ContextMenuDivider />
              <ContextMenuItem
                label="Atualizar vinculados agora"
                icon={RefreshCw}
                hint={PP_HELP.hub.menuOtaFamilyNow}
                onSelect={() => run("ota-now")}
              />
              <ContextMenuItem
                label="Agendar atualização…"
                icon={CalendarClock}
                hint={PP_HELP.hub.menuOtaFamilySchedule}
                onSelect={() => run("ota-schedule")}
              />
              <ContextMenuDivider />
              <ContextMenuItem
                label="Arquivar versão (soft delete)…"
                icon={Archive}
                hint={PP_HELP.hub.menuArchiveFirmware}
                destructive
                onSelect={() => run("archive")}
              />
            </>
          ) : (
            <>
              <ContextMenuItem
                label="Editar"
                icon={Pencil}
                hint={PP_HELP.hub.menuEditFirmwareDraft}
                onSelect={() => run("edit")}
              />
              <ContextMenuItem
                label="Anexar/alterar source"
                icon={FileCode}
                hint={PP_HELP.hub.menuAttachSource}
                onSelect={() => run("edit")}
              />
              <ContextMenuItem
                label="Anexar binário"
                icon={Package}
                hint={PP_HELP.hub.menuAttachBinary}
                onSelect={() => run("edit")}
              />
              <ContextMenuItem
                label="Publicar"
                icon={Upload}
                hint={PP_HELP.hub.menuPublishFirmware}
                onSelect={() => run("edit")}
              />
            </>
          )
        ) : null}
      </div>
    </AnchoredPanelPortal>
  );
}
