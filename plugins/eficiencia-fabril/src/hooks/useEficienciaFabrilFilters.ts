import { useCallback, useMemo, useState } from "react";

import type { EficienciaFabrilFilterParams } from "../types/eficienciaFabril";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../utils/dates";

const BRANCHES = ["01", "02"] as const;

export function useEficienciaFabrilFilters() {
  const [dateStart, setDateStart] = useState(getFirstDayOfMonthInputValue);
  const [dateEnd, setDateEnd] = useState(getTodayInputValue);
  const [branch, setBranch] = useState<string>("");
  const [employee, setEmployee] = useState("");
  const [workCenter, setWorkCenter] = useState("");
  const [statusOkOnly, setStatusOkOnly] = useState(true);
  const [page, setPage] = useState(1);

  const apiParams: EficienciaFabrilFilterParams = useMemo(
    () => ({
      date_start: dateStart,
      date_end: dateEnd,
      branch: branch || undefined,
      employee: employee.trim() || undefined,
      work_center: workCenter.trim() || undefined,
      status_ok_only: statusOkOnly,
      page,
      page_size: 50,
    }),
    [branch, dateEnd, dateStart, employee, page, statusOkOnly, workCenter]
  );

  const resetPage = useCallback(() => setPage(1), []);

  return {
    branches: BRANCHES,
    dateStart,
    dateEnd,
    branch,
    employee,
    workCenter,
    statusOkOnly,
    page,
    setDateStart,
    setDateEnd,
    setBranch,
    setEmployee,
    setWorkCenter,
    setStatusOkOnly,
    setPage,
    resetPage,
    apiParams,
  };
}
