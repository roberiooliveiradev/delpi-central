import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Pencil, RefreshCcw } from "lucide-react";
import { useState, type ReactNode } from "react";

import { itPortalApi, type ActionPlan, type ActionPlanListQuery } from "../../api/itPortalApi";
import { ActionStatusBadge, PriorityBadge } from "../../app/badges";
import { formatDate, orDash } from "../../app/format";
import { ItpActionButton } from "../../app/itPortalUi";
import { DataTableSection, type DataTableColumn } from "../../app/itpDataTableUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { ActionPlanFormModal, ActionPlanStatusModal } from "./ActionPlanModals";

type ModalState = { kind: "edit" | "status"; plan: ActionPlan } | null;

export function ActionPlanTable({
  title,
  query,
  showServer,
  emptyMessage,
  toolbarFilters,
  headerActions,
  search,
  onSearchChange,
  onPageChange,
  onPageSizeChange,
  onSortChange,
}: {
  title: string;
  query: ActionPlanListQuery;
  showServer: boolean;
  emptyMessage: string;
  toolbarFilters?: ReactNode;
  headerActions?: ReactNode;
  search?: string;
  onSearchChange?: (value: string) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (key: string) => void;
}) {
  const { basePath, capabilities } = usePortal();
  const canManage = capabilities?.can_manage_action_plans === true;
  const [modal, setModal] = useState<ModalState>(null);

  const listQuery = useQuery({
    queryKey: queryKeys.actionPlanList(query),
    queryFn: ({ signal }) => itPortalApi.listActionPlans(query, signal),
    placeholderData: keepPreviousData,
  });

  const columns: DataTableColumn<ActionPlan>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    {
      key: "title",
      header: "Plano de ação",
      sortable: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <strong>{row.title}</strong>
          {row.responsible ? <span className="itp-muted">{row.responsible}</span> : null}
        </span>
      ),
    },
    ...(showServer
      ? [
          {
            key: "server",
            header: "Servidor",
            interactive: true,
            render: (row: ActionPlan) => (
              <ItpActionButton
                variant="link"
                href={buildPath(basePath, { serverId: row.server_id })}
                title={`Abrir ${row.server.name}`}
                onClick={spaNavigate(buildPath(basePath, { serverId: row.server_id }))}
              >
                {row.server.name}
              </ItpActionButton>
            ),
          } satisfies DataTableColumn<ActionPlan>,
        ]
      : []),
    { key: "priority", header: "Prioridade", sortable: true, render: (row) => <PriorityBadge value={row.priority} /> },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (row) => <ActionStatusBadge value={row.status} overdue={row.is_overdue} />,
    },
    { key: "due_date", header: "Prazo", sortable: true, render: (row) => formatDate(row.due_date) },
    { key: "updated_by", header: "Atualizado por", render: (row) => orDash(row.updated_by_name) },
    ...(canManage
      ? [
          {
            key: "actions",
            header: "Ações",
            interactive: true,
            align: "right" as const,
            render: (row: ActionPlan) => (
              <span className="itp-row-actions">
                <ItpActionButton
                  variant="ghost"
                  aria-label={`Editar ${row.code}`}
                  onClick={() => setModal({ kind: "edit", plan: row })}
                >
                  <Pencil size={14} strokeWidth={1.75} aria-hidden="true" /> Editar
                </ItpActionButton>
                <ItpActionButton
                  variant="ghost"
                  aria-label={`Alterar status de ${row.code}`}
                  onClick={() => setModal({ kind: "status", plan: row })}
                >
                  <RefreshCcw size={14} strokeWidth={1.75} aria-hidden="true" /> Status
                </ItpActionButton>
              </span>
            ),
          } satisfies DataTableColumn<ActionPlan>,
        ]
      : []),
  ];

  if (listQuery.error && !listQuery.data) {
    return <QueryErrorState error={toApiError(listQuery.error)} onRetry={() => void listQuery.refetch()} />;
  }

  const page = listQuery.data;
  return (
    <>
      <DataTableSection<ActionPlan>
        title={title}
        columns={columns}
        rows={page?.items ?? []}
        rowKey={(row) => row.id}
        loading={listQuery.isPending}
        refreshing={listQuery.isFetching && !listQuery.isPending}
        emptyMessage={emptyMessage}
        hideSearch={!onSearchChange}
        serverSearch={onSearchChange ? { value: search ?? "", onChange: onSearchChange } : undefined}
        searchPlaceholder="Buscar por título ou servidor…"
        serverPagination={{
          page: query.page ?? 1,
          pageSize: query.page_size ?? 20,
          total: page?.total ?? 0,
          onPageChange,
          onPageSizeChange,
        }}
        serverSort={{
          sortKey: query.sort ?? "due_date",
          sortDirection: query.direction ?? "asc",
          onSortChange,
        }}
        toolbarFilters={toolbarFilters}
        headerActions={headerActions}
      />
      {modal?.kind === "edit" ? (
        <ActionPlanFormModal open serverId={modal.plan.server_id} plan={modal.plan} onClose={() => setModal(null)} />
      ) : null}
      {modal?.kind === "status" ? (
        <ActionPlanStatusModal open plan={modal.plan} onClose={() => setModal(null)} />
      ) : null}
    </>
  );
}

/** Estado de listagem server-side (página, ordenação, busca) compartilhado pelas tabelas. */
export function useListState<TSort extends string>(defaultSort: TSort, defaultDirection: "asc" | "desc" = "asc") {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sort, setSort] = useState<TSort>(defaultSort);
  const [direction, setDirection] = useState<"asc" | "desc">(defaultDirection);
  return {
    page,
    pageSize,
    sort,
    direction,
    setPage,
    resetPage: () => setPage(1),
    onPageSizeChange: (size: number) => {
      setPageSize(size);
      setPage(1);
    },
    onSortChange: (key: string) => {
      if (key === sort) {
        setDirection((current) => (current === "asc" ? "desc" : "asc"));
      } else {
        setSort(key as TSort);
        setDirection("asc");
      }
      setPage(1);
    },
  };
}
