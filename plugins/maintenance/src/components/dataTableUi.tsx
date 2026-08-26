import type { ReactNode } from "react";

import {
  createDashboardDataTableKit,
  dataTableBemClasses,
  type DashboardDataTableSectionProps,
  type DataTableColumn,
  type DataTableClassNames,
} from "@delpi/plugin-ui/index";

import { MaintenanceLoadingCard } from "../app/maintenanceUi";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";
import type { ServerTableConfig } from "./data/types";
import {
  DmTablePageSizeSelect,
  DmTablePagination,
  TABLE_PAGE_SIZE_OPTIONS,
} from "./dmPaginationKit";

import "./data/DataTable.css";

const DM_TABLE_CLASS_NAMES: DataTableClassNames = {
  ...dataTableBemClasses("dm"),
  outerRoot: "dm-datatable",
  scrollWrap: "dm-datatable__scroll dm-table-wrap delpi-ui-table-wrap",
  sortableColumn: "dm-table__col--sortable delpi-ui-table__col--sortable",
  rowClickable: `${dataTableBemClasses("dm").rowClickable} is-clickable`,
};

const TABLE_LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) => `${total} registro(s)`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
  initialLoadingTitle: "Carregando registros",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: "dm",
  labels: TABLE_LABELS,
  LoadingActivityCard: MaintenanceLoadingCard,
  Pagination: DmTablePagination,
  TablePageSizeSelect: DmTablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 20,
  tableClassNames: DM_TABLE_CLASS_NAMES,
});

const KitDataTableSection = kit.DataTableSection;

export const DEFAULT_TABLE_PAGE_SIZE = 20;

export type MaintenanceDataTableSectionProps<T> = Omit<
  DashboardDataTableSectionProps<T>,
  "rowKey"
> & {
  /** Compat legado — preferir `rowKey`. */
  getRowKey?: (row: T, index?: number) => string;
  rowKey?: (row: T) => string;
  /** Compat legado — mapeado para `serverPagination` + `serverSort`. */
  serverTable?: ServerTableConfig;
  /** Compat legado — mapeado para `headerActions`. */
  actions?: ReactNode;
  /** Compat legado — mapeado para `toolbarFilters` (largura total abaixo do toggle Tabela/Cards). */
  toolbar?: ReactNode;
  countBadgeLabel?: string;
  badge?: ReactNode;
  className?: string;
  hidePaginationWhenSinglePage?: boolean;
};

export function DataTableSection<T>({
  getRowKey,
  rowKey,
  serverTable,
  actions,
  toolbar,
  countBadgeLabel,
  badge,
  className,
  hidePaginationWhenSinglePage: _hidePaginationWhenSinglePage,
  hideSearch = true,
  hidePageSizeSelect = true,
  hint,
  ...rest
}: MaintenanceDataTableSectionProps<T>) {
  const resolvedRowKey =
    rowKey ??
    ((row: T) => {
      if (!getRowKey) {
        throw new Error("DataTableSection exige rowKey ou getRowKey.");
      }
      return getRowKey(row, 0);
    });

  const resolvedHint =
    hint ??
    (typeof badge === "string" ? badge : undefined) ??
    (countBadgeLabel ? undefined : undefined);

  const section = (
    <KitDataTableSection
      {...rest}
      rowKey={resolvedRowKey}
      headerActions={actions ?? rest.headerActions}
      toolbarFilters={toolbar ?? rest.toolbarFilters}
      toolbarLeading={rest.toolbarLeading}
      hideSearch={hideSearch}
      hidePageSizeSelect={hidePageSizeSelect}
      hint={resolvedHint}
      serverPagination={
        serverTable
          ? {
              page: serverTable.page,
              pageSize: serverTable.pageSize,
              total: serverTable.total,
              onPageChange: serverTable.onPageChange,
            }
          : rest.serverPagination
      }
      serverSort={
        serverTable
          ? {
              sortKey: serverTable.sortKey,
              sortDirection: serverTable.sortDirection,
              onSortChange: serverTable.onSortChange,
            }
          : rest.serverSort
      }
    />
  );

  if (!className) return section;
  return <div className={className}>{section}</div>;
}

export const DataTable = kit.DataTable;

export type { DataTableColumn };
export type {
  DashboardDataTableSectionProps,
  ServerPaginationConfig,
  ServerSortConfig,
} from "@delpi/plugin-ui/index";
