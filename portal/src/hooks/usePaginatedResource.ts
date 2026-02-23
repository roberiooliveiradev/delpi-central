// src/hooks/usePaginatedResource.ts

import { useEffect, useState } from "react";

export type PaginationMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export function usePaginatedResource<T>(
  fetcher: (params: { page: number; pageSize: number }) => Promise<{
    data: T[];
    pagination: PaginationMeta;
  }>,
  initialPageSize = 10,
  deps: any[] = []
) {
  const [data, setData] = useState<T[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(initialPageSize);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const res = await fetcher({ page, pageSize });
        if (!cancelled) {
          setData(res?.data ?? []);
          setPagination(res?.pagination ?? null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, ...deps]); // 🔥 fetcher removido da dependência

  return {
    data,
    pagination,
    loading,
    page,
    setPage,
    next: () =>
      pagination && page < pagination.total_pages && setPage(page + 1),
    prev: () => page > 1 && setPage(page - 1),
  };
}