// src/hooks/usePaginatedResource.ts

import { useEffect, useState, useRef } from "react";

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
  const [pagination, setPagination] = useState<PaginationMeta | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(initialPageSize);
  const [loading, setLoading] = useState(false);

  // 🔥 armazenamos a versão atual do fetcher
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetcherRef.current({ page, pageSize });

      setData(res?.data ?? []);
      setPagination(res?.pagination ?? undefined);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, ...deps]); // 🚫 NÃO incluir fetcher

  const refetch = () => {
    load();
  };

  return {
    data,
    pagination,
    loading,
    page,
    setPage,
    next: () =>
      pagination && page < pagination.total_pages && setPage(page + 1),
    prev: () => page > 1 && setPage(page - 1),
    refetch,
  };
}