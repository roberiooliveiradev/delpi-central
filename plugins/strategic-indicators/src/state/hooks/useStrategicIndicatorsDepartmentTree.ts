import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import { buildDepartmentTreeModel } from "../../data/builders/buildDepartmentTreeModel";
import { resolveDepartmentTreeScopes } from "../../data/departmentTreeScopes";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import { fetchStrategicIndicatorsExecutiveSummary } from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import { fetchStrategicIndicators } from "../../data/api/strategicIndicatorsApi";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { DepartmentTreeModel } from "../../data/types/departmentTree";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import type { StrategicIndicatorsViewMode } from "../../ui/shared/strategicIndicatorsFilters";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";

type UseStrategicIndicatorsDepartmentTreeParams = {
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

type DepartmentTreeCache = {
  model: DepartmentTreeModel;
};

export function useStrategicIndicatorsDepartmentTree({
  viewMode,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentTreeParams) {
  const [model, setModel] = useState<DepartmentTreeModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);

  const scopes = useMemo(
    () => resolveDepartmentTreeScopes(viewMode, branch),
    [viewMode, branch],
  );

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    loadRef.current = async () => {
      const requestId = ++requestIdRef.current;

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const cacheKey = buildStrategicIndicatorsCacheKey("departments-tree", {
        competence,
        branch: viewMode === "branch" ? branch : "consolidated-all",
        viewMode,
        startDate,
        endDate,
      });
      const cached =
        getStrategicIndicatorsCachedValue<DepartmentTreeCache>(cacheKey);

      beginStrategicIndicatorsLoad({
        cached: cached?.model ?? null,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: (value) => setModel(value),
        setLoading,
        setRefreshing,
      });

      setError(null);

      try {
        const token = getAccessTokenRef.current;
        const executiveBranch =
          viewMode === "branch" && branch.trim() ? branch.trim() : undefined;

        const executivePromise = fetchStrategicIndicatorsExecutiveSummary({
          branch: executiveBranch,
          competence,
          startDate,
          endDate,
          getAccessToken: token,
          signal: controller.signal,
        });

        const scopePromises = scopes.map(async (scope) => {
          const [departmentsResponse, indicatorsResponse] = await Promise.all([
            fetchStrategicIndicatorsDepartments({
              branch: scope.branch,
              competence,
              startDate,
              endDate,
              getAccessToken: token,
              signal: controller.signal,
            }),
            fetchStrategicIndicators({
              branch: scope.branch,
              competence,
              startDate,
              endDate,
              getAccessToken: token,
              signal: controller.signal,
            }),
          ]);

          return {
            scope,
            departments: adaptDepartmentsToView(departmentsResponse),
            indicators: adaptIndicatorsToView(indicatorsResponse),
          };
        });

        const [executiveResult, ...scopeResults] = await Promise.all([
          executivePromise,
          ...scopePromises,
        ]);

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        const executive = adaptExecutiveSummaryToView(executiveResult);
        const nextModel = buildDepartmentTreeModel({
          competence: executive.competence,
          igd: executive.igd,
          igdExact: executive.igdExact,
          classification: executive.classification,
          scopePayloads: scopeResults,
        });

        setModel(nextModel);
        setStrategicIndicatorsCachedValue(cacheKey, { model: nextModel });
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Árvore de departamentos",
            route: "/departments",
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
          }),
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [viewMode, branch, competence, startDate, endDate, scopes]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [viewMode, branch, competence, startDate, endDate, scopes]);

  const reload = useCallback(() => {
    void loadRef.current();
  }, []);

  return useMemo(
    () => ({
      model,
      loading,
      refreshing,
      error,
      reload,
      isMultiColumn: viewMode === "consolidated",
    }),
    [model, loading, refreshing, error, reload, viewMode],
  );
}
