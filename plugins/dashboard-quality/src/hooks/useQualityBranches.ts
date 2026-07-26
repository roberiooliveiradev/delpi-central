import { listQualityBranches } from "../api/qualityApi";
import { useQualityResource } from "./useQualityResource";

type UseQualityBranchesParams = {
  start_date?: string;
  end_date?: string;
};

export function useQualityBranches(params: UseQualityBranchesParams = {}) {
  const { data, loading, error, reload } = useQualityResource(
    (signal) =>
      listQualityBranches(
        {
          start_date: params.start_date,
          end_date: params.end_date,
        },
        signal
      ),
    [params.start_date, params.end_date],
    { cacheKey: `branches:${params.start_date ?? ""}:${params.end_date ?? ""}` }
  );

  return {
    branches: data?.branches ?? [],
    loading,
    error,
    reload,
  };
}
