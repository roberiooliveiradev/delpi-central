import { useEffect, useState } from "react";

import {
  DEFAULT_PANEL_FILTERS,
  readPanelFilters,
  replacePanelFilters,
  type PanelFilters,
} from "../utils/panelFilterUrl";
import { PRODUCTION_PULSE_BASE_PATH } from "../constants/routes";

function parseSearchParams(search: string): URLSearchParams {
  const raw = search.startsWith("?") ? search.slice(1) : search;
  return new URLSearchParams(raw);
}

function isPanelPath(pathname: string): boolean {
  const normalized = pathname.replace(/\/+$/, "") || PRODUCTION_PULSE_BASE_PATH;
  return normalized === PRODUCTION_PULSE_BASE_PATH;
}

export function usePanelFilters(search: string, defaultBranch: string) {
  const [filters, setFiltersState] = useState<PanelFilters>(() => {
    const parsed = readPanelFilters(search);
    return {
      ...parsed,
      branch: parsed.branch || defaultBranch || DEFAULT_PANEL_FILTERS.branch,
    };
  });

  useEffect(() => {
    const query = parseSearchParams(search);
    const parsed = readPanelFilters(search);
    setFiltersState((current) => ({
      ...current,
      branch: parsed.branch || defaultBranch || current.branch,
      anchorType: query.has("anchorType") ? parsed.anchorType : current.anchorType,
      role: query.has("role") ? parsed.role : current.role,
      status: query.has("status") ? parsed.status : current.status,
      search: query.has("search") ? parsed.search : current.search,
      view: query.has("view") ? parsed.view : current.view,
      groupBy: query.has("groupBy") ? parsed.groupBy : current.groupBy,
      page: query.has("page") ? parsed.page : current.page,
    }));
  }, [search, defaultBranch]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!isPanelPath(window.location.pathname)) return;
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
