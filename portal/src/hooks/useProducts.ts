// src/hooks/useProducts.ts

import { useEffect, useState } from "react";
import { useDelpiApi } from "./useDelpiApi";
import type { Product } from "../data/delpiApi";

export const useProducts = (page: number, pageSize: number) => {
  const api = useDelpiApi();

  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!api) return;

    let mounted = true;

    setLoading(true);
    setError(null);

    api
      .getProducts(page, pageSize)
      .then((response) => {
        if (!mounted) return;

        const result = response.data;

        setItems(result.items ?? []);
        setTotal(result.total ?? 0);
        setTotalPages(result.total_pages ?? 1);
      })
      .catch((err) => {
        if (mounted) {
          setError(err?.message ?? "Erro ao carregar produtos");
          setItems([]); // 🔥 evita undefined
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [api, page, pageSize]);

  return {
    items,
    total,
    totalPages,
    loading,
    error,
  };
};