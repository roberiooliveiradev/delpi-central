import { useCallback, useMemo, useState } from "react";

import type { EficienciaFabrilShift } from "../constants/shifts";
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
import { useDebouncedValue } from "./useDebouncedValue";

const PAGE_SIZE = 50;

export type EficienciaFabrilFilterState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  op: string;
  employee: string;
  workCenter: string;
  shifts: EficienciaFabrilShift[];
  statusOkOnly: boolean;
  sortBy: AppointmentsSortColumn;
  sortDir: SortDirection;
};

function createInitialFilters(fixedBranch: string): EficienciaFabrilFilterState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: fixedBranch,
    op: "",
    employee: "",
    workCenter: "",
    shifts: [],
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
    op: filters.op.trim() || undefined,
    employee: filters.employee.trim() || undefined,
    work_center: filters.workCenter.trim() || undefined,
    shifts: filters.shifts.length > 0 ? filters.shifts : undefined,
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

  const debouncedOp = useDebouncedValue(filters.op, 350);
  const debouncedEmployee = useDebouncedValue(filters.employee, 350);
  const debouncedWorkCenter = useDebouncedValue(filters.workCenter, 350);

  const effectiveFilters = useMemo(
    () => ({
      ...filters,
      op: debouncedOp,
      employee: debouncedEmployee,
      workCenter: debouncedWorkCenter,
    }),
    [debouncedEmployee, debouncedOp, debouncedWorkCenter, filters]
  );

  const apiParams = useMemo(
    () => toApiFilters(effectiveFilters, page),
    [effectiveFilters, page]
  );

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
      op: "",
      employee: "",
      workCenter: "",
      shifts: [],
    });
  }, [patchFilters]);

  return {
    dateStart: filters.dateStart,
    dateEnd: filters.dateEnd,
    op: filters.op,
    employee: filters.employee,
    workCenter: filters.workCenter,
    shifts: filters.shifts,
    sortBy: filters.sortBy,
    sortDir: filters.sortDir,
    page,
    setDateStart: (value: string) => patchFilters({ dateStart: value }),
    setDateEnd: (value: string) => patchFilters({ dateEnd: value }),
    setOp: (value: string) => patchFilters({ op: value }),
    setEmployee: (value: string) => patchFilters({ employee: value }),
    setWorkCenter: (value: string) => patchFilters({ workCenter: value }),
    setShifts: (value: EficienciaFabrilShift[]) => patchFilters({ shifts: value }),
    setPage,
    toggleSortColumn,
    clearSecondaryFilters,
    apiParams,
    appliedDateStart: effectiveFilters.dateStart,
    appliedDateEnd: effectiveFilters.dateEnd,
  };
}
