import { useMemo } from "react";

import {
  productionPulseDeviceDetailPath,
  productionPulseDeviceNewPath,
} from "../constants/routes";
import { navigateProductionPulse } from "../utils/navigation";

import { resolveBranchOptions } from "../constants/branches";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { PP_HELP } from "../content/helpTooltips";
import {
  PpActionButton,
  PpHintAction,
  PpPageHero,
  PpPagination,
  PpSegmentToggle,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { usePanelData } from "../hooks/usePanelData";
import { usePanelFilters } from "../hooks/usePanelFilters";
import { useViewportBucket } from "../hooks/useViewportBucket";
import { isMobileViewport } from "../utils/viewportLayout";
import { groupDevices, paginateDevices, totalPages } from "../utils/deviceGrouping";
import { DeviceCardList } from "../components/DeviceCard";
import { DeviceFiltersBar } from "../components/DeviceFiltersBar";
import { DeviceGroupedByWorkCenter } from "../components/DeviceGroupedByWorkCenter";
import { DeviceKpiStrip } from "../components/DeviceKpiStrip";
import { DeviceTable } from "../components/DeviceTable";

const PAGE_SIZE = 20;

type PanelPageProps = {
  search: string;
  permissions: ProductionPulsePermissionFlags;
  /** Hub side panel / modal — sem hero de página cheia; KPIs e filtros densos. */
  embedded?: boolean;
};

export function PanelPage({ search, permissions, embedded = false }: PanelPageProps) {
  const branchOptions = useMemo(
    () => resolveBranchOptions(permissions.allowedBranches),
    [permissions.allowedBranches],
  );
  const defaultBranch = branchOptions[0]?.id ?? "01";
  const { filters, setFilters } = usePanelFilters(search, defaultBranch);
  const viewport = useViewportBucket();
  const isMobile = isMobileViewport(viewport);

  const branchAllowed =
    permissions.isAdmin ||
    permissions.allowedBranches.length === 0 ||
    permissions.allowedBranches.includes(filters.branch);

  const {
    summary,
    filteredDevices,
    loading,
    error,
    pollNotice,
    pollingDeviceId,
    reload,
    runPoll,
    clearPollNotice,
  } = usePanelData(filters, permissions.canViewDevices && branchAllowed);

  const groups = useMemo(
    () => (filters.view === "grouped" ? groupDevices(filteredDevices, filters.groupBy) : []),
    [filteredDevices, filters.groupBy, filters.view],
  );

  const pagedDevices = useMemo(
    () => paginateDevices(filteredDevices, filters.page, PAGE_SIZE),
    [filteredDevices, filters.page],
  );

  const pageCount = totalPages(filteredDevices.length, PAGE_SIZE);

  const openDevice = (deviceId: string) => {
    navigateProductionPulse(productionPulseDeviceDetailPath(deviceId));
  };

  const openCreate = () => {
    navigateProductionPulse(productionPulseDeviceNewPath(filters.branch));
  };

  if (!permissions.canViewDevices) {
    return (
      <div className={`pp-page-stack${embedded ? " pp-panel-page--embedded" : ""}`}>
        {!embedded ? <PpPageHero title="Pulso de Produção" badge={ppShellIcon} /> : null}
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  if (!branchAllowed) {
    return (
      <div className={`pp-page-stack${embedded ? " pp-panel-page--embedded" : ""}`}>
        {!embedded ? <PpPageHero title="Pulso de Produção" badge={ppShellIcon} /> : null}
        <PpStateBox
          variant="error"
          title="Sem permissão para esta filial"
          message="Escolha outra filial ou solicite acesso ao administrador."
        />
      </div>
    );
  }

  const showEmptyFilial = !loading && !error && filteredDevices.length === 0 && !filters.search && !filters.status && !filters.anchorType && !filters.role;
  const showEmptyFilters = !loading && !error && filteredDevices.length === 0 && !showEmptyFilial;
  const effectiveView =
    embedded && filters.view === "cards" ? "table" : filters.view;

  return (
    <div className={`pp-page-stack pp-panel-page${embedded ? " pp-panel-page--embedded" : ""}`}>
      {!embedded ? (
        <PpPageHero
          title="Pulso de Produção"
          description={PP_HELP.shell.heroTitle}
          badge={ppShellIcon}
          actions={
            <div className="pp-panel-hero-actions">
              {branchOptions.length > 1 ? (
                <PpHintAction hint={PP_HELP.shell.heroFilial} ariaLabel="Ajuda: Filial">
                  <PpSegmentToggle
                    ariaLabel="Filial"
                    size="sm"
                    widthMode="content"
                    value={filters.branch}
                    onChange={(branch) => setFilters({ branch, page: 1 })}
                    options={branchOptions.map((item) => ({ value: item.id, label: item.label }))}
                  />
                </PpHintAction>
              ) : null}
            </div>
          }
        />
      ) : branchOptions.length > 1 ? (
        <div className="pp-panel-embedded-toolbar">
          <PpHintAction hint={PP_HELP.shell.heroFilial} ariaLabel="Ajuda: Filial">
            <PpSegmentToggle
              ariaLabel="Filial"
              size="sm"
              widthMode="content"
              value={filters.branch}
              onChange={(branch) => setFilters({ branch, page: 1 })}
              options={branchOptions.map((item) => ({ value: item.id, label: item.label }))}
            />
          </PpHintAction>
        </div>
      ) : null}

      <DeviceKpiStrip summary={summary} loading={loading} compact={embedded} />

      <DeviceFiltersBar
        filters={filters}
        canManage={permissions.canManageDevices}
        onChange={setFilters}
        onCreateDevice={openCreate}
        compact={embedded}
      />

      {pollNotice ? (
        <div className="pp-poll-notice" role="status">
          <strong>{PP_HELP.panel.pollNoticeTitle}</strong>
          <span>{pollNotice}</span>
          <PpActionButton variant="ghost" onClick={clearPollNotice}>
            {PP_HELP.panel.pollNoticeClose}
          </PpActionButton>
        </div>
      ) : null}

      {error ? (
        <PpStateBox
          variant="error"
          title="Erro ao carregar"
          message={error}
          action={
            <PpActionButton variant="ghost" onClick={() => void reload()}>
              {PP_HELP.panel.retryLoad}
            </PpActionButton>
          }
        />
      ) : null}

      {showEmptyFilial ? (
        <PpStateBox
          variant="empty"
          title="Nenhum dispositivo cadastrado"
          message={PP_HELP.panel.emptyFilial}
          action={
            permissions.canManageDevices ? (
              <PpActionButton variant="primary" onClick={openCreate}>
                Cadastrar dispositivo
              </PpActionButton>
            ) : undefined
          }
        />
      ) : null}

      {showEmptyFilters ? (
        <PpStateBox
          variant="empty"
          title="Nenhum dispositivo com esses filtros"
          message={PP_HELP.panel.emptyFilters}
          action={
            <PpActionButton
              variant="ghost"
              onClick={() =>
                setFilters({
                  anchorType: "",
                  role: "",
                  status: "",
                  search: "",
                  page: 1,
                })
              }
            >
              {PP_HELP.panel.clearFilters}
            </PpActionButton>
          }
        />
      ) : null}

      {!showEmptyFilial && !showEmptyFilters ? (
        effectiveView === "grouped" ? (
          <DeviceGroupedByWorkCenter
            groups={groups}
            mobile={isMobile || embedded}
            pollingDeviceId={pollingDeviceId}
            onPoll={runPoll}
            onOpenDevice={openDevice}
          />
        ) : effectiveView === "cards" ? (
          <DeviceCardList
            devices={pagedDevices}
            loading={loading}
            pollingDeviceId={pollingDeviceId}
            onOpenDevice={openDevice}
            onPoll={runPoll}
          />
        ) : (
          <DeviceTable
            devices={pagedDevices}
            loading={loading}
            pollingDeviceId={pollingDeviceId}
            onPoll={runPoll}
            onOpenDevice={openDevice}
          />
        )
      ) : null}

      {!showEmptyFilial && !showEmptyFilters && effectiveView !== "grouped" ? (
        <PpPagination
          page={filters.page}
          pageSize={PAGE_SIZE}
          total={filteredDevices.length}
          totalPages={pageCount}
          onPageChange={(page) => setFilters({ page })}
          hideWhenSinglePage
        />
      ) : null}
    </div>
  );
}
