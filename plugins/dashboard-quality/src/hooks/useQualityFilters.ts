import { useCallback, useState } from "react";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
  inputDateToApi,
} from "../utils/dates";
import type { DateRangeParams } from "../types/ppm";

export function useQualityFilters() {
  const [dateStart, setDateStart] = useState(getFirstDayOfMonthInputValue);
  const [dateEnd, setDateEnd] = useState(getTodayInputValue);
  const [branch, setBranch] = useState("");

  const apiParams: DateRangeParams = {
    branch: branch || undefined,
    date_start: inputDateToApi(dateStart),
    date_end: inputDateToApi(dateEnd),
  };

  const resetFilters = useCallback(() => {
    setDateStart(getFirstDayOfMonthInputValue());
    setDateEnd(getTodayInputValue());
    setBranch("");
  }, []);

  return {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    resetFilters,
  };
}
