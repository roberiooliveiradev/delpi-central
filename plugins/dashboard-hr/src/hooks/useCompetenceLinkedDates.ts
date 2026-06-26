import { useCallback, useState } from "react";

import {
  applyCompetenceChange,
  applyDateEndChange,
  applyDateStartChange,
  type LinkedDateFilters,
} from "../utils/competenceFilters";

export function useCompetenceLinkedDates(initial: LinkedDateFilters) {
  const [dateStart, setDateStartState] = useState(initial.dateStart);
  const [dateEnd, setDateEndState] = useState(initial.dateEnd);
  const [competence, setCompetenceState] = useState(initial.competence);

  const replaceAll = useCallback((next: LinkedDateFilters) => {
    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
    setCompetenceState(next.competence);
  }, []);

  const setCompetence = useCallback((value: string) => {
    if (!value) {
      setCompetenceState("");
      return;
    }

    const next = applyCompetenceChange(value);
    setCompetenceState(next.competence);
    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
  }, []);

  const setDateStart = useCallback(
    (value: string) => {
      const next = applyDateStartChange(value, dateEnd);
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setCompetenceState(next.competence);
    },
    [dateEnd]
  );

  const setDateEnd = useCallback(
    (value: string) => {
      const next = applyDateEndChange(dateStart, value);
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setCompetenceState(next.competence);
    },
    [dateStart]
  );

  return {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceAll,
  };
}
