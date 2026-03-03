// src/hooks/useProductsDashboard.ts

import { useEffect, useState } from "react";
import type { DelpiApi, Product } from "../data/delpiApi";

export function useProductsDashboard(api: DelpiApi) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [filters, setFilters] = useState({
    code: "",
    description: "",
  });

  useEffect(() => {
    let cancelled = false;

    async function fetchProducts() {
      setLoading(true);

      try {
        const hasFilter =
          filters.code || filters.description;

        const res = hasFilter
          ? await api.searchProducts({
              code: filters.code,
              description: filters.description,
              page,
              pageSize,
            })
          : await api.getProducts(page, pageSize);

        const paginated = res.data;

        if (cancelled) return;

        setProducts(paginated.items);
        setTotal(paginated.total);
        setTotalPages(paginated.total_pages);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchProducts();

    return () => {
      cancelled = true;
    };
  }, [
    api,
    page,
    pageSize,
    filters.code,
    filters.description,
  ]);

  return {
    products,
    loading,
    page,
    pageSize,
    total,
    totalPages,
    setPage,
    setPageSize,
    filters,
    setFilters,
  };
}