import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type Server, type ServerListQuery } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge, EnvironmentBadge } from "../../app/badges";
import { formatDateTime } from "../../app/format";
import { ItpActionButton, ItpPageHero, ItpSelectField } from "../../app/itPortalUi";
import { DataTableSection, type DataTableColumn } from "../../app/itpDataTableUi";
import { navigateTo } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { useDebouncedValue } from "../../app/useDebouncedValue";
import {
  ARCHIVED_OPTIONS,
  CRITICALITY_OPTIONS,
  ENVIRONMENT_OPTIONS,
  UNIT_LABELS,
  UNIT_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { ServerFormModal } from "./ServerFormModal";

export function ServersPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_servers === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [unit, setUnit] = useState("");
  const [environment, setEnvironment] = useState("");
  const [criticality, setCriticality] = useState("");
  const [archived, setArchived] = useState<"active" | "archived" | "all">("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: ServerListQuery = {
    q: q || undefined,
    unit_code: unit || undefined,
    environment: environment || undefined,
    criticality: criticality || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const serversQuery = useQuery({
    queryKey: queryKeys.serverList(query),
    queryFn: ({ signal }) => itPortalApi.listServers(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || unit || environment || criticality) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setUnit("");
    setEnvironment("");
    setCriticality("");
    setArchived("active");
    list.resetPage();
  };
  const withReset = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    list.resetPage();
  };

  const columns: DataTableColumn<Server>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "name",
      header: "Servidor",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.name}</strong>
          <span className="itp-muted">{row.hostname}</span>
        </span>
      ),
    },
    {
      key: "environment",
      header: "Ambiente",
      sortable: true,
      render: (row) => <EnvironmentBadge value={row.environment} />,
    },
    { key: "unit", header: "Unidade", render: (row) => UNIT_LABELS[row.unit_code] ?? row.unit_code },
    {
      key: "criticality",
      header: "Criticidade",
      sortable: true,
      render: (row) => <CriticalityBadge value={row.criticality} />,
    },
    {
      key: "status",
      header: "Situação",
      render: (row) => (row.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={row.administrative_status} />),
    },
    { key: "open_actions", header: "Ações abertas", align: "right", render: (row) => row.open_action_count },
    { key: "updated_at", header: "Atualizado em", sortable: true, render: (row) => formatDateTime(row.updated_at) },
  ];

  const createButton = canManage ? (
    <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
      <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar servidor
    </ItpActionButton>
  ) : null;

  return (
    <>
      <ItpPageHero
        aria-label="Servidores"
        eyebrow="Inventário"
        title="Servidores"
        description="Cadastro manual dos servidores da infraestrutura. A situação é informada pela equipe de TI — não há monitoramento automático nesta etapa."
        actions={createButton}
      />
      {serversQuery.error && !serversQuery.data ? (
        <QueryErrorState error={toApiError(serversQuery.error)} onRetry={() => void serversQuery.refetch()} />
      ) : (
        <DataTableSection<Server>
          title="Inventário de servidores"
          columns={columns}
          rows={serversQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={serversQuery.isPending}
          refreshing={serversQuery.isFetching && !serversQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhum servidor corresponde aos filtros."
              : canManage
                ? "Nenhum servidor cadastrado. Use «Cadastrar servidor» para começar."
                : "Nenhum servidor cadastrado ainda."
          }
          searchPlaceholder="Buscar por nome ou hostname…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: serversQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{ sortKey: list.sort, sortDirection: list.direction, onSortChange: list.onSortChange }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { serverId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField label="Unidade" options={UNIT_OPTIONS} value={unit} allowEmpty onChange={withReset(setUnit)} />
              <ItpSelectField
                label="Ambiente"
                options={ENVIRONMENT_OPTIONS}
                value={environment}
                allowEmpty
                onChange={withReset(setEnvironment)}
              />
              <ItpSelectField
                label="Criticidade"
                options={CRITICALITY_OPTIONS}
                value={criticality}
                allowEmpty
                onChange={withReset(setCriticality)}
              />
              <ItpSelectField
                label="Cadastro"
                options={ARCHIVED_OPTIONS}
                value={archived}
                onChange={(value) => {
                  setArchived((value || "active") as typeof archived);
                  list.resetPage();
                }}
              />
              {filtersActive ? (
                <ItpActionButton variant="link" onClick={clearFilters}>
                  Limpar filtros
                </ItpActionButton>
              ) : null}
            </div>
          }
        />
      )}
      {creating ? (
        <ServerFormModal
          open
          onClose={() => setCreating(false)}
          onSaved={(server) => navigateTo(buildPath(basePath, { serverId: server.id }))}
        />
      ) : null}
    </>
  );
}
