import { useCallback, useMemo, useState } from "react";

import type { EficienciaFabrilShift } from "../constants/shifts";
import type { EficienciaFabrilEfficiencyBand } from "../constants/efficiencyBands";
import type { EficienciaFabrilFilterParams } from "../types/eficienciaFabril";
import {
  DEFAULT_APPOINTMENTS_SORT,
  type AppointmentsSortColumn,
  type SortDirection,
  toggleSort,
} from "../utils/appointmentsTableSort";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../utils/dates";

const PAGE_SIZE = 50;

export type EficienciaFabrilFilterState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  ops: string[];
  employees: string[];
  workCenters: string[];
  shifts: EficienciaFabrilShift[];
  efficiencyBands: EficienciaFabrilEfficiencyBand[];
  statusOkOnly: boolean;
  sortBy: AppointmentsSortColumn;
  sortDir: SortDirection;
};

function createInitialFilters(fixedBranch: string): EficienciaFabrilFilterState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: fixedBranch,
    ops: [],
    employees: [],
    workCenters: [],
    shifts: [],
    efficiencyBands: [],
    statusOkOnly: true,
    ...DEFAULT_APPOINTMENTS_SORT,
  };
}

function toApiFilters(
  filters: EficienciaFabrilFilterState,
  page: number
): EficienciaFabrilFilterParams {
  return {
    date_start: filters.dateStart,
    date_end: filters.dateEnd,
    branch: filters.branch,
    ops: filters.ops.length > 0 ? filters.ops : undefined,
    employees: filters.employees.length > 0 ? filters.employees : undefined,
    work_centers: filters.workCenters.length > 0 ? filters.workCenters : undefined,
    shifts: filters.shifts.length > 0 ? filters.shifts : undefined,
    efficiency_bands:
      filters.efficiencyBands.length > 0 ? filters.efficiencyBands : undefined,
    status_ok_only: filters.statusOkOnly,
    sort_by: filters.sortBy,
    sort_dir: filters.sortDir,
    page,
    page_size: PAGE_SIZE,
  };
}

export function useEficienciaFabrilFilters(fixedBranch: string) {
  const [filters, setFilters] = useState(() => createInitialFilters(fixedBranch));
  const [page, setPage] = useState(1);

  const apiParams = useMemo(() => toApiFilters(filters, page), [filters, page]);

  const patchFilters = useCallback(
    (patch: Partial<EficienciaFabrilFilterState>, resetPage = true) => {
      setFilters((current) => ({ ...current, ...patch, branch: fixedBranch }));
      if (resetPage) {
        setPage(1);
      }
    },
    [fixedBranch]
  );

  const toggleSortColumn = useCallback((column: AppointmentsSortColumn) => {
    setFilters((current) => {
      const next = toggleSort(current.sortBy, current.sortDir, column);
      return { ...current, ...next, branch: fixedBranch };
    });
    setPage(1);
  }, [fixedBranch]);

  const clearSecondaryFilters = useCallback(() => {
    patchFilters({
      ops: [],
      employees: [],
      workCenters: [],
      shifts: [],
      efficiencyBands: [],
    });
  }, [patchFilters]);

  return {
    dateStart: filters.dateStart,
    dateEnd: filters.dateEnd,
    ops: filters.ops,
    employees: filters.employees,
    workCenters: filters.workCenters,
    shifts: filters.shifts,
    efficiencyBands: filters.efficiencyBands,
    sortBy: filters.sortBy,
    sortDir: filters.sortDir,
    page,
    setDateStart: (value: string) => patchFilters({ dateStart: value }),
    setDateEnd: (value: string) => patchFilters({ dateEnd: value }),
    setOps: (value: string[]) => patchFilters({ ops: value }),
    setEmployees: (value: string[]) => patchFilters({ employees: value }),
    setWorkCenters: (value: string[]) => patchFilters({ workCenters: value }),
    setShifts: (value: EficienciaFabrilShift[]) => patchFilters({ shifts: value }),
    setEfficiencyBands: (value: EficienciaFabrilEfficiencyBand[]) =>
      patchFilters({ efficiencyBands: value }),
    setPage,
    toggleSortColumn,
    clearSecondaryFilters,
    apiParams,
    appliedDateStart: filters.dateStart,
    appliedDateEnd: filters.dateEnd,
  };
}
