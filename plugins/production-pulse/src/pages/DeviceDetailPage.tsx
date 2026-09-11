import { useMemo, useState } from "react";

import type { DeletionImpact, FirmwareUpdateTarget } from "../api/productionPulseApi";
import {
  deleteDevicePermanently,
  disableDevice,
  fetchDeviceDeletionImpact,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpHintAction,
  PpHostContainedDialog,
  PpPageHero,
  PpStateBox,
  PpUnderlineNav,
  ppShellIcon,
} from "../app/productionPulseUi";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import { PermanentDeleteDialog } from "../components/PermanentDeleteDialog";
import { DeviceCommandsTab } from "../components/detail/DeviceCommandsTab";
import { DeviceFirmwareTab } from "../components/detail/DeviceFirmwareTab";
import { DeviceHardwareTab } from "../components/detail/DeviceHardwareTab";
import { DeviceHistoryTab } from "../components/detail/DeviceHistoryTab";
import { DeviceOverviewTab } from "../components/detail/DeviceOverviewTab";
import { DetailStatusBanner } from "../components/detail/DetailStatusBanner";
import { FactoryResetModal } from "../components/modals/FactoryResetModal";
import { ResetCounterModal } from "../components/modals/ResetCounterModal";
import {
  productionPulseDeviceDetailPath,
  productionPulseDeviceEditPath,
  type ProductionPulseRoute,
} from "../constants/routes";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { PP_HELP } from "../content/helpTooltips";
import { DEVICE_DETAIL_NAV, useDeviceDetail } from "../hooks/useDeviceDetail";
import { buildPanelPath, readPanelFilters } from "../utils/panelFilterUrl";
import { navigateProductionPulse, replaceProductionPulse } from "../utils/navigation";
import { formatDeviceDetailDescription } from "../utils/deviceDisplay";
import { DeviceStatusBadge } from "../components/DeviceStatusBadge";

type DeviceDetailTab = Extract<ProductionPulseRoute, { kind: "deviceDetail" }>["tab"];

type DeviceDetailPageProps = {
  deviceId: string;
  tab: DeviceDetailTab;
  search: string;
  permissions: ProductionPulsePermissionFlags;
  /** When true, omit page chrome and keep tab switches local (no route navigate). */
  embedded?: boolean;
  onClose?: () => void;
  hubOtaTarget?: FirmwareUpdateTarget | null;
  suppressLocalOtaPoll?: boolean;
  onOperationalNotice?: (notice: {
    id?: string;
    variant?: "error" | "warning" | "info" | "success";
    title?: string;
    message: string;
  }) => void;
  /** Hub coordinates PermanentDeleteDialog; when omitted, detail owns the flow. */
  onRequestPermanentDelete?: (deviceId: string, label: string) => void;
};

export function DeviceDetailPage({
  deviceId,
  tab: tabProp,
  search,
  permissions,
  embedded = false,
  onClose,
  hubOtaTarget,
  suppressLocalOtaPoll,
  onOperationalNotice,
  onRequestPermanentDelete,
}: DeviceDetailPageProps) {
  const [localTab, setLocalTab] = useState<DeviceDetailTab>(tabProp);
  const tab = embedded ? localTab : tabProp;

  const [resetOpen, setResetOpen] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [factoryOpen, setFactoryOpen] = useState(false);
  const [factoryLoading, setFactoryLoading] = useState(false);
  const [factoryError, setFactoryError] = useState<string | null>(null);
  const [deactivateOpen, setDeactivateOpen] = useState(false);
  const [deactivateLoading, setDeactivateLoading] = useState(false);
  const [deactivateError, setDeactivateError] = useState<string | null>(null);
  const [permanentOpen, setPermanentOpen] = useState(false);
  const [permanentImpact, setPermanentImpact] = useState<DeletionImpact | null>(null);
  const [permanentLoading, setPermanentLoading] = useState(false);
  const [permanentBusy, setPermanentBusy] = useState(false);
  const [permanentError, setPermanentError] = useState<string | null>(null);

  const {
    device,
    loading,
    error,
    actionError,
    liveConnectivityIssue,
    liveSnapshot,
    refreshing,
    commandsRefreshToken,
    historyRefreshToken,
    refreshLive,
    pollNow,
    resetCounter,
    factoryReset,
    reloadDevice,
  } = useDeviceDetail({
    deviceId,
    enabled: permissions.canViewDevices,
  });

  const panelBackPath = useMemo(() => {
    const currentFilters = readPanelFilters(search);
    return buildPanelPath({
      ...currentFilters,
      branch: device?.branch ?? currentFilters.branch,
      page: 1,
    });
  }, [device?.branch, search]);

  const navItems = DEVICE_DETAIL_NAV.map((item) => ({
    id: item.id,
    label: item.label,
    hint:
      item.id === "overview"
        ? PP_HELP.detail.tabOverview
        : item.id === "history"
          ? PP_HELP.detail.tabHistory
          : item.id === "commands"
            ? PP_HELP.detail.tabCommands
            : item.id === "firmware"
              ? PP_HELP.detail.tabFirmware
              : PP_HELP.detail.tabHardware,
  }));

  const setTab = (nextTab: DeviceDetailTab) => {
    if (embedded) {
      setLocalTab(nextTab);
      return;
    }
    replaceProductionPulse(productionPulseDeviceDetailPath(deviceId, nextTab));
  };

  const handleReset = async () => {
    setResetLoading(true);
    setResetError(null);
    try {
      await resetCounter();
      setResetOpen(false);
    } catch (err) {
      setResetError(err instanceof Error ? err.message : "Erro ao zerar contador.");
    } finally {
      setResetLoading(false);
    }
  };

  const handleFactoryReset = async () => {
    setFactoryLoading(true);
    setFactoryError(null);
    try {
      await factoryReset();
      setFactoryOpen(false);
    } catch (err) {
      setFactoryError(err instanceof Error ? err.message : "Erro ao restaurar fábrica.");
    } finally {
      setFactoryLoading(false);
    }
  };

  const handleDeactivate = async () => {
    setDeactivateLoading(true);
    setDeactivateError(null);
    try {
      await disableDevice(deviceId);
      setDeactivateOpen(false);
      if (onClose) {
        onClose();
        return;
      }
      navigateProductionPulse(panelBackPath);
    } catch (err) {
      setDeactivateError(err instanceof Error ? err.message : "Erro ao desativar dispositivo.");
    } finally {
      setDeactivateLoading(false);
    }
  };

  const openLocalPermanentDelete = async () => {
    if (!device) return;
    if (onRequestPermanentDelete) {
      onRequestPermanentDelete(deviceId, device.name);
      return;
    }
    setPermanentOpen(true);
    setPermanentImpact(null);
    setPermanentError(null);
    setPermanentLoading(true);
    try {
      const impact = await fetchDeviceDeletionImpact(deviceId);
      setPermanentImpact(impact);
    } catch (err) {
      setPermanentOpen(false);
      setPermanentError(err instanceof Error ? err.message : "Falha ao analisar dependências.");
    } finally {
      setPermanentLoading(false);
    }
  };

  const handlePermanentDelete = async () => {
    if (!device) return;
    setPermanentBusy(true);
    setPermanentError(null);
    try {
      await deleteDevicePermanently(deviceId);
      setPermanentOpen(false);
      if (onClose) {
        onClose();
        return;
      }
      navigateProductionPulse(panelBackPath);
    } catch (err) {
      setPermanentError(err instanceof Error ? err.message : "Falha ao excluir permanentemente.");
    } finally {
      setPermanentBusy(false);
    }
  };

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        {!embedded ? <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} /> : null}
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  if (loading && !device) {
    return (
      <div className="pp-page-stack">
        {!embedded ? <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} /> : null}
        <PpStateBox variant="loading" title="Carregando dispositivo…" message="Aguarde um instante." />
      </div>
    );
  }

  if (error && !device) {
    return (
      <div className="pp-page-stack">
        {!embedded ? <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} /> : null}
        <PpStateBox variant="error" title="Erro ao carregar" message={error} />
      </div>
    );
  }

  if (!device) {
    return (
      <div className="pp-page-stack">
        {!embedded ? <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} /> : null}
        <PpStateBox variant="empty" title="Dispositivo não encontrado" message="Verifique o link ou volte ao painel." />
      </div>
    );
  }

  return (
    <div className={`pp-page-stack pp-device-detail${embedded ? " pp-form-page--embedded" : ""}`}>
      {!embedded ? (
        <ProductionPulsePagePath panelHref={panelBackPath} current={device.name} />
      ) : null}
      <PpPageHero
        title={device.name}
        description={formatDeviceDetailDescription(device)}
        badge={embedded ? undefined : ppShellIcon}
        actions={
          <div className="pp-detail-hero-actions">
            <DeviceStatusBadge status={device.status} />
            {permissions.canManageDevices ? (
              <>
                <PpHintAction hint={PP_HELP.detail.editDevice} ariaLabel="Ajuda: Editar">
                  <PpActionButton
                    variant="ghost"
                    className="pp-hero-brand-btn"
                    onClick={() => navigateProductionPulse(productionPulseDeviceEditPath(deviceId))}
                  >
                    Editar
                  </PpActionButton>
                </PpHintAction>
                {device.enabled ? (
                  <PpHintAction hint={PP_HELP.detail.deactivate} ariaLabel="Ajuda: Desativar">
                    <PpActionButton
                      variant="ghost"
                      className="pp-hero-brand-btn"
                      onClick={() => setDeactivateOpen(true)}
                    >
                      Desativar
                    </PpActionButton>
                  </PpHintAction>
                ) : null}
                <PpHintAction
                  hint={PP_HELP.hub.menuPermanentDeleteDevice}
                  ariaLabel="Ajuda: Excluir permanentemente"
                >
                  <PpActionButton
                    variant="ghost"
                    className="pp-hero-brand-btn"
                    onClick={() => void openLocalPermanentDelete()}
                  >
                    Excluir permanentemente…
                  </PpActionButton>
                </PpHintAction>
              </>
            ) : null}
            <PpHintAction hint={PP_HELP.detail.pollNow} ariaLabel="Ajuda: Atualizar agora">
              <PpActionButton
                variant="ghost"
                className="pp-hero-brand-btn"
                onClick={() => void pollNow()}
                disabled={refreshing}
              >
                {refreshing ? PP_HELP.detail.pollNowLoading : PP_HELP.detail.pollNowAction}
              </PpActionButton>
            </PpHintAction>
            {embedded && onClose ? (
              <PpActionButton variant="ghost" className="pp-hero-brand-btn" onClick={onClose}>
                Fechar
              </PpActionButton>
            ) : null}
          </div>
        }
      />

      <PpUnderlineNav
        items={navItems.map((item) => ({
          ...item,
          title: item.hint,
          onSelect: () => setTab(item.id),
        }))}
        activeId={tab}
        aria-label="Abas do dispositivo"
      />

      {actionError ? (
        <DetailStatusBanner
          variant="warning"
          title={PP_HELP.detail.actionFailedTitle}
          message={actionError}
        />
      ) : null}

      {permanentError && !permanentOpen ? (
        <DetailStatusBanner variant="warning" title="Exclusão permanente" message={permanentError} />
      ) : null}

      {tab === "overview" ? (
        <DeviceOverviewTab
          device={device}
          liveSnapshot={liveSnapshot}
          liveConnectivityIssue={liveConnectivityIssue}
          refreshing={refreshing}
          canCommand={permissions.canCommandDevices}
          onRefreshLive={() => void refreshLive()}
          onPollNow={() => void pollNow()}
          onReset={() => setResetOpen(true)}
          onFactoryReset={() => setFactoryOpen(true)}
        />
      ) : null}

      {tab === "history" ? (
        <DeviceHistoryTab device={device} refreshToken={historyRefreshToken} />
      ) : null}

      {tab === "commands" ? (
        <DeviceCommandsTab deviceId={deviceId} refreshToken={commandsRefreshToken} />
      ) : null}

      {tab === "firmware" ? (
        <DeviceFirmwareTab
          device={device}
          liveSnapshot={liveSnapshot}
          canManage={permissions.canManageDevices}
          onUpdated={() => void reloadDevice()}
          hubOtaTarget={hubOtaTarget}
          suppressLocalPoll={suppressLocalOtaPoll}
          onOperationalNotice={onOperationalNotice}
        />
      ) : null}

      {tab === "hardware" ? (
        <DeviceHardwareTab deviceId={deviceId} canManage={permissions.canManageDevices} />
      ) : null}

      <ResetCounterModal
        open={resetOpen}
        loading={resetLoading}
        error={resetError}
        onConfirm={() => void handleReset()}
        onClose={() => {
          if (resetLoading) return;
          setResetOpen(false);
          setResetError(null);
        }}
      />

      <FactoryResetModal
        open={factoryOpen}
        loading={factoryLoading}
        error={factoryError}
        onConfirm={() => void handleFactoryReset()}
        onClose={() => {
          if (factoryLoading) return;
          setFactoryOpen(false);
          setFactoryError(null);
        }}
      />

      <PpHostContainedDialog
        open={deactivateOpen}
        title={PP_HELP.modals.deactivateTitle}
        onClose={() => {
          if (deactivateLoading) return;
          setDeactivateOpen(false);
          setDeactivateError(null);
        }}
      >
        <p>{PP_HELP.modals.deactivateBody}</p>
        {deactivateError ? <PpStateBox variant="error" title="Desativação" message={deactivateError} /> : null}
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={() => setDeactivateOpen(false)} disabled={deactivateLoading}>
            Cancelar
          </PpActionButton>
          <PpActionButton onClick={() => void handleDeactivate()} disabled={deactivateLoading}>
            {deactivateLoading ? "Desativando…" : "Desativar dispositivo"}
          </PpActionButton>
        </div>
      </PpHostContainedDialog>

      <PermanentDeleteDialog
        open={permanentOpen}
        title={PP_HELP.hub.permanentDeleteDeviceTitle}
        entityLabel={device.name}
        confirmPhrase={device.name}
        impact={permanentImpact}
        loadingImpact={permanentLoading}
        confirmBusy={permanentBusy}
        onConfirm={() => void handlePermanentDelete()}
        onCancel={() => {
          if (permanentBusy) return;
          setPermanentOpen(false);
          setPermanentImpact(null);
          setPermanentError(null);
        }}
      />
    </div>
  );
}
