import { useEffect, useMemo, useState } from "react";

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
  ProductionAppointmentItem,
  ProductionOrderByOpData,
} from "../types/productionExtras";
import { getLineOpForecast } from "../utils/opAllocation";

const MAX_OPS_FETCH = 5;

export type OpExtrasBundle = {
  byOp: ProductionOrderByOpData | null;
  appointments: ProductionAppointmentItem[];
  forbidden: boolean;
  error: string | null;
};

export type OpenOrdersLineDetailExtras = {
  loading: boolean;
  factoryStatus: ProductFactoryStatusData | null;
  factoryForbidden: boolean;
  factoryError: string | null;
  opsByNumber: Record<string, OpExtrasBundle>;
  productStructure: ProductStructureData | null;
  structureError: string | null;
  /** OV resolvida (campo item ou probe pedido≈OV). */
  proposalNumber: string | null;
  proposalBranch: string | null;
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
};

export function useOpenOrdersLineDetailExtras(
  item: OpenOrdersTotvsItem | null,
  open: boolean,
): OpenOrdersLineDetailExtras {
  const [state, setState] = useState<OpenOrdersLineDetailExtras>(EMPTY);

  const opNumbers = useMemo(() => {
    if (!item) return [] as string[];
    return getLineOpForecast(item)
      .opsUtilizadas.map((op) => op.numero_op?.trim())
      .filter((op): op is string => Boolean(op && op !== "—"))
      .slice(0, MAX_OPS_FETCH);
  }, [item]);

  const opKey = opNumbers.join("|");
  const productCode = item?.produto?.trim() ?? "";
  const branch = item?.filial?.trim() ?? "";
  const explicitProposal = item?.proposal_number?.trim() || null;

  useEffect(() => {
    if (!open || !item) {
      setState(EMPTY);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    async function load() {
      setState((prev) => ({ ...prev, loading: true }));

      const [factoryResult, structureResult, proposalResult, ...opResults] =
        await Promise.all([
          productCode
            ? fetchOptional(() => fetchProductFactoryStatus(productCode, controller.signal))
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
                data: { proposal_number: explicitProposal },
                forbidden: false,
                missing: false,
                error: null as string | null,
              })
            : Promise.resolve({
                data: null as { proposal_number: string } | null,
                forbidden: false,
                missing: true,
                error: null as string | null,
              }),
          ...opNumbers.map(async (opNumber) => {
            const [byOpResult, apptResult] = await Promise.all([
              fetchOptional(() =>
                fetchProductionOrderByOp(
                  opNumber,
                  { branch: branch || undefined },
                  controller.signal,
                ),
              ),
              fetchOptional(() =>
                fetchAppointmentsByOp(
                  { op: opNumber, branch: branch || undefined },
                  controller.signal,
                ),
              ),
            ]);
            return {
              opNumber,
              byOp: byOpResult.data,
              appointments: apptResult.data?.items ?? [],
              forbidden: byOpResult.forbidden || apptResult.forbidden,
              error: byOpResult.error || apptResult.error,
            };
          }),
        ]);

      if (cancelled || controller.signal.aborted) return;

      const opsByNumber: Record<string, OpExtrasBundle> = {};
      for (const row of opResults) {
        opsByNumber[row.opNumber] = {
          byOp: row.byOp,
          appointments: row.appointments,
          forbidden: row.forbidden,
          error: row.error,
        };
      }

      const resolvedProposal =
        explicitProposal ||
        (proposalResult.data && "proposal_number" in proposalResult.data
          ? proposalResult.data.proposal_number
          : null);

      setState({
        loading: false,
        factoryStatus: factoryResult.data,
        factoryForbidden: factoryResult.forbidden,
        factoryError: factoryResult.error,
        opsByNumber,
        productStructure: structureResult.data,
        structureError: structureResult.error,
        proposalNumber: resolvedProposal,
        proposalBranch: resolvedProposal ? branch || null : null,
      });
    }

    void load();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [open, item, opKey, productCode, branch, explicitProposal, opNumbers]);

  return state;
}
