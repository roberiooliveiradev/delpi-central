import { useCallback, useState } from "react";

import {
  applyCompetenceChange,
  applyDateRangeChange,
  type LinkedDateFilters,
} from "../utils/competence";

const EMPTY: LinkedDateFilters = { dateStart: "", dateEnd: "", competence: "" };

/** Mantém competência (YYYY-MM) e intervalo de datas sincronizados, como no dashboard-quality. */
export function useCompetenceLinkedDates(initial: LinkedDateFilters = EMPTY) {
  const [state, setState] = useState<LinkedDateFilters>(initial);

  const setCompetence = useCallback((value: string) => {
    setState(applyCompetenceChange(value));
  }, []);

  const setDateStart = useCallback((value: string) => {
    setState((current) => applyDateRangeChange(value, current.dateEnd));
  }, []);

  const setDateEnd = useCallback((value: string) => {
    setState((current) => applyDateRangeChange(current.dateStart, value));
  }, []);

  const replaceAll = useCallback((next: LinkedDateFilters) => {
    setState(next);
  }, []);

  const reset = useCallback(() => setState(EMPTY), []);

  return {
    dateStart: state.dateStart,
    dateEnd: state.dateEnd,
    competence: state.competence,
    setCompetence,
    setDateStart,
    setDateEnd,
    replaceAll,
    reset,
  };
}
