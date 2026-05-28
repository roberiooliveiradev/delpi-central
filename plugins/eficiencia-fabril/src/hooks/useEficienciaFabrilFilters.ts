import { useCallback, useMemo, useState } from "react";

import type { EficienciaFabrilListFilterParams } from "../api/fetchAllEficienciaFabrilItems";
import type { EficienciaFabrilFilterParams } from "../types/eficienciaFabril";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../utils/dates";

const BRANCHES = ["01", "02"] as const;
const PAGE_SIZE = 50;

export type EficienciaFabrilFilterState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  op: string;
  employee: string;
  workCenter: string;
  statusOkOnly: boolean;
};

function createInitialFilters(): EficienciaFabrilFilterState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: "",
    op: "",
    employee: "",
    workCenter: "",
    statusOkOnly: true,
  };
}

function toListFilterParams(
  filters: EficienciaFabrilFilterState
): EficienciaFabrilListFilterParams {
  return {
    date_start: filters.dateStart,
    date_end: filters.dateEnd,
    branch: filters.branch || undefined,
    op: filters.op.trim() || undefined,
    employee: filters.employee.trim() || undefined,
    work_center: filters.workCenter.trim() || undefined,
    status_ok_only: filters.statusOkOnly,
  };
}

function toApiFilters(
  filters: EficienciaFabrilFilterState,
  page: number
): EficienciaFabrilFilterParams {
  return {
    ...toListFilterParams(filters),
    page,
    page_size: PAGE_SIZE,
  };
}

export function useEficienciaFabrilFilters() {
  const [draft, setDraft] = useState(createInitialFilters);
  const [committed, setCommitted] = useState(createInitialFilters);
  const [page, setPage] = useState(1);

  const apiParams = useMemo(
    () => toApiFilters(committed, page),
    [committed, page]
  );

  const listFilterParams = useMemo(
    () => toListFilterParams(committed),
    [committed]
  );

  const hasPendingChanges = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(committed),
    [committed, draft]
  );

  const applyFilters = useCallback(() => {
    setCommitted({ ...draft });
    setPage(1);
  }, [draft]);

  const resetPage = useCallback(() => setPage(1), []);

  const patchDraft = useCallback(
    (patch: Partial<EficienciaFabrilFilterState>) => {
      setDraft((current) => ({ ...current, ...patch }));
    },
    []
  );

  return {
    branches: BRANCHES,
    dateStart: draft.dateStart,
    dateEnd: draft.dateEnd,
    branch: draft.branch,
    op: draft.op,
    employee: draft.employee,
    workCenter: draft.workCenter,
    statusOkOnly: draft.statusOkOnly,
    hasPendingChanges,
    page,
    setDateStart: (value: string) => patchDraft({ dateStart: value }),
    setDateEnd: (value: string) => patchDraft({ dateEnd: value }),
    setBranch: (value: string) => patchDraft({ branch: value }),
    setOp: (value: string) => patchDraft({ op: value }),
    setEmployee: (value: string) => patchDraft({ employee: value }),
    setWorkCenter: (value: string) => patchDraft({ workCenter: value }),
    setStatusOkOnly: (value: boolean) => patchDraft({ statusOkOnly: value }),
    setPage,
    resetPage,
    applyFilters,
    apiParams,
    listFilterParams,
  };
}
