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

/** Janela do comparativo (atual vs. anterior imediato). */
export type PurchaseEvolutionWindowMonths = 6 | 12;

export type UseCustomerPurchaseEvolutionResult = {
  points: PurchaseEvolutionPoint[];
  loading: boolean;
  error: string | null;
  windowMonths: PurchaseEvolutionWindowMonths;
};

/**
 * Série 2× janela → pontos atuais + anteriores alinhados por índice.
 */
export function useCustomerPurchaseEvolution(
  codigo: string | undefined,
  loja: string | undefined,
  enabled = true,
  windowMonths: PurchaseEvolutionWindowMonths = 12,
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

  const fetchMonths = windowMonths * 2;

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
      { months: fetchMonths, signal: controller.signal },
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
  }, [enabled, identity, fetchMonths]);

  const points = useMemo(() => {
    if (rawPoints.length < 2) {
      return rawPoints.map((point) => ({
        periodo: point.label,
        atual: Number(point.value) || 0,
        anterior: 0,
      }));
    }
    const prior = rawPoints.slice(0, -windowMonths);
    const current = rawPoints.slice(-windowMonths);
    const priorOffset = Math.max(0, prior.length - current.length);
    return current.map((point, index) => ({
      periodo: point.label,
      atual: Number(point.value) || 0,
      anterior: Number(prior[priorOffset + index]?.value) || 0,
    }));
  }, [rawPoints, windowMonths]);

  return { points, loading, error, windowMonths };
}
