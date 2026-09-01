import { useEffect, useState } from "react";

import {
  DEFAULT_PANEL_FILTERS,
  readPanelFilters,
  replacePanelFilters,
  type PanelFilters,
} from "../utils/panelFilterUrl";

export function usePanelFilters(search: string, defaultBranch: string) {
  const [filters, setFiltersState] = useState<PanelFilters>(() => {
    const parsed = readPanelFilters(search);
    return {
      ...parsed,
      branch: parsed.branch || defaultBranch || DEFAULT_PANEL_FILTERS.branch,
    };
  });

  useEffect(() => {
    const parsed = readPanelFilters(search);
    setFiltersState((current) => ({
      ...current,
      ...parsed,
      branch: parsed.branch || defaultBranch || current.branch,
    }));
  }, [search, defaultBranch]);

  useEffect(() => {
    replacePanelFilters(filters);
  }, [filters]);

  const setFilters = (patch: Partial<PanelFilters>) => {
    setFiltersState((current) => {
      const resetsPage =
        patch.page === undefined &&
        (patch.search !== undefined ||
          patch.status !== undefined ||
          patch.anchorType !== undefined ||
          patch.role !== undefined ||
          patch.branch !== undefined ||
          patch.view !== undefined);
      return {
        ...current,
        ...patch,
        page: patch.page ?? (resetsPage ? 1 : current.page),
      };
    });
  };

  return { filters, setFilters };
}
