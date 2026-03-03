// src/hooks/useProductsDashboard.ts

import { useEffect, useState } from "react";
import { DelpiApi } from "../data/delpiApi";
import type { Product } from "../data/delpiApi";

export const useProductsDashboard = (
  api: DelpiApi
) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    api
      .getProducts(1, 10)
      .then((res) => {
        if (!mounted) return;
        setProducts(res.data.items ?? []);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [api]);

  return { products, loading };
};