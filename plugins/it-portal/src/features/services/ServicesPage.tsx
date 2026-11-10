import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type ArchiveFilter, type Service, type ServiceListQuery } from "../../api/itPortalApi";
import {
  AdministrativeStatusBadge,
  ArchivedBadge,
  CriticalityBadge,
  EnvironmentBadge,
  ServiceKindBadge,
} from "../../app/badges";
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
  SERVICE_KIND_OPTIONS,
  SERVICE_TYPE_LABELS,
  UNIT_LABELS,
  UNIT_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { ServiceFormModal } from "./ServiceFormModal";

export function ServicesPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_services === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState("");
  const [unit, setUnit] = useState("");
  const [environment, setEnvironment] = useState("");
  const [criticality, setCriticality] = useState("");
  const [archived, setArchived] = useState<ArchiveFilter>("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: ServiceListQuery = {
    q: q || undefined,
    service_kind: kind || undefined,
    unit_code: unit || undefined,
    environment: environment || undefined,
    criticality: criticality || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const servicesQuery = useQuery({
    queryKey: queryKeys.serviceList(query),
    queryFn: ({ signal }) => itPortalApi.listServices(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || kind || unit || environment || criticality) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setKind("");
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

  const columns: DataTableColumn<Service>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "name",
      header: "Serviço",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.name}</strong>
          <span className="itp-muted">
            {SERVICE_TYPE_LABELS[row.service_type]}
            {row.technology ? ` · ${row.technology}` : ""}
          </span>
        </span>
      ),
    },
    { key: "kind", header: "Natureza", render: (row) => <ServiceKindBadge value={row.service_kind} /> },
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
    { key: "hostings", header: "Servidores", align: "right", render: (row) => row.hosting_count },
    { key: "databases", header: "Bancos", align: "right", render: (row) => row.database_count },
    { key: "updated_at", header: "Atualizado em", sortable: true, render: (row) => formatDateTime(row.updated_at) },
  ];

  return (
    <>
      <ItpPageHero
        aria-label="Serviços e aplicações"
        eyebrow="Inventário"
        title="Serviços e aplicações"
        description="Aplicações de negócio e serviços de plataforma, com os servidores onde executam e os bancos que utilizam. Cadastro manual — não há descoberta automática."
        actions={
          canManage ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar serviço
            </ItpActionButton>
          ) : null
        }
      />
      {servicesQuery.error && !servicesQuery.data ? (
        <QueryErrorState error={toApiError(servicesQuery.error)} onRetry={() => void servicesQuery.refetch()} />
      ) : (
        <DataTableSection<Service>
          title="Inventário de serviços"
          columns={columns}
          rows={servicesQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={servicesQuery.isPending}
          refreshing={servicesQuery.isFetching && !servicesQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhum serviço corresponde aos filtros."
              : canManage
                ? "Nenhum serviço cadastrado. Use «Cadastrar serviço» para começar."
                : "Nenhum serviço cadastrado ainda."
          }
          searchPlaceholder="Buscar por nome ou tecnologia…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: servicesQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{ sortKey: list.sort, sortDirection: list.direction, onSortChange: list.onSortChange }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { serviceId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField label="Natureza" options={SERVICE_KIND_OPTIONS} value={kind} allowEmpty onChange={withReset(setKind)} />
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
        <ServiceFormModal
          onClose={() => setCreating(false)}
          onSaved={(service) => navigateTo(buildPath(basePath, { serviceId: service.id }))}
        />
      ) : null}
    </>
  );
}
