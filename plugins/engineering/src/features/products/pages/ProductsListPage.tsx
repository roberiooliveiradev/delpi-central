import { useCallback, useEffect, useMemo, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFieldLabel,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/DataTable";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import { searchProducts } from "../api/productApi";
import {
  PRODUCT_COPY,
  PRODUCT_HELP,
  productStatusLabel,
  productTypeLabel,
} from "../productCopy";
import { PRODUCT_PATHS, navigateProducts } from "../productRoutes";
import type { ProductRecord } from "../types";

type Filters = {
  code: string;
  description: string;
  group_code: string;
  product_type: string;
  customer_reference: string;
};

const EMPTY_FILTERS: Filters = {
  code: "",
  description: "",
  group_code: "",
  product_type: "",
  customer_reference: "",
};

const PAGE_SIZE = 50;
const SORTABLE_COLUMNS = new Set(["code", "description", "group_code"]);

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

export function ProductsListPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [list, setList] = useState<{
    items: ProductRecord[];
    total: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await searchProducts({
        code: applied.code || undefined,
        description: applied.description || undefined,
        group_code: applied.group_code || undefined,
        product_type: applied.product_type || undefined,
        customer_reference: applied.customer_reference || undefined,
        sort: sortBy ?? undefined,
        direction: sortBy ? sortDir : undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setList({ items: result.items, total: result.total });
    } catch (err) {
      setError(errorMessage(err, "Falha ao consultar o catálogo de produtos."));
      setList(null);
    } finally {
      setLoading(false);
    }
  }, [applied, sortBy, sortDir, page]);

  useEffect(() => {
    const controller = new AbortController();
    void load();
    return () => controller.abort();
  }, [load]);

  const applyFilters = useCallback(() => {
    setPage(1);
    setApplied(filters);
  }, [filters]);

  const clearFilters = useCallback(() => {
    setFilters(EMPTY_FILTERS);
    setPage(1);
    setApplied(EMPTY_FILTERS);
  }, []);

  const onSortChange = useCallback(
    (columnKey: string) => {
      if (!SORTABLE_COLUMNS.has(columnKey)) return;
      setPage(1);
      if (sortBy === columnKey) {
        setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
      } else {
        setSortBy(columnKey);
        setSortDir("asc");
      }
    },
    [sortBy],
  );

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
        render: (row) => row.description ?? "—",
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
    <main className="engineering-products">
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
      >
        <div
          className="engineering-nc-filters"
          role="group"
          aria-label="Filtros de produtos"
        >
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="Código" hint={PRODUCT_HELP.code} />
            <input
              value={filters.code}
              onChange={(e) =>
                setFilters((f) => ({ ...f, code: e.target.value }))
              }
              disabled={loading}
              placeholder="Código do produto"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Descrição"
              hint={PRODUCT_HELP.description}
            />
            <input
              value={filters.description}
              onChange={(e) =>
                setFilters((f) => ({ ...f, description: e.target.value }))
              }
              disabled={loading}
              placeholder="Descrição do produto"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="Grupo" hint={PRODUCT_HELP.group} />
            <input
              value={filters.group_code}
              onChange={(e) =>
                setFilters((f) => ({ ...f, group_code: e.target.value }))
              }
              disabled={loading}
              placeholder="Código do grupo"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Tipo"
              hint={PRODUCT_HELP.productType}
            />
            <input
              value={filters.product_type}
              onChange={(e) =>
                setFilters((f) => ({ ...f, product_type: e.target.value }))
              }
              disabled={loading}
              placeholder="MP,PI,PA"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Ref. cliente"
              hint={PRODUCT_HELP.drawingCode}
            />
            <input
              value={filters.customer_reference}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  customer_reference: e.target.value,
                }))
              }
              disabled={loading}
              placeholder="Referência do cliente"
            />
          </label>
        </div>
        <div className="engineering-nc-actions">
          <EngineeringActionButton
            variant="primary"
            onClick={applyFilters}
            disabled={loading}
          >
            Filtrar
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="ghost"
            onClick={clearFilters}
            disabled={loading}
          >
            Limpar
          </EngineeringActionButton>
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
          hint={`${list.total} registro(s)${
            sortBy ? ` — ordenado por ${sortBy} (${sortDir})` : ""
          }`}
          columns={columns}
          rows={list.items}
          rowKey={(row) => row.code}
          loading={loading}
          hideSearch
          serverSort={{
            sortKey: sortBy,
            sortDirection: sortDir,
            onSortChange,
          }}
          serverPagination={{
            page,
            pageSize: PAGE_SIZE,
            total: list.total,
            onPageChange: setPage,
          }}
          onRowClick={openDetail}
          columnPreferencesKey="engineering-products-list"
        />
      ) : null}
    </main>
  );
}
