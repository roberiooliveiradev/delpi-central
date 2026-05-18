import { listQualityBranches } from "../api/qualityApi";
import { useQualityResource } from "./useQualityResource";

type UseQualityBranchesParams = {
  date_start?: string;
  date_end?: string;
};

export function useQualityBranches(params: UseQualityBranchesParams = {}) {
  const { data, loading, error, reload } = useQualityResource(
    (signal) =>
      listQualityBranches(
        {
          date_start: params.date_start,
          date_end: params.date_end,
        },
        signal
      ),
    [params.date_start, params.date_end],
    { cacheKey: `branches:${params.date_start ?? ""}:${params.date_end ?? ""}` }
  );

  return {
    branches: data?.branches ?? [],
    loading,
    error,
    reload,
  };
}
