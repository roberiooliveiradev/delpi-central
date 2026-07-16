import type { ComunicadoDataResolved } from "./comunicadoTypes";

export type ComunicadoDataPageState = {
  page: number;
  pageSize?: number;
  totalPages?: number;
  hasMore: boolean;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function positiveInt(value: unknown): number | undefined {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) && parsed >= 1 ? Math.floor(parsed) : undefined;
}

export function resolveComunicadoDataPageState(
  resolved: ComunicadoDataResolved | null | undefined,
): ComunicadoDataPageState | null {
  const data = asRecord(resolved?.data);
  const meta = asRecord(resolved?.meta);
  const pagination = asRecord(data?.pagination) ?? asRecord(meta?.pagination) ?? data;
  if (!pagination) return null;
  const page = positiveInt(pagination.page);
  if (!page) return null;
  const pageSize = positiveInt(pagination.page_size ?? pagination.pageSize);
  const totalPages = positiveInt(pagination.total_pages ?? pagination.totalPages);
  const explicitHasNext = pagination.has_next ?? pagination.hasNext;
  const hasMore =
    typeof explicitHasNext === "boolean"
      ? explicitHasNext
      : totalPages != null
        ? page < totalPages
        : false;
  return { page, pageSize, totalPages, hasMore };
}

export function mergeComunicadoDataPages(
  previous: ComunicadoDataResolved,
  nextPage: ComunicadoDataResolved,
): ComunicadoDataResolved {
  const previousRows = previous.table?.rows ?? [];
  const nextRows = nextPage.table?.rows ?? [];
  return {
    ...previous,
    ...nextPage,
    table:
      previous.table || nextPage.table
        ? {
            ...previous.table,
            ...nextPage.table,
            columns: nextPage.table?.columns ?? previous.table?.columns,
            rows: [...previousRows, ...nextRows],
          }
        : undefined,
  };
}
