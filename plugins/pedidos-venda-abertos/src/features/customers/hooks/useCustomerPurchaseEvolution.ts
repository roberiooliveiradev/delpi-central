import { useEffect, useMemo, useState } from "react";

import {
  fetchCustomerBillingSeries,
  type CustomerBillingSeriesPoint,
} from "../../../api/customerBillingSeriesApi";

export type PurchaseEvolutionPoint = {
  periodo: string;
  atual: number;
  anterior: number;
};

export type UseCustomerPurchaseEvolutionResult = {
  points: PurchaseEvolutionPoint[];
  loading: boolean;
  error: string | null;
};

/**
 * Série 24 meses → 12 atuais + 12 anteriores alinhados por índice (mockup evolução).
 */
export function useCustomerPurchaseEvolution(
  codigo: string | undefined,
  loja: string | undefined,
  enabled = true,
): UseCustomerPurchaseEvolutionResult {
  const [rawPoints, setRawPoints] = useState<CustomerBillingSeriesPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identity = useMemo(() => {
    const code = (codigo ?? "").trim();
    const store = (loja ?? "").trim();
    if (!code || !store) return null;
    return { code, store };
  }, [codigo, loja]);

  useEffect(() => {
    if (!enabled || !identity) {
      setRawPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    void fetchCustomerBillingSeries(
      [{ customer_code: identity.code, customer_store: identity.store }],
      { months: 24, signal: controller.signal },
    )
      .then((payload) => {
        if (cancelled) return;
        setRawPoints(payload.points ?? []);
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar a evolução.";
        setError(message);
        setRawPoints([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [enabled, identity]);

  const points = useMemo(() => {
    if (rawPoints.length < 2) {
      return rawPoints.map((point) => ({
        periodo: point.label,
        atual: Number(point.value) || 0,
        anterior: 0,
      }));
    }
    const prior = rawPoints.slice(0, -12);
    const current = rawPoints.slice(-12);
    const priorOffset = Math.max(0, prior.length - current.length);
    return current.map((point, index) => ({
      periodo: point.label,
      atual: Number(point.value) || 0,
      anterior: Number(prior[priorOffset + index]?.value) || 0,
    }));
  }, [rawPoints]);

  return { points, loading, error };
}
