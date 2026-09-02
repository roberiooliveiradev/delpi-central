import { useMemo } from "react";

import { productionPulseDeviceNewPath } from "../constants/routes";
import { navigateProductionPulse } from "../utils/navigation";

import { resolveBranchOptions } from "../constants/branches";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { PP_HELP } from "../content/helpTooltips";
import { PpActionButton, PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";
import { usePanelData } from "../hooks/usePanelData";
import { usePanelFilters } from "../hooks/usePanelFilters";
import { useViewportBucket } from "../hooks/useViewportBucket";
import { groupDevices, paginateDevices, totalPages } from "../utils/deviceGrouping";
import { DeviceCardList } from "../components/DeviceCard";
import { DeviceFiltersBar } from "../components/DeviceFiltersBar";
import { DeviceGroupedByWorkCenter } from "../components/DeviceGroupedByWorkCenter";
import { DeviceKpiStrip } from "../components/DeviceKpiStrip";
import { DeviceTable } from "../components/DeviceTable";
import { FilialSwitcher } from "../components/FilialSwitcher";

const PAGE_SIZE = 20;

type PanelPageProps = {
  search: string;
  permissions: ProductionPulsePermissionFlags;
};

export function PanelPage({ search, permissions }: PanelPageProps) {
  const branchOptions = useMemo(
    () => resolveBranchOptions(permissions.allowedBranches),
    [permissions.allowedBranches],
  );
  const defaultBranch = branchOptions[0]?.id ?? "01";
  const { filters, setFilters } = usePanelFilters(search, defaultBranch);
  const viewport = useViewportBucket();
  const isMobile = viewport === "mobile";

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
    navigateProductionPulse(`/apps/production-pulse/devices/${deviceId}`);
  };

  const openCreate = () => {
    navigateProductionPulse(productionPulseDeviceNewPath(filters.branch));
  };

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Pulso de Produção" badge={ppShellIcon} />
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
      <div className="pp-page-stack">
        <PpPageHero title="Pulso de Produção" badge={ppShellIcon} />
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

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Pulso de Produção"
        description={PP_HELP.shell.heroTitle}
        badge={ppShellIcon}
        actions={
          branchOptions.length > 1 ? (
            <FilialSwitcher
              compact
              filiais={branchOptions}
              value={filters.branch}
              onChange={(branch) => setFilters({ branch, page: 1 })}
            />
          ) : null
        }
      />

      <DeviceKpiStrip summary={summary} loading={loading} />

      <DeviceFiltersBar
        filters={filters}
        canManage={permissions.canManageDevices}
        onChange={setFilters}
        onCreateDevice={openCreate}
      />

      {pollNotice ? (
        <div className="pp-poll-notice" role="status">
          <strong>{PP_HELP.panel.pollNoticeTitle}</strong>
          <span>{pollNotice}</span>
          <PpActionButton variant="ghost" onClick={clearPollNotice}>
            Fechar
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
              Tentar novamente
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
              Limpar filtros
            </PpActionButton>
          }
        />
      ) : null}

      {!showEmptyFilial && !showEmptyFilters ? (
        filters.view === "grouped" ? (
          <DeviceGroupedByWorkCenter
            groups={groups}
            mobile={isMobile}
            pollingDeviceId={pollingDeviceId}
            onPoll={runPoll}
            onOpenDevice={openDevice}
          />
        ) : isMobile ? (
          <DeviceCardList
            devices={pagedDevices}
            pollingDeviceId={pollingDeviceId}
            onPoll={runPoll}
            onOpenDevice={openDevice}
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

      {!showEmptyFilial && !showEmptyFilters && filters.view === "list" && pageCount > 1 ? (
        <div className="pp-compact-pagination">
          <PpActionButton
            variant="ghost"
            disabled={filters.page <= 1}
            onClick={() => setFilters({ page: filters.page - 1 })}
          >
            Anterior
          </PpActionButton>
          <span>
            Página {filters.page} de {pageCount}
          </span>
          <PpActionButton
            variant="ghost"
            disabled={filters.page >= pageCount}
            onClick={() => setFilters({ page: filters.page + 1 })}
          >
            Próxima
          </PpActionButton>
        </div>
      ) : null}
    </div>
  );
}
