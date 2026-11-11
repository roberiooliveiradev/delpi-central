import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import {
  itPortalApi,
  type ArchiveFilter,
  type DatabaseInstance,
  type DatabaseListQuery,
} from "../../api/itPortalApi";
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
  DBMS_LABELS,
  DBMS_OPTIONS,
  ENVIRONMENT_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { DatabaseFormModal } from "./DatabaseFormModal";

export function DatabasesPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_databases === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [dbms, setDbms] = useState("");
  const [environment, setEnvironment] = useState("");
  const [criticality, setCriticality] = useState("");
  const [archived, setArchived] = useState<ArchiveFilter>("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: DatabaseListQuery = {
    q: q || undefined,
    dbms: dbms || undefined,
    environment: environment || undefined,
    criticality: criticality || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const databasesQuery = useQuery({
    queryKey: queryKeys.databaseList(query),
    queryFn: ({ signal }) => itPortalApi.listDatabases(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || dbms || environment || criticality) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setDbms("");
    setEnvironment("");
    setCriticality("");
    setArchived("active");
    list.resetPage();
  };
  const withReset = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    list.resetPage();
  };

  const columns: DataTableColumn<DatabaseInstance>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "name",
      header: "Instância",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.name}</strong>
          <span className="itp-muted">{row.purpose ?? "—"}</span>
        </span>
      ),
    },
    {
      key: "dbms",
      header: "SGBD",
      sortable: true,
      render: (row) => `${DBMS_LABELS[row.dbms]}${row.version ? ` ${row.version}` : ""}`,
    },
    {
      key: "server",
      header: "Servidor",
      render: (row) => (
        <span className="itp-cell-stack">
          <span>{row.server.name}</span>
          <span className="itp-muted">{row.server.hostname}</span>
        </span>
      ),
    },
    {
      key: "environment",
      header: "Ambiente",
      sortable: true,
      render: (row) => <EnvironmentBadge value={row.environment} />,
    },
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
    { key: "consumers", header: "Serviços", align: "right", render: (row) => row.consumer_count },
    { key: "updated_at", header: "Atualizado em", sortable: true, render: (row) => formatDateTime(row.updated_at) },
  ];

  return (
    <>
      <ItpPageHero
        variant="immersive"
        aria-label="Bancos de dados"
        eyebrow="Inventário"
        title="Bancos de dados"
        description="Instâncias de bancos de dados, o servidor que as hospeda e os serviços que as utilizam. Somente dados descritivos — credenciais ficam no cofre corporativo."
        actions={
          canManage ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar instância
            </ItpActionButton>
          ) : null
        }
      />
      {databasesQuery.error && !databasesQuery.data ? (
        <QueryErrorState error={toApiError(databasesQuery.error)} onRetry={() => void databasesQuery.refetch()} />
      ) : (
        <DataTableSection<DatabaseInstance>
          title="Inventário de bancos de dados"
          columns={columns}
          rows={databasesQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={databasesQuery.isPending}
          refreshing={databasesQuery.isFetching && !databasesQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhuma instância corresponde aos filtros."
              : canManage
                ? "Nenhuma instância cadastrada. Use «Cadastrar instância» para começar."
                : "Nenhuma instância cadastrada ainda."
          }
          searchPlaceholder="Buscar por nome, versão ou servidor…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: databasesQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{ sortKey: list.sort, sortDirection: list.direction, onSortChange: list.onSortChange }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { databaseId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField label="SGBD" options={DBMS_OPTIONS} value={dbms} allowEmpty onChange={withReset(setDbms)} />
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
                  setArchived((value || "active") as ArchiveFilter);
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
        <DatabaseFormModal
          onClose={() => setCreating(false)}
          onSaved={(database) => navigateTo(buildPath(basePath, { databaseId: database.id }))}
        />
      ) : null}
    </>
  );
}
