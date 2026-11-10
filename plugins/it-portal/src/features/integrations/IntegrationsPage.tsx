import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type ArchiveFilter, type Integration, type IntegrationListQuery } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge } from "../../app/badges";
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
  ADMINISTRATIVE_STATUS_OPTIONS,
  ARCHIVED_OPTIONS,
  CRITICALITY_OPTIONS,
  INTEGRATION_DIRECTION_LABELS,
  INTEGRATION_PROTOCOL_LABELS,
  INTEGRATION_PROTOCOL_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { IntegrationEndpoint } from "./IntegrationEndpoint";
import { IntegrationFormModal } from "./IntegrationFormModal";

export function IntegrationsPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_integrations === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [protocol, setProtocol] = useState("");
  const [criticality, setCriticality] = useState("");
  const [status, setStatus] = useState("");
  const [archived, setArchived] = useState<ArchiveFilter>("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: IntegrationListQuery = {
    q: q || undefined,
    protocol: protocol || undefined,
    criticality: criticality || undefined,
    administrative_status: status || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const integrationsQuery = useQuery({
    queryKey: queryKeys.integrationList(query),
    queryFn: ({ signal }) => itPortalApi.listIntegrations(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || protocol || criticality || status) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setProtocol("");
    setCriticality("");
    setStatus("");
    setArchived("active");
    list.resetPage();
  };
  const withReset = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    list.resetPage();
  };

  const columns: DataTableColumn<Integration>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    { key: "name", header: "Integração", sortable: true, render: (row) => <strong>{row.name}</strong> },
    { key: "source", header: "Origem", interactive: true, render: (row) => <IntegrationEndpoint integration={row} side="source" /> },
    { key: "target", header: "Destino", interactive: true, render: (row) => <IntegrationEndpoint integration={row} side="target" /> },
    {
      key: "protocol",
      header: "Protocolo",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <span>{INTEGRATION_PROTOCOL_LABELS[row.protocol]}</span>
          <span className="itp-muted">{INTEGRATION_DIRECTION_LABELS[row.direction]}</span>
        </span>
      ),
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
    { key: "updated_at", header: "Atualizado em", sortable: true, render: (row) => formatDateTime(row.updated_at) },
  ];

  return (
    <>
      <ItpPageHero
        aria-label="Integrações"
        eyebrow="Inventário"
        title="Integrações"
        description="Trocas de dados entre serviços cadastrados, ou entre um serviço e um sistema externo. Não registre credenciais, tokens nem payloads."
        actions={
          canManage ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar integração
            </ItpActionButton>
          ) : null
        }
      />
      {integrationsQuery.error && !integrationsQuery.data ? (
        <QueryErrorState error={toApiError(integrationsQuery.error)} onRetry={() => void integrationsQuery.refetch()} />
      ) : (
        <DataTableSection<Integration>
          title="Inventário de integrações"
          columns={columns}
          rows={integrationsQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={integrationsQuery.isPending}
          refreshing={integrationsQuery.isFetching && !integrationsQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhuma integração corresponde aos filtros."
              : canManage
                ? "Nenhuma integração cadastrada. Use «Cadastrar integração» para começar."
                : "Nenhuma integração cadastrada ainda."
          }
          searchPlaceholder="Buscar por nome, finalidade ou sistema externo…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: integrationsQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{ sortKey: list.sort, sortDirection: list.direction, onSortChange: list.onSortChange }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { integrationId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField
                label="Protocolo"
                options={INTEGRATION_PROTOCOL_OPTIONS}
                value={protocol}
                allowEmpty
                onChange={withReset(setProtocol)}
              />
              <ItpSelectField
                label="Criticidade"
                options={CRITICALITY_OPTIONS}
                value={criticality}
                allowEmpty
                onChange={withReset(setCriticality)}
              />
              <ItpSelectField
                label="Situação"
                options={ADMINISTRATIVE_STATUS_OPTIONS}
                value={status}
                allowEmpty
                onChange={withReset(setStatus)}
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
        <IntegrationFormModal
          onClose={() => setCreating(false)}
          onSaved={(integration) => navigateTo(buildPath(basePath, { integrationId: integration.id }))}
        />
      ) : null}
    </>
  );
}
