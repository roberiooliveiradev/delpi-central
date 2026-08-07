import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  fetchAppointmentsByOp,
  fetchOptional,
  fetchProductFactoryStatus,
  fetchProductStructure,
  fetchProductionOrderByOp,
} from "../api/productionExtrasApi";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import type {
  ProductFactoryStatusData,
  ProductStructureData,
  ProductionAppointmentByOpRow,
  ProductionOrderByOpData,
} from "../types/productionExtras";
import { getLineOpForecast } from "../utils/opAllocation";
import { resolveProposalForOpenOrderLine } from "../utils/resolveProposalForOpenOrder";

/** Prefetch inicial; demais OPs sob demanda ao selecionar. */
export const MAX_OPS_PREFETCH = 12;
const OPS_CONCURRENCY = 3;

export type OpExtrasBundle = {
  byOp: ProductionOrderByOpData | null;
  appointments: ProductionAppointmentByOpRow[];
  forbidden: boolean;
  error: string | null;
  loading?: boolean;
};

export type OpenOrdersLineDetailExtras = {
  loading: boolean;
  factoryStatus: ProductFactoryStatusData | null;
  factoryForbidden: boolean;
  factoryError: string | null;
  opsByNumber: Record<string, OpExtrasBundle>;
  productStructure: ProductStructureData | null;
  structureError: string | null;
  /** OV resolvida (campo item ou busca /commercial/proposals). */
  proposalNumber: string | null;
  proposalBranch: string | null;
  opsPrefetchTruncated: number;
  ensureOpLoaded: (opNumber: string) => void;
};

const EMPTY: OpenOrdersLineDetailExtras = {
  loading: false,
  factoryStatus: null,
  factoryForbidden: false,
  factoryError: null,
  opsByNumber: {},
  productStructure: null,
  structureError: null,
  proposalNumber: null,
  proposalBranch: null,
  opsPrefetchTruncated: 0,
  ensureOpLoaded: () => undefined,
};

async function mapPool<T, R>(
  items: T[],
  concurrency: number,
  mapper: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let next = 0;
  async function worker() {
    while (next < items.length) {
      const index = next;
      next += 1;
      results[index] = await mapper(items[index]);
    }
  }
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, () =>
    worker(),
  );
  await Promise.all(workers);
  return results;
}

async function loadOpBundle(
  opNumber: string,
  branch: string,
  signal: AbortSignal,
): Promise<OpExtrasBundle & { opNumber: string }> {
  const [byOpResult, apptResult] = await Promise.all([
    fetchOptional(() =>
      fetchProductionOrderByOp(opNumber, { branch: branch || undefined }, signal),
    ),
    fetchOptional(() =>
      fetchAppointmentsByOp({ op: opNumber, branch: branch || undefined }, signal),
    ),
  ]);
  return {
    opNumber,
    byOp: byOpResult.data,
    appointments: apptResult.data?.items ?? [],
    forbidden: byOpResult.forbidden || apptResult.forbidden,
    error: byOpResult.error || apptResult.error,
    loading: false,
  };
}

export function useOpenOrdersLineDetailExtras(
  item: OpenOrdersTotvsItem | null,
  open: boolean,
  selectedOp?: string | null,
): OpenOrdersLineDetailExtras {
  const [state, setState] = useState<Omit<OpenOrdersLineDetailExtras, "ensureOpLoaded">>(
    EMPTY,
  );
  const abortRef = useRef<AbortController | null>(null);
  const loadedOpsRef = useRef<Set<string>>(new Set());

  const allOpNumbers = useMemo(() => {
    if (!item) return [] as string[];
    return getLineOpForecast(item)
      .opsUtilizadas.map((op) => op.numero_op?.trim())
      .filter((op): op is string => Boolean(op && op !== "—"));
  }, [item]);

  const prefetchOps = useMemo(
    () => allOpNumbers.slice(0, MAX_OPS_PREFETCH),
    [allOpNumbers],
  );
  const truncatedCount = Math.max(0, allOpNumbers.length - prefetchOps.length);
  const opKey = prefetchOps.join("|");
  const productCode = item?.produto?.trim() ?? "";
  const branch = item?.filial?.trim() ?? "";
  const explicitProposal = item?.proposal_number?.trim() || null;

  const ensureOpLoaded = useCallback(
    (opNumber: string) => {
      const op = opNumber.trim();
      if (!op || !open || !item) return;
      if (loadedOpsRef.current.has(op)) return;
      const controller = abortRef.current;
      if (!controller || controller.signal.aborted) return;

      loadedOpsRef.current.add(op);
      setState((prev) => ({
        ...prev,
        opsByNumber: {
          ...prev.opsByNumber,
          [op]: {
            byOp: null,
            appointments: [],
            forbidden: false,
            error: null,
            loading: true,
          },
        },
      }));

      void loadOpBundle(op, branch, controller.signal).then((row) => {
        if (controller.signal.aborted) return;
        setState((prev) => ({
          ...prev,
          opsByNumber: {
            ...prev.opsByNumber,
            [row.opNumber]: {
              byOp: row.byOp,
              appointments: row.appointments,
              forbidden: row.forbidden,
              error: row.error,
              loading: false,
            },
          },
        }));
      });
    },
    [open, item, branch],
  );

  useEffect(() => {
    if (!open || !item) {
      setState(EMPTY);
      loadedOpsRef.current = new Set();
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    let cancelled = false;
    loadedOpsRef.current = new Set(prefetchOps);

    async function load() {
      setState((prev) => ({
        ...prev,
        loading: true,
        opsPrefetchTruncated: truncatedCount,
      }));

      const [factoryResult, structureResult, proposalResolved, opRows] =
        await Promise.all([
          productCode
            ? fetchOptional(() =>
                fetchProductFactoryStatus(
                  productCode,
                  { branch: branch || undefined },
                  controller.signal,
                ),
              )
            : Promise.resolve({
                data: null as ProductFactoryStatusData | null,
                forbidden: false,
                missing: false,
                error: null as string | null,
              }),
          productCode
            ? fetchOptional(() => fetchProductStructure(productCode, controller.signal))
            : Promise.resolve({
                data: null as ProductStructureData | null,
                forbidden: false,
                missing: false,
                error: null as string | null,
              }),
          explicitProposal
            ? Promise.resolve({
                proposalNumber: explicitProposal,
                branch: branch || null,
              })
            : resolveProposalForOpenOrderLine(item!, controller.signal),
          mapPool(prefetchOps, OPS_CONCURRENCY, (opNumber) =>
            loadOpBundle(opNumber, branch, controller.signal),
          ),
        ]);

      if (cancelled || controller.signal.aborted) return;

      const opsByNumber: Record<string, OpExtrasBundle> = {};
      for (const row of opRows) {
        loadedOpsRef.current.add(row.opNumber);
        opsByNumber[row.opNumber] = {
          byOp: row.byOp,
          appointments: row.appointments,
          forbidden: row.forbidden,
          error: row.error,
          loading: false,
        };
      }

      setState({
        loading: false,
        factoryStatus: factoryResult.data,
        factoryForbidden: factoryResult.forbidden,
        factoryError: factoryResult.error,
        opsByNumber,
        productStructure: structureResult.data,
        structureError: structureResult.error,
        proposalNumber: proposalResolved?.proposalNumber ?? null,
        proposalBranch: proposalResolved?.branch ?? null,
        opsPrefetchTruncated: truncatedCount,
      });
    }

    void load();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [open, item, opKey, productCode, branch, explicitProposal, prefetchOps, truncatedCount]);

  useEffect(() => {
    if (!open || !selectedOp?.trim()) return;
    ensureOpLoaded(selectedOp);
  }, [open, selectedOp, ensureOpLoaded]);

  return {
    ...state,
    ensureOpLoaded,
  };
}
