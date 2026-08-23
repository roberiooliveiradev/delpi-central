import { useCallback, useEffect, useState } from "react";

import { fetchMaterials } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { MaterialsIssueId, MaterialsPayload, PpcBranch } from "../types";

export type MaterialsFilters = {
  view: MaterialsIssueId;
  search: string;
  page: number;
  pageSize: number;
  sort: string;
  direction: "asc" | "desc";
};

export const MATERIALS_DEFAULT_FILTERS: MaterialsFilters = {
  view: "excess",
  search: "",
  page: 1,
  pageSize: 50,
  sort: "required_date",
  direction: "asc",
};

export function useMaterials(branch: PpcBranch, filters: MaterialsFilters) {
  const [data, setData] = useState<MaterialsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchMaterials({
      branch,
      view: filters.view,
      search: filters.search,
      sort: filters.sort,
      direction: filters.direction,
      page: filters.page,
      pageSize: filters.pageSize,
      refresh: reloadToken > 0,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.materials.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    branch,
    filters.direction,
    filters.page,
    filters.pageSize,
    filters.search,
    filters.sort,
    filters.view,
    reloadToken,
  ]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
  };
}
