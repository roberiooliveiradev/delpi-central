import { useCallback, useEffect, useState } from "react";
import type { SuppliesFilterParams } from "../types/supplies";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readSuppliesFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type SuppliesFilterDefaults,
  type SuppliesFilterUrlState,
} from "../utils/filterUrl";

export type SuppliesFiltersOptions = {
  /**
   * Período inicial da página, usado somente quando a URL/sessão não
   * traz filtros. Convenção compartilhada: estado persistido vence o
   * default (o usuário carrega o recorte entre páginas).
   */
  defaultPeriod?: SuppliesFilterDefaults;
};

export function useSuppliesFilters(options?: SuppliesFiltersOptions) {
  // Capturado uma única vez: o default de período define apenas o estado
  // inicial e o fallback de re-sync — não é reativo.
  const [defaultPeriod] = useState(options?.defaultPeriod);
  const initial = readSuppliesFilters(undefined, defaultPeriod);
  const {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceAll,
  } = useCompetenceLinkedDates(initial);
  const [branches, setBranchesState] = useState(initial.branches);
  const [location, setLocationState] = useState(initial.location);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches, location });
  }, [dateStart, dateEnd, competence, branches, location]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readSuppliesFilters(undefined, defaultPeriod);
      replaceAll(next);
      setBranchesState(next.branches);
      setLocationState(next.location);
    });
  }, [replaceAll, defaultPeriod]);

  const resolvedBranch = resolveApiBranch(branches);
  /**
   * Seleção exata de filiais para contratos multivalorados
   * (`branch` repetível): [] = consolidado autorizado.
   */
  const apiBranches = branches;

  const periodParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const stockParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const filterState: SuppliesFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setLocation: useCallback((v: string) => setLocationState(v), []),
    apiBranches,
    periodParams,
    stockParams,
    filterState,
  };
}
