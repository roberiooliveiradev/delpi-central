// src/hooks/useProductsDashboard.ts

import { useEffect, useRef, useState } from "react";
import { DelpiApi } from "../data/delpiApi";
import type { Product } from "../data/delpiApi";

const POLLING_INTERVAL = 30000; // 30 segundos

export const useProductsDashboard = (api: DelpiApi) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isFetchingRef = useRef(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    const fetchData = async () => {
      // Evita chamadas paralelas
      if (isFetchingRef.current) return;

      // Não faz polling se aba estiver oculta
      if (document.hidden) return;

      try {
        isFetchingRef.current = true;

        const res = await api.getProducts(1, 10);

        if (!mountedRef.current) return;

        setProducts(res.data.items ?? []);
      } catch (err) {
        console.error("Erro ao atualizar dashboard:", err);
      } finally {
        if (mountedRef.current) {
          setLoading(false);
        }
        isFetchingRef.current = false;
      }
    };

    // 🔥 Primeira carga imediata
    fetchData();

    // 🔁 Polling
    intervalRef.current = setInterval(fetchData, POLLING_INTERVAL);

    return () => {
      mountedRef.current = false;

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [api]);

  return { products, loading };
};