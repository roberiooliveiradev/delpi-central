import { useEffect, useRef } from "react";

import {
  AnchoredPanelPortal,
  ContextMenuDivider,
  ContextMenuItem,
  PpActionButton,
} from "../app/productionPulseUi";
import type { FirmwareListItem } from "../api/productionPulseApi";
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
            <PpActionButton onClick={onPrimary}>
              {isDevice ? "Atualizar agora" : "Atualizar vinculados"}
            </PpActionButton>
          ) : null}
          <PpActionButton variant="ghost" onClick={onInspect}>
            Ver detalhes
          </PpActionButton>
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
            <ContextMenuItem label="Editar" onSelect={() => run("edit")} />
            <ContextMenuItem label="Renomear" onSelect={() => run("rename")} />
            <ContextMenuDivider />
            <ContextMenuItem label="Atualizar agora" onSelect={() => run("ota-now")} />
            <ContextMenuItem label="Agendar atualização…" onSelect={() => run("ota-schedule")} />
            <ContextMenuDivider />
            <ContextMenuItem label="Desvincular firmware" onSelect={() => run("unlink")} />
            <ContextMenuDivider />
            {device.enabled ? (
              <ContextMenuItem
                label="Desativar (soft delete)…"
                destructive
                onSelect={() => run("disable")}
              />
            ) : (
              <ContextMenuItem label="Reativar" onSelect={() => run("enable")} />
            )}
          </>
        ) : null}
        {entity.type === "firmware" && firmware ? (
          isPublishedFirmware(firmware) ? (
            <>
              <ContextMenuItem label="Editar metadados" onSelect={() => run("edit")} />
              <ContextMenuItem label="Criar nova versão" onSelect={() => run("new-version")} />
              <ContextMenuDivider />
              <ContextMenuItem
                label="Atualizar vinculados agora"
                onSelect={() => run("ota-now")}
              />
              <ContextMenuItem
                label="Agendar atualização…"
                onSelect={() => run("ota-schedule")}
              />
              <ContextMenuDivider />
              <ContextMenuItem
                label="Arquivar versão (soft delete)…"
                destructive
                onSelect={() => run("archive")}
              />
            </>
          ) : (
            <>
              <ContextMenuItem label="Editar" onSelect={() => run("edit")} />
              <ContextMenuItem label="Anexar/alterar source" onSelect={() => run("edit")} />
              <ContextMenuItem label="Anexar binário" onSelect={() => run("edit")} />
              <ContextMenuItem label="Publicar" onSelect={() => run("edit")} />
            </>
          )
        ) : null}
      </div>
    </AnchoredPanelPortal>
  );
}
