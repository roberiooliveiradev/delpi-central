import { useCallback, useMemo, useState } from "react";

import type { EficienciaFabrilFilterParams } from "../types/eficienciaFabril";
import type { EficienciaFabrilShift } from "../constants/shifts";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../utils/dates";

const PAGE_SIZE = 50;

export type EficienciaFabrilFilterState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  op: string;
  employee: string;
  workCenter: string;
  shift: EficienciaFabrilShift | "";
  statusOkOnly: boolean;
};

function createInitialFilters(fixedBranch: string): EficienciaFabrilFilterState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: fixedBranch,
    op: "",
    employee: "",
    workCenter: "",
    shift: "",
    statusOkOnly: true,
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
    shift: filters.shift || undefined,
    status_ok_only: filters.statusOkOnly,
    page,
    page_size: PAGE_SIZE,
  };
}

export function useEficienciaFabrilFilters(fixedBranch: string) {
  const [draft, setDraft] = useState(() => createInitialFilters(fixedBranch));
  const [committed, setCommitted] = useState(() => createInitialFilters(fixedBranch));
  const [page, setPage] = useState(1);

  const apiParams = useMemo(
    () => toApiFilters(committed, page),
    [committed, page]
  );

  const hasPendingChanges = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(committed),
    [committed, draft]
  );

  const applyFilters = useCallback(() => {
    setCommitted({ ...draft, branch: fixedBranch });
    setPage(1);
  }, [draft, fixedBranch]);

  const resetPage = useCallback(() => setPage(1), []);

  const patchDraft = useCallback(
    (patch: Partial<EficienciaFabrilFilterState>) => {
      setDraft((current) => ({ ...current, ...patch, branch: fixedBranch }));
    },
    [fixedBranch]
  );

  return {
    dateStart: draft.dateStart,
    dateEnd: draft.dateEnd,
    op: draft.op,
    employee: draft.employee,
    workCenter: draft.workCenter,
    shift: draft.shift,
    statusOkOnly: draft.statusOkOnly,
    hasPendingChanges,
    page,
    setDateStart: (value: string) => patchDraft({ dateStart: value }),
    setDateEnd: (value: string) => patchDraft({ dateEnd: value }),
    setOp: (value: string) => patchDraft({ op: value }),
    setEmployee: (value: string) => patchDraft({ employee: value }),
    setWorkCenter: (value: string) => patchDraft({ workCenter: value }),
    setShift: (value: EficienciaFabrilShift | "") => patchDraft({ shift: value }),
    setStatusOkOnly: (value: boolean) => patchDraft({ statusOkOnly: value }),
    setPage,
    resetPage,
    applyFilters,
    apiParams,
  };
}
