import { useCallback, useMemo, useState } from "react";

import type { AuditListItem } from "../api/audit5sApi";
import type { AuditDashboardFilterParams, ChartGranularity } from "../types/auditDashboard";
import { computeAuditDateRange } from "../utils/auditDashboardDefaults";

const PAGE_SIZE = 20;

export type AuditDashboardFilterState = {
  dateStart: string;
  dateEnd: string;
  areaId: string;
  shift: string;
  auditStatus: string;
  sensoOrder: string;
  granularity: ChartGranularity;
};

function createInitialFilters(audits: AuditListItem[]): AuditDashboardFilterState {
  const { dateStart, dateEnd } = computeAuditDateRange(audits);
  return {
    dateStart,
    dateEnd,
    areaId: "",
    shift: "",
    auditStatus: "",
    sensoOrder: "",
    granularity: "month",
  };
}

function toApiParams(
  branch: string,
  filters: AuditDashboardFilterState,
  page: number,
): AuditDashboardFilterParams {
  const sensoOrder = filters.sensoOrder ? Number(filters.sensoOrder) : undefined;
  return {
    branch,
    start_date: filters.dateStart,
    end_date: filters.dateEnd,
    area_id: filters.areaId || undefined,
    shift: filters.shift || undefined,
    audit_status: filters.auditStatus || undefined,
    senso_order: sensoOrder && sensoOrder >= 1 && sensoOrder <= 5 ? sensoOrder : undefined,
    granularity: filters.granularity,
    page,
    page_size: PAGE_SIZE,
  };
}

export function useAudit5sDashboardFilters(branch: string, audits: AuditListItem[]) {
  const initialFilters = useMemo(() => createInitialFilters(audits), [audits]);
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);

  const apiParams = useMemo(
    () => toApiParams(branch, filters, page),
    [branch, filters, page],
  );

  const patchFilters = useCallback((patch: Partial<AuditDashboardFilterState>) => {
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
    setShift: (value: string) => patchFilters({ shift: value }),
    setAuditStatus: (value: string) => patchFilters({ auditStatus: value }),
    setSensoOrder: (value: string) => patchFilters({ sensoOrder: value }),
    setGranularity: (value: ChartGranularity) => patchFilters({ granularity: value }),
  };
}
