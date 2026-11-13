import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type Workstation, type WorkstationListQuery } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge } from "../../app/badges";
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
  UNIT_LABELS,
  UNIT_OPTIONS,
  WORKSTATION_KIND_LABELS,
  WORKSTATION_KIND_OPTIONS,
} from "../../content/labels";
import { useListState } from "../action-plans/ActionPlanTable";
import { WorkstationFormModal } from "./WorkstationFormModal";

export function WorkstationsPage() {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_computers === true;
  const list = useListState("name");
  const [search, setSearch] = useState("");
  const [unit, setUnit] = useState("");
  const [kind, setKind] = useState("");
  const [status, setStatus] = useState("");
  const [archived, setArchived] = useState<"active" | "archived" | "all">("active");
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search);

  const query: WorkstationListQuery = {
    q: q || undefined,
    unit_code: unit || undefined,
    device_kind: kind || undefined,
    administrative_status: status || undefined,
    archived,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const computersQuery = useQuery({
    queryKey: queryKeys.workstationList(query),
    queryFn: ({ signal }) => itPortalApi.listWorkstations(query, signal),
    placeholderData: keepPreviousData,
  });

  const filtersActive = Boolean(search || unit || kind || status) || archived !== "active";
  const clearFilters = () => {
    setSearch("");
    setUnit("");
    setKind("");
    setStatus("");
    setArchived("active");
    list.resetPage();
  };
  const withReset = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    list.resetPage();
  };

  const columns: DataTableColumn<Workstation>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "name",
      header: "Computador",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.name}</strong>
          <span className="itp-muted">{row.hostname}</span>
        </span>
      ),
    },
    {
      key: "device_kind",
      header: "Tipo",
      sortable: true,
      render: (row) => WORKSTATION_KIND_LABELS[row.device_kind],
    },
    {
      key: "unit",
      header: "Unidade",
      render: (row) => UNIT_LABELS[row.unit_code] ?? row.unit_code,
    },
    {
      key: "department",
      header: "Setor",
      render: (row) => row.department || "—",
    },
    {
      key: "status",
      header: "Situação cadastral",
      render: (row) => row.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={row.administrative_status} />,
    },
    {
      key: "updated_at",
      header: "Atualizado em",
      sortable: true,
      render: (row) => formatDateTime(row.updated_at),
    },
  ];

  return (
    <>
      <ItpPageHero
        variant="immersive"
        aria-label="Computadores"
        eyebrow="Inventário · Delpi Remote"
        title="Computadores"
        description="Cadastre desktops e notebooks da empresa. Esta é a situação do cadastro, não o estado online da máquina. Monitoramento e acesso remoto serão liberados em etapas futuras."
        actions={canManage ? (
          <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
            <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar computador
          </ItpActionButton>
        ) : null}
      />
      {computersQuery.error && !computersQuery.data ? (
        <QueryErrorState error={toApiError(computersQuery.error)} onRetry={() => void computersQuery.refetch()} />
      ) : (
        <DataTableSection<Workstation>
          title="Inventário de computadores"
          columns={columns}
          rows={computersQuery.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={computersQuery.isPending}
          refreshing={computersQuery.isFetching && !computersQuery.isPending}
          emptyMessage={
            filtersActive
              ? "Nenhum computador corresponde aos filtros."
              : canManage
                ? "Nenhum computador cadastrado. Use «Cadastrar computador» para começar."
                : "Nenhum computador cadastrado ainda."
          }
          searchPlaceholder="Buscar por nome, hostname, IP ou setor…"
          serverSearch={{ value: search, onChange: withReset(setSearch) }}
          serverPagination={{
            page: list.page,
            pageSize: list.pageSize,
            total: computersQuery.data?.total ?? 0,
            onPageChange: list.setPage,
            onPageSizeChange: list.onPageSizeChange,
          }}
          serverSort={{
            sortKey: list.sort,
            sortDirection: list.direction,
            onSortChange: list.onSortChange,
          }}
          onRowClick={(row) => navigateTo(buildPath(basePath, { workstationId: row.id }))}
          toolbarFilters={
            <div className="itp-filters">
              <ItpSelectField label="Unidade" options={UNIT_OPTIONS} value={unit} allowEmpty onChange={withReset(setUnit)} />
              <ItpSelectField label="Tipo" options={WORKSTATION_KIND_OPTIONS} value={kind} allowEmpty onChange={withReset(setKind)} />
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
        <WorkstationFormModal
          onClose={() => setCreating(false)}
          onSaved={(workstation) => navigateTo(buildPath(basePath, { workstationId: workstation.id }))}
        />
      ) : null}
    </>
  );
}
