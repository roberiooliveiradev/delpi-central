import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type ArchiveFilter, type Network, type NetworkListQuery } from "../../api/itPortalApi";
import { ArchivedBadge, CriticalityBadge, EnvironmentBadge, NetworkScopeBadge } from "../../app/badges";
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
  NETWORK_SCOPE_OPTIONS,
  UNIT_LABELS,
  UNIT_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { NetworkFormModal } from "./NetworkFormModal";

export function NetworksPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_networks === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [scope, setScope] = useState("");
  const [unit, setUnit] = useState("");
  const [environment, setEnvironment] = useState("");
  const [criticality, setCriticality] = useState("");
  const [archived, setArchived] = useState<ArchiveFilter>("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: NetworkListQuery = {
    q: q || undefined,
    network_scope: scope || undefined,
    unit_code: unit || undefined,
    environment: environment || undefined,
    criticality: criticality || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const networksQuery = useQuery({
    queryKey: queryKeys.networkList(query),
    queryFn: ({ signal }) => itPortalApi.listNetworks(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || scope || unit || environment || criticality) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setScope("");
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

  const columns: DataTableColumn<Network>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "name",
      header: "Rede",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.name}</strong>
          <span className="itp-muted">
            {row.cidr}
            {row.vlan_id !== null ? ` · VLAN ${row.vlan_id}` : ""}
          </span>
        </span>
      ),
    },
    { key: "scope", header: "Escopo", render: (row) => <NetworkScopeBadge value={row.network_scope} /> },
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
    { key: "status", header: "Situação", render: (row) => (row.archived ? <ArchivedBadge /> : "Ativa") },
    { key: "servers", header: "Servidores", align: "right", render: (row) => row.server_count },
    { key: "updated_at", header: "Atualizado em", sortable: true, render: (row) => formatDateTime(row.updated_at) },
  ];

  return (
    <>
      <ItpPageHero
        aria-label="Redes"
        eyebrow="Inventário"
        title="Redes"
        description="Sub-redes e VLANs da infraestrutura e os servidores conectados a cada uma. Cadastro manual — o Portal de TI não faz varredura de rede."
        actions={
          canManage ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar rede
            </ItpActionButton>
          ) : null
        }
      />
      {networksQuery.error && !networksQuery.data ? (
        <QueryErrorState error={toApiError(networksQuery.error)} onRetry={() => void networksQuery.refetch()} />
      ) : (
        <DataTableSection<Network>
          title="Inventário de redes"
          columns={columns}
          rows={networksQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={networksQuery.isPending}
          refreshing={networksQuery.isFetching && !networksQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhuma rede corresponde aos filtros."
              : canManage
                ? "Nenhuma rede cadastrada. Use «Cadastrar rede» para começar."
                : "Nenhuma rede cadastrada ainda."
          }
          searchPlaceholder="Buscar por nome, CIDR, zona ou local…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: networksQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{ sortKey: list.sort, sortDirection: list.direction, onSortChange: list.onSortChange }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { networkId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField label="Escopo" options={NETWORK_SCOPE_OPTIONS} value={scope} allowEmpty onChange={withReset(setScope)} />
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
        <NetworkFormModal
          onClose={() => setCreating(false)}
          onSaved={(network) => navigateTo(buildPath(basePath, { networkId: network.id }))}
        />
      ) : null}
    </>
  );
}
