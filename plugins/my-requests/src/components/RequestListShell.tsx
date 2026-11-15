/**
 * Composição canônica das listas Minhas / Fila de trabalho —
 * paridade com Meus Chamados de TI usando apenas componentes do kit:
 * PagePath clicável, hero compacto (título, descrição, contagem,
 * Atualizar, ação) com a toolbar da grade via `toolbarPortalTarget`
 * (mesma instância/estado do DataTableSection — busca dominante,
 * Filtros, Ordenar, Colunas, itens/página, chips, Tabela|Cards) e a
 * grade `embedded` logo abaixo, sem card externo redundante.
 *
 * O domínio (merge, contratos, colunas, cards) fica nas páginas.
 */

import { ArrowUpDown, ListFilter, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  ActionButton,
  HintAction,
  SectionHintLabel,
  type DashboardFilterFieldDescriptor,
  type DashboardFilterRule,
  type DashboardSortFieldOption,
  type DashboardSortLevel,
  type DataTableColumn,
  type ScopeChip,
} from "@delpi/plugin-ui/index";

import { MyRequestsDataTableSection } from "../ui/dataTableUi";

import { REQUEST_LIST_SEARCH_DEBOUNCE_MS } from "../content/requestListFilters";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { headerSortDirection } from "../domain/requestListSort";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import {
  MyRequestsFilterRulesBuilder,
  MyRequestsListToolbarPopover,
  MyRequestsPageHero,
  MyRequestsPagePath,
  MyRequestsScopeChipBar,
  MyRequestsSortLevelsBuilder,
} from "../ui/mrUi";

export type RequestListSortConfig = {
  /** Catálogo de campos ordenáveis do contrato efetivo. */
  fields: readonly DashboardSortFieldOption[];
  /** Níveis de ordenação em edição (draft do popover). */
  levels: DashboardSortLevel[];
  /** Teto de níveis que o contrato suporta (1..3). */
  maxLevels: number;
  onChange: (levels: DashboardSortLevel[]) => void;
  /**
   * Aplica níveis — atômico: o chamador informa o estado a gravar
   * (header passa o novo nível; o popover passa o draft). Nunca
   * `onChange` + `onApply()` no mesmo tick — o apply fecharia sobre
   * o estado anterior.
   */
  onApply: (levels: DashboardSortLevel[]) => void;
  /** Rótulo resumido no gatilho (ex.: "Data"). */
  summaryLabel?: string;
};

export type RequestListFilterConfig = {
  /** Catálogo de campos filtráveis do contrato efetivo. */
  fields: readonly DashboardFilterFieldDescriptor[];
  /** Regras em edição (draft do popover). */
  rules: DashboardFilterRule[];
  onChange: (rules: DashboardFilterRule[]) => void;
  onApply: () => void;
  onClear: () => void;
};

export type RequestListShellProps<Row> = {
  title: string;
  /** Contexto acima do título (ex.: "Solicitações e demandas"). */
  eyebrow?: string;
  description?: ReactNode;
  /** Contagem autoritativa (ex.: "42 solicitações"). */
  count?: string;
  /** CTA principal do hero (ex.: Nova solicitação). */
  heroAction?: ReactNode;
  onRefresh: () => void;
  refreshing?: boolean;

  rows: Row[];
  columns: DataTableColumn<Row>[];
  rowKey: (row: Row) => string;
  loading?: boolean;
  error?: string | null;
  emptyMessage: string;
  /** Ajuda in-app da seção (tooltip do título da grade). */
  sectionHint?: string;
  searchHint?: string;
  searchPlaceholder?: string;

  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;

  /** Busca committed — o shell faz o debounce/Enter. */
  search: string;
  onSearchCommit: (value: string) => void;

  /** Chips de escopo rápido (status etc.). */
  chips?: ScopeChip[];
  chipsLabel?: string;
  onClearChips?: () => void;

  sort?: RequestListSortConfig;
  filter?: RequestListFilterConfig;

  /** Header-sort: coluna → campo do contrato (só colunas ordenáveis). */
  columnSortMap?: Record<string, string>;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";

  columnPrefsKey: string;
  viewLayoutKey: string;
  renderCard: (row: Row) => ReactNode;
};

export function RequestListShell<Row extends object>({
  title,
  eyebrow,
  description,
  count,
  heroAction,
  onRefresh,
  refreshing = false,
  rows,
  columns,
  rowKey,
  loading = false,
  error,
  emptyMessage,
  sectionHint,
  searchHint,
  searchPlaceholder = "Número, código, nome…",
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  search,
  onSearchCommit,
  chips,
  chipsLabel,
  onClearChips,
  sort,
  filter,
  columnSortMap,
  sortKey,
  sortDirection = "desc",
  columnPrefsKey,
  viewLayoutKey,
  renderCard,
}: RequestListShellProps<Row>) {
  const [searchDraft, setSearchDraft] = useState(search);
  const debounceRef = useRef<number | null>(null);
  /* Host da toolbar no body do hero — a MESMA toolbar da seção é
   * renderizada via portal (instância/estado únicos do kit). */
  const [toolbarHost, setToolbarHost] = useState<HTMLElement | null>(null);

  useEffect(() => setSearchDraft(search), [search]);

  const commitSearch = (value: string) => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    if (value.trim() !== search.trim()) onSearchCommit(value);
  };

  const handleSearch = (value: string) => {
    setSearchDraft(value);
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(
      () => commitSearch(value),
      REQUEST_LIST_SEARCH_DEBOUNCE_MS,
    );
  };

  useEffect(
    () => () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    },
    [],
  );

  /* Apenas colunas presentes no contrato exibem affordance de sort —
   * nunca um botão falso onde o backend não ordena. */
  const sortableColumns = useMemo(
    () =>
      columnSortMap
        ? columns.map((column) =>
            columnSortMap[column.key] ? { ...column, sortable: true } : column,
          )
        : columns,
    [columns, columnSortMap],
  );

  return (
    <>
      <MyRequestsPagePath
        back={{ label: "Início", href: "/" }}
        items={[
          {
            id: "module",
            label: "Minhas solicitações",
            href: myRequestsPath("mine"),
            onNavigate: (event: { preventDefault(): void }) => {
              event.preventDefault();
              navigateMyRequestsPath(myRequestsPath("mine"));
            },
          },
        ]}
        current={title}
      />

      <MyRequestsPageHero
        eyebrow={eyebrow}
        title={
          sectionHint ? (
            <SectionHintLabel label={title} hint={sectionHint} />
          ) : (
            title
          )
        }
        description={description}
        badge={count}
        actions={
          <>
            <HintAction hint="Recarrega a lista." ariaLabel="Ajuda: Atualizar">
              <ActionButton
                type="button"
                variant="ghost"
                aria-label="Atualizar"
                disabled={refreshing || loading}
                onClick={onRefresh}
              >
                <RefreshCw size={16} aria-hidden />
                Atualizar
              </ActionButton>
            </HintAction>
            {heroAction}
          </>
        }
      >
        <div
          ref={setToolbarHost}
          className="delpi-ui-list-toolbar-host"
          data-testid="request-list-toolbar-host"
        />
      </MyRequestsPageHero>

      {error ? (
        <div className="my-requests-list-error" role="alert">
          {error}
        </div>
      ) : null}

      <MyRequestsDataTableSection
        title=""
        embedded
        hideRecordsCount
        columns={sortableColumns}
        rows={rows}
        rowKey={rowKey}
        loading={loading}
        emptyMessage={emptyMessage}
        serverSearch={{ value: searchDraft, onChange: handleSearch }}
        searchPlaceholder={searchPlaceholder}
        searchHint={searchHint}
        serverPagination={{
          page,
          pageSize,
          total,
          onPageChange,
          onPageSizeChange,
        }}
        toolbarPortalTarget={toolbarHost}
        toolbarLayout="hero"
        toolbarExtraPlacement="before"
        serverSort={
          columnSortMap && sort
            ? {
                sortKey: sortKey ?? null,
                sortDirection,
                onSortChange: (columnKey) => {
                  const field = columnSortMap[columnKey];
                  if (!field) return;
                  const direction =
                    sortKey === columnKey
                      ? sortDirection === "asc"
                        ? "desc"
                        : "asc"
                      : headerSortDirection(field);
                  /* Aplicação atômica — o novo nível vai por extenso;
                   * setState + apply no mesmo tick aplicaria o estado
                   * anterior por closure (regressão UX-V2-HEADER-01). */
                  sort.onApply([{ field, direction }]);
                },
              }
            : undefined
        }
        toolbarExtra={
          <>
            {filter ? (
              <HintAction
                hint={MY_REQUESTS_HELP_TOOLTIPS.listUi.filterBuilderToggle}
                ariaLabel="Ajuda: Filtros avançados"
              >
                <MyRequestsListToolbarPopover
                  label="Filtros"
                  icon={<ListFilter size={16} aria-hidden />}
                  ariaLabel="Filtros avançados"
                  panelAriaLabel="Filtros avançados"
                  panelTitle="Filtros avançados"
                  panelHint="Refine a lista com um ou mais critérios."
                  wide
                >
                  {(close: () => void) => (
                    <MyRequestsFilterRulesBuilder
                      rules={filter.rules}
                      fields={filter.fields}
                      onChange={filter.onChange}
                      onClear={filter.onClear}
                      onApply={() => {
                        filter.onApply();
                        close();
                      }}
                    />
                  )}
                </MyRequestsListToolbarPopover>
              </HintAction>
            ) : null}
            {sort ? (
              <HintAction
                hint={MY_REQUESTS_HELP_TOOLTIPS.listUi.sortBuilderToggle}
                ariaLabel="Ajuda: Ordenação"
              >
                <MyRequestsListToolbarPopover
                  label={sort.summaryLabel ?? "Ordenar"}
                  icon={<ArrowUpDown size={16} aria-hidden />}
                  ariaLabel={
                    sort.summaryLabel
                      ? `Ordenar: ${sort.summaryLabel}`
                      : "Ordenar"
                  }
                  panelAriaLabel="Ordenação"
                  panelTitle="Ordenar"
                  panelHint={
                    sort.maxLevels > 1
                      ? "Até três níveis. O primeiro é o que a grade destaca."
                      : "Escolha a direção da ordenação."
                  }
                >
                  {(close: () => void) => (
                    <MyRequestsSortLevelsBuilder
                      levels={sort.levels}
                      options={sort.fields}
                      maxLevels={sort.maxLevels}
                      onChange={sort.onChange}
                      onApply={() => {
                        sort.onApply(sort.levels);
                        close();
                      }}
                    />
                  )}
                </MyRequestsListToolbarPopover>
              </HintAction>
            ) : null}
          </>
        }
        toolbarLeading={
          chips && chips.length ? (
            <HintAction
              hint={MY_REQUESTS_HELP_TOOLTIPS.listUi.statusChips}
              ariaLabel="Ajuda: Status"
            >
              <MyRequestsScopeChipBar
                chips={chips}
                label={chipsLabel}
                onClearAll={onClearChips}
              />
            </HintAction>
          ) : undefined
        }
        columnPreferencesKey={columnPrefsKey}
        viewLayoutPreferencesKey={viewLayoutKey}
        renderCard={renderCard}
      />
    </>
  );
}
