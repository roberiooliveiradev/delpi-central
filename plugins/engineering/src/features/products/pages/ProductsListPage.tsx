import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFieldLabel,
  EngineeringLoadingActivityCard,
  EngineeringMultiSelectField,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/DataTable";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchProductFilterOptions,
  searchProducts,
} from "../api/productApi";
import {
  PRODUCT_COPY,
  PRODUCT_HELP,
  productDescriptionDisplay,
  productStatusLabel,
  productTypeLabel,
} from "../productCopy";
import {
  PRODUCT_PATHS,
  buildProductsListUrl,
  navigateProducts,
  parseProductsListUrl,
  useLocationSearch,
  type ProductsListUrlState,
} from "../productRoutes";
import type { ProductFilterOptions, ProductRecord } from "../types";

const PAGE_SIZE = 50;
const DEBOUNCE_MS = 400;
const SORTABLE_COLUMNS = new Set(["code", "description", "group_code"]);

type TextDraft = {
  code: string;
  description: string;
  customer_reference: string;
};

function draftFrom(state: ProductsListUrlState): TextDraft {
  return {
    code: state.code,
    description: state.description,
    customer_reference: state.customer_reference,
  };
}

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

function commitListState(
  state: ProductsListUrlState,
  options?: { replace?: boolean },
) {
  navigateProducts(buildProductsListUrl(state), { replace: options?.replace ?? true });
}

export function ProductsListPage() {
  const search = useLocationSearch();
  const applied = useMemo(() => parseProductsListUrl(search), [search]);

  /* Draft dos campos de texto — o valor digitado vive aqui até o
   * debounce commitar na URL. Quando a URL muda por fora (voltar/
   * avançar/limpar/deep link), o draft ressincroniza durante o render
   * (padrão React de ajuste de estado derivado). */
  const [draft, setDraft] = useState<TextDraft>(() => draftFrom(applied));
  const [prevApplied, setPrevApplied] = useState(applied);
  if (prevApplied !== applied) {
    setPrevApplied(applied);
    setDraft(draftFrom(applied));
  }

  const [list, setList] = useState<{
    items: ProductRecord[];
    total: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestSeq = useRef(0);

  const load = useCallback(
    async (state: ProductsListUrlState, signal: AbortSignal) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      setError(null);
      try {
        const result = await searchProducts(
          {
            code: state.code || undefined,
            description: state.description || undefined,
            group_code: state.groups.length
              ? state.groups.join(",")
              : undefined,
            product_type: state.types.length
              ? state.types.join(",")
              : undefined,
            customer_reference: state.customer_reference || undefined,
            sort: state.sort ?? undefined,
            direction: state.sort ? state.direction : undefined,
            page: state.page,
            page_size: PAGE_SIZE,
          },
          signal,
        );
        if (seq !== requestSeq.current || signal.aborted) return;
        setList({ items: result.items, total: result.total });
      } catch (err) {
        if (seq !== requestSeq.current || signal.aborted) return;
        setError(
          errorMessage(err, "Falha ao consultar o catálogo de produtos."),
        );
        setList(null);
      } finally {
        if (seq === requestSeq.current && !signal.aborted) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(applied, controller.signal);
    return () => controller.abort();
  }, [applied, load]);

  /* Debounce dos campos de texto → URL (replace; sem spam de histórico).
   * Seleções múltiplas/ordenação/paginação comutam imediatamente. */
  useEffect(() => {
    if (
      draft.code === applied.code &&
      draft.description === applied.description &&
      draft.customer_reference === applied.customer_reference
    ) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      commitListState({ ...applied, ...draft, page: 1 });
    }, DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [draft, applied]);

  /* Opções oficiais de filtro (grupos/tipos distintos do cadastro). */
  const [options, setOptions] = useState<ProductFilterOptions | null>(null);
  const [optionsUnavailable, setOptionsUnavailable] = useState(false);
  const loadOptions = useCallback(async (signal: AbortSignal) => {
    try {
      const data = await fetchProductFilterOptions(signal);
      if (!signal.aborted) setOptions(data);
    } catch {
      if (!signal.aborted) setOptionsUnavailable(true);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void loadOptions(controller.signal);
    return () => controller.abort();
  }, [loadOptions]);

  const groupOptions = useMemo(
    () => (options?.groups ?? []).map((g) => ({ value: g, label: g })),
    [options],
  );
  const typeOptions = useMemo(
    () =>
      (options?.types ?? []).map((t) => ({
        value: t,
        label: `${t} — ${productTypeLabel(t)}`,
      })),
    [options],
  );

  /* Commits de filtros carregam o draft pendente — digitar um texto e
   * clicar num multiselect antes do debounce não perde o que foi
   * digitado. `Limpar` é a exceção deliberada (reseta tudo). */
  const onSortChange = useCallback(
    (columnKey: string) => {
      if (!SORTABLE_COLUMNS.has(columnKey)) return;
      const base = { ...applied, ...draft };
      const next: ProductsListUrlState =
        applied.sort === columnKey
          ? {
              ...base,
              direction: applied.direction === "asc" ? "desc" : "asc",
              page: 1,
            }
          : { ...base, sort: columnKey, direction: "asc", page: 1 };
      commitListState(next);
    },
    [applied, draft],
  );

  const onPageChange = useCallback(
    (nextPage: number) => {
      commitListState({ ...applied, ...draft, page: nextPage });
    },
    [applied, draft],
  );

  const onGroupsChange = useCallback(
    (values: string[]) => {
      commitListState({ ...applied, ...draft, groups: values, page: 1 });
    },
    [applied, draft],
  );

  const onTypesChange = useCallback(
    (values: string[]) => {
      commitListState({ ...applied, ...draft, types: values, page: 1 });
    },
    [applied, draft],
  );

  const clearFilters = useCallback(() => {
    /* Reseta o draft pendente também — sem isso, um debounce em voo
     * recomitaria o texto digitado depois da limpeza da URL. */
    setDraft({ code: "", description: "", customer_reference: "" });
    navigateProducts(PRODUCT_PATHS.list, { replace: true });
  }, []);

  const hasActiveFilters =
    applied.code !== "" ||
    applied.description !== "" ||
    applied.customer_reference !== "" ||
    applied.groups.length > 0 ||
    applied.types.length > 0 ||
    draft.code !== applied.code ||
    draft.description !== applied.description ||
    draft.customer_reference !== applied.customer_reference;

  const openDetail = useCallback((row: ProductRecord) => {
    navigateProducts(PRODUCT_PATHS.detail(row.code));
  }, []);

  const columns = useMemo<DataTableColumn<ProductRecord>[]>(
    () => [
      {
        key: "code",
        header: "Código",
        sortable: true,
        render: (row) => row.code,
      },
      {
        key: "description",
        header: "Descrição",
        sortable: true,
        render: (row) => {
          const display = productDescriptionDisplay(row.description);
          if (display.informative) return display.text;
          if (display.text === "—") return "—";
          return (
            <span
              className="engineering-products__placeholder-value"
              title={PRODUCT_HELP.nonInformativeDescription}
            >
              {display.text}
            </span>
          );
        },
      },
      {
        key: "type",
        header: "Tipo",
        render: (row) => productTypeLabel(row.type),
      },
      {
        key: "group_code",
        header: "Grupo",
        sortable: true,
        render: (row) => row.group_code ?? "—",
      },
      {
        key: "unit",
        header: "UM",
        render: (row) => row.unit ?? "—",
      },
      {
        key: "customer_reference",
        header: "Ref. cliente",
        render: (row) => row.customer_reference ?? "—",
      },
      {
        key: "current_revision",
        header: "Rev.",
        render: (row) => row.current_revision ?? "—",
      },
      {
        key: "status",
        header: "Situação",
        render: (row) => {
          const label = productStatusLabel(row);
          const variant =
            label === "Ativo"
              ? ("success" as const)
              : label === "Bloqueado"
                ? ("error" as const)
                : ("neutral" as const);
          return <EngineeringStatusBadge label={label} variant={variant} />;
        },
      },
    ],
    [],
  );

  return (
    <main className="engineering-products engineering-products--fill">
      <EngineeringPagePath
        back={{
          label: "Início",
          href: "/apps/engineering",
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home");
          },
        }}
        items={[]}
        current={PRODUCT_COPY.breadcrumbBack}
      />

      <EngineeringPageHero
        eyebrow="Portal Engenharia"
        title={PRODUCT_COPY.listTitle}
        description={PRODUCT_COPY.listDescription}
        density="compact"
        actions={
          hasActiveFilters ? (
            <EngineeringActionButton
              variant="ghost"
              onClick={clearFilters}
              title={PRODUCT_HELP.clearFilters}
            >
              Limpar filtros
            </EngineeringActionButton>
          ) : null
        }
      >
        <div
          className="engineering-nc-filters"
          role="group"
          aria-label="Filtros de produtos"
        >
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="Código" hint={PRODUCT_HELP.code} />
            <input
              value={draft.code}
              onChange={(e) =>
                setDraft((d) => ({ ...d, code: e.target.value }))
              }
              placeholder="Código do produto"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Descrição"
              hint={PRODUCT_HELP.description}
            />
            <input
              value={draft.description}
              onChange={(e) =>
                setDraft((d) => ({ ...d, description: e.target.value }))
              }
              placeholder="Descrição do produto"
            />
          </label>
          <EngineeringMultiSelectField
            label="Grupo"
            labelHint={PRODUCT_HELP.groups}
            options={groupOptions}
            selectedValues={applied.groups}
            onChange={onGroupsChange}
            searchable
            disabled={loading}
            emptyLabel={optionsUnavailable ? "Opções indisponíveis" : "Todos"}
          />
          <EngineeringMultiSelectField
            label="Tipo"
            labelHint={PRODUCT_HELP.productType}
            options={typeOptions}
            selectedValues={applied.types}
            onChange={onTypesChange}
            searchable
            disabled={loading}
            emptyLabel="Todos"
          />
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Ref. cliente"
              hint={PRODUCT_HELP.drawingCode}
            />
            <input
              value={draft.customer_reference}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  customer_reference: e.target.value,
                }))
              }
              placeholder="Referência do cliente"
            />
          </label>
        </div>
      </EngineeringPageHero>

      {error ? (
        <EngineeringStateBanner variant="error">
          {`Catálogo de produtos indisponível — ${error}`}
        </EngineeringStateBanner>
      ) : null}

      {loading && !list ? (
        <EngineeringLoadingActivityCard
          title="Carregando produtos"
          description="Consultando a Engineering API com seus filtros."
        />
      ) : null}

      {!loading && !error && list && list.items.length === 0 ? (
        <EngineeringEmptyState message={PRODUCT_COPY.emptyList} />
      ) : null}

      {list && list.items.length > 0 ? (
        <DataTableSection
          title={PRODUCT_COPY.listTitle}
          titleHint={PRODUCT_HELP.search}
          hint={
            applied.sort
              ? `Ordenado por ${applied.sort} (${applied.direction})`
              : undefined
          }
          fillHeight
          columns={columns}
          rows={list.items}
          rowKey={(row) => row.code}
          loading={loading}
          hideSearch
          serverSort={{
            sortKey: applied.sort,
            sortDirection: applied.direction,
            onSortChange,
          }}
          serverPagination={{
            page: applied.page,
            pageSize: PAGE_SIZE,
            total: list.total,
            onPageChange,
          }}
          onRowClick={openDetail}
          columnPreferencesKey="engineering-products-list"
        />
      ) : null}
    </main>
  );
}
