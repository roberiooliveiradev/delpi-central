import {
  fetchDepartmentIndicators,
  fetchGlobalIndicators,
} from "../api/financialApi";
import { copy } from "../content/copy";
import type { DepartmentIndicators, FinancialBranch, GlobalIndicators } from "../types";
import { useAsyncResource } from "./useAsyncResource";

export type IndicatorsBundle = {
  department: DepartmentIndicators;
  global: GlobalIndicators;
};

export function useIndicators(branch: FinancialBranch) {
  return useAsyncResource<IndicatorsBundle>(
    async (signal) => {
      const [department, global] = await Promise.all([
        fetchDepartmentIndicators({ branch, signal }),
        fetchGlobalIndicators({ branch, signal }),
      ]);
      return { department, global };
    },
    [branch],
    copy.indicators.loadError,
  );
}
