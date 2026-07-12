import { useCallback, useMemo, useState } from "react";

import type { AuditListItem } from "../api/audit5sApi";
import type { NcBoardFilterParams } from "../types/ncManagement";
import { computeAuditDateRange } from "../utils/auditDashboardDefaults";

const PAGE_SIZE = 20;

export type NcBoardFilterState = {
  dateStart: string;
  dateEnd: string;
  areaId: string;
  status: string;
  responsible: string;
  overdueOnly: boolean;
};

function createInitialFilters(audits: AuditListItem[]): NcBoardFilterState {
  const { dateStart, dateEnd } = computeAuditDateRange(audits);
  return {
    dateStart,
    dateEnd,
    areaId: "",
    status: "",
    responsible: "",
    overdueOnly: false,
  };
}

function toApiParams(
  branch: string,
  filters: NcBoardFilterState,
  page: number,
): NcBoardFilterParams {
  const responsible = filters.responsible.trim();
  return {
    branch,
    date_start: filters.dateStart,
    date_end: filters.dateEnd,
    area_id: filters.areaId || undefined,
    status: filters.status || undefined,
    responsible: responsible || undefined,
    overdue_only: filters.overdueOnly || undefined,
    sort: "due_date_asc",
    page,
    page_size: PAGE_SIZE,
  };
}

export function useAudit5sNcBoardFilters(branch: string, audits: AuditListItem[]) {
  const initialFilters = useMemo(() => createInitialFilters(audits), [audits]);
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);

  const apiParams = useMemo(
    () => toApiParams(branch, filters, page),
    [branch, filters, page],
  );

  const patchFilters = useCallback((patch: Partial<NcBoardFilterState>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  return {
    filters,
    apiParams,
    page,
    setPage,
    setDateStart: (value: string) => patchFilters({ dateStart: value }),
    setDateEnd: (value: string) => patchFilters({ dateEnd: value }),
    setAreaId: (value: string) => patchFilters({ areaId: value }),
    setStatus: (value: string) => patchFilters({ status: value }),
    setResponsible: (value: string) => patchFilters({ responsible: value }),
    setOverdueOnly: (value: boolean) => patchFilters({ overdueOnly: value }),
  };
}
