import { useMemo, useState } from "react";

import {
  PpActionButton,
  PpPageHero,
  PpStateBox,
  PpUnderlineNav,
  ppShellIcon,
} from "../app/productionPulseUi";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import { DeviceCommandsTab } from "../components/detail/DeviceCommandsTab";
import { DeviceHistoryTab } from "../components/detail/DeviceHistoryTab";
import { DeviceOverviewTab } from "../components/detail/DeviceOverviewTab";
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

type DeviceDetailPageProps = {
  deviceId: string;
  tab: Extract<ProductionPulseRoute, { kind: "deviceDetail" }>["tab"];
  search: string;
  permissions: ProductionPulsePermissionFlags;
};

export function DeviceDetailPage({
  deviceId,
  tab,
  search,
  permissions,
}: DeviceDetailPageProps) {
  const [resetOpen, setResetOpen] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);

  const {
    device,
    loading,
    error,
    actionError,
    liveSnapshot,
    refreshing,
    commandsRefreshToken,
    historyRefreshToken,
    refreshLive,
    pollNow,
    resetCounter,
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
          : PP_HELP.detail.tabCommands,
  }));

  const setTab = (nextTab: typeof tab) => {
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

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} />
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
        <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} />
        <PpStateBox variant="loading" title="Carregando dispositivo…" message="Aguarde um instante." />
      </div>
    );
  }

  if (error && !device) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} />
        <PpStateBox variant="error" title="Erro ao carregar" message={error} />
      </div>
    );
  }

  if (!device) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Detalhe do dispositivo" badge={ppShellIcon} />
        <PpStateBox variant="empty" title="Dispositivo não encontrado" message="Verifique o link ou volte ao painel." />
      </div>
    );
  }

  return (
    <div className="pp-page-stack pp-device-detail">
      <ProductionPulsePagePath panelHref={panelBackPath} current={device.name} />
      <PpPageHero
        title={device.name}
        description={formatDeviceDetailDescription(device)}
        badge={ppShellIcon}
        actions={
          <div className="pp-device-detail__hero-actions">
            <DeviceStatusBadge status={device.status} />
            {permissions.canManageDevices ? (
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(productionPulseDeviceEditPath(deviceId))}
              >
                Editar
              </PpActionButton>
            ) : null}
            <PpActionButton variant="ghost" onClick={() => void pollNow()} disabled={refreshing}>
              {refreshing ? PP_HELP.detail.pollNowLoading : PP_HELP.detail.pollNowAction}
            </PpActionButton>
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

      {actionError ? <p className="pp-detail-banner-error">{actionError}</p> : null}

      {tab === "overview" ? (
        <DeviceOverviewTab
          device={device}
          liveSnapshot={liveSnapshot}
          refreshing={refreshing}
          canCommand={permissions.canCommandDevices}
          onRefreshLive={() => void refreshLive()}
          onPollNow={() => void pollNow()}
          onReset={() => setResetOpen(true)}
        />
      ) : null}

      {tab === "history" ? (
        <DeviceHistoryTab device={device} refreshToken={historyRefreshToken} />
      ) : null}

      {tab === "commands" ? (
        <DeviceCommandsTab deviceId={deviceId} refreshToken={commandsRefreshToken} />
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
    </div>
  );
}
