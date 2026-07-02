import { useCallback, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { useClientPagination } from "../../hooks/useClientPagination";
import { DataTable, type DataTableColumn, type SortDirection } from "./DataTable";
import { Pagination } from "./Pagination";

const DEFAULT_PAGE_SIZE = 20;

type SortState = { key: string; dir: SortDirection };

function compareValues(
  a: string | number | null | undefined,
  b: string | number | null | undefined,
): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), "pt-BR", { numeric: true, sensitivity: "base" });
}

function buildSearchText<T>(row: T, columns: DataTableColumn<T>[]): string {
  return columns
    .map((column) => {
      const value = column.render(row);
      if (value == null || value === false) return "";
      if (typeof value === "string" || typeof value === "number") {
        return String(value);
      }
      return "";
    })
    .join(" ")
    .toLowerCase();
}

export type DataTableSectionProps<T> = {
  title: string;
  hint?: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  pageSize?: number;
  searchPlaceholder?: string;
  getSearchText?: (row: T) => string;
  initialSort?: SortState | null;
};

export function DataTableSection<T>({
  title,
  hint,
  columns,
  rows,
  rowKey,
  loading = false,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = DEFAULT_PAGE_SIZE,
  searchPlaceholder = "Buscar na tabela…",
  getSearchText,
  initialSort = null,
}: DataTableSectionProps<T>) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortState | null>(initialSort);

  const handleSort = useCallback((key: string) => {
    setSort((current) => {
      if (!current || current.key !== key) return { key, dir: "asc" };
      if (current.dir === "asc") return { key, dir: "desc" };
      return null;
    });
  }, []);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return rows;

    return rows.filter((row) => {
      const haystack = (getSearchText ?? ((item) => buildSearchText(item, columns)))(
        row,
      ).toLowerCase();
      return haystack.includes(query);
    });
  }, [rows, search, columns, getSearchText]);

  const sortedRows = useMemo(() => {
    if (!sort) return filteredRows;
    const column = columns.find((item) => item.key === sort.key);
    if (!column?.sortAccessor) return filteredRows;
    const accessor = column.sortAccessor;
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...filteredRows].sort((a, b) => factor * compareValues(accessor(a), accessor(b)));
  }, [filteredRows, sort, columns]);

  const { page, setPage, slice, total } = useClientPagination(sortedRows, pageSize);

  return (
    <section className="kz-card kz-table-section" aria-busy={loading}>
      <div className="kz-table-section__header">
        <h2 className="kz-section-title">{title}</h2>
        <div className="kz-table-section__meta-group">
          {hint ? <span className="kz-table-section__meta">{hint}</span> : null}
          <span className="kz-table-section__meta">{total} registro(s)</span>
        </div>
      </div>

      <div className="kz-table-toolbar">
        <div className="kz-table-search" role="search">
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            className="kz-table-search__input"
            value={search}
            placeholder={searchPlaceholder}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Filtrar registros da tabela"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={slice}
        rowKey={rowKey}
        loading={loading}
        emptyMessage={emptyMessage}
        sortKey={sort?.key ?? null}
        sortDir={sort?.dir ?? "asc"}
        onSort={handleSort}
      />

      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={setPage}
      />
    </section>
  );
}
