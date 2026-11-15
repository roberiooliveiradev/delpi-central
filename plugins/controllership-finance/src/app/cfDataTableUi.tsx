/** Kit DataTable do Portal — fábricas `@delpi/plugin-ui`, prefixo `cf`. */
import type { ReactNode } from "react";

import {
  createDashboardDataTableKit,
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type DashboardDataTableSectionProps,
  type DataTableColumn,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";
import { CF_HELP } from "../content/helpTooltips";
import {
  CfInteractiveDataCard,
  CfLoadingCard,
  UI_PREFIX,
} from "./controllershipFinanceUi";

const P = CF_HELP.closing.pagination;

const paginationKit = createDashboardPaginationKit({
  prefix: UI_PREFIX,
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da tabela",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({ rangeStart, rangeEnd, total, page, totalPages }) =>
      `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Ir para página",
    jumpError: (reason: PageJumpValidationReason, totalPages: number) => {
      switch (reason) {
        case "empty":
          return P.jumpEmpty;
        case "invalid":
          return P.jumpInvalid;
        case "below_min":
          return P.jumpBelowMin;
        case "above_max":
          return `A página máxima é ${totalPages}.`;
        default:
          return "";
      }
    },
  },
});

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) =>
    `${total.toLocaleString("pt-BR")} ${total === 1 ? "registro" : "registros"}`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
  initialLoadingTitle: "Carregando registros",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: UI_PREFIX,
  labels: LABELS,
  LoadingActivityCard: CfLoadingCard,
  Pagination: paginationKit.Pagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 50,
});

const KitDataTableSection = kit.DataTableSection;

/**
 * DataTableSection do portal — paginação inteligente por padrão:
 * o rodapé de paginação só aparece quando há mais de uma página
 * navegável no conjunto exibido (client ou server-side). O seletor
 * «Itens por página» na toolbar permanece sempre disponível.
 * Opt-out pontual via `hidePaginationWhenSinglePage={false}`.
 */
export function DataTableSection<T>(props: DashboardDataTableSectionProps<T>) {
  return <KitDataTableSection hidePaginationWhenSinglePage {...props} />;
}

/** Converte decimal serializado («1234.50») em número para `sortValue` de colunas numéricas. */
export function cfNumericSortValue(
  value: string | number | null | undefined,
): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Card mobile derivado das colunas da tabela (U12): a mesma definição de
 * coluna alimenta tabela e cards — sem segunda fonte de rótulos/valores.
 * A primeira coluna vira título; `onActivate` torna o card clicável.
 */
export function renderCfRecordCard<T>(
  columns: ReadonlyArray<DataTableColumn<T>>,
  row: T,
  options: {
    ariaLabel?: string;
    onActivate?: (row: T) => void;
    openHint?: string;
    skipKeys?: readonly string[];
  } = {},
): ReactNode {
  const skip = new Set(options.skipKeys ?? []);
  const fields = columns
    .filter((column) => !skip.has(column.key) && column.header.trim() !== "")
    .map((column, index) => ({
      id: column.key,
      label: column.mobileLabel ?? column.header,
      value: column.render(row),
      valueTone: index === 0 ? ("title" as const) : undefined,
    }));
  const onActivate = options.onActivate;
  return (
    <CfInteractiveDataCard
      ariaLabel={options.ariaLabel}
      fields={fields}
      onActivate={onActivate ? () => onActivate(row) : undefined}
      openHint={onActivate ? (options.openHint ?? "Abrir detalhes") : undefined}
    />
  );
}

export { TABLE_PAGE_SIZE_OPTIONS };

export type { DataTableColumn } from "@delpi/plugin-ui/index";
export type {
  DashboardDataTableSectionProps as DataTableSectionProps,
  ServerPaginationConfig,
} from "@delpi/plugin-ui/index";
