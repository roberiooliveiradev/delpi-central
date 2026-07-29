import { useCallback, useMemo, useState } from "react";

import {
  applyCompetenceChange,
  applyDateRangeChange,
  resolveLinkedDateFilters,
  type LinkedDateFilters,
} from "../utils/competence";

/**
 * Mantém competência (YYYY-MM) e intervalo de datas sincronizados, como no dashboard-quality.
 * Sem valores iniciais, começa no mês vigente; `reset` volta ao mesmo padrão.
 */
export function useCompetenceLinkedDates(initial?: LinkedDateFilters) {
  const initialState = useMemo(() => resolveLinkedDateFilters(initial ?? {}), [initial]);
  const [state, setState] = useState<LinkedDateFilters>(initialState);

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
    setState(resolveLinkedDateFilters(next));
  }, []);

  const reset = useCallback(() => setState(resolveLinkedDateFilters({})), []);

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
