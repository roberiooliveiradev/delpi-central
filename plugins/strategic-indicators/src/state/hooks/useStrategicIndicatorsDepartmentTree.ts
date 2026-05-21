import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import { buildDepartmentTreeModel } from "../../data/builders/buildDepartmentTreeModel";
import {
  writeDepartmentsReadCache,
  writeIndicatorsReadCache,
} from "../../data/builders/departmentTreeCacheWrites";
import { tryBuildDepartmentTreeFromReadCache } from "../../data/builders/departmentTreeReadCache";
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

  const query = useMemo(
    () => ({ competence, startDate, endDate }),
    [competence, startDate, endDate],
  );

  const load = useCallback(async () => {
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
    const cachedTree =
      getStrategicIndicatorsCachedValue<DepartmentTreeCache>(cacheKey);
    const hydratedFromReads = tryBuildDepartmentTreeFromReadCache({
      viewMode,
      branch,
      scopes,
      query,
    });

    beginStrategicIndicatorsLoad({
      cached: cachedTree?.model ?? hydratedFromReads,
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

        const departments = adaptDepartmentsToView(departmentsResponse);
        const indicators = adaptIndicatorsToView(indicatorsResponse);

        writeDepartmentsReadCache(query, scope.branch, departments);
        writeIndicatorsReadCache(query, scope.branch, indicators);

        return {
          scope,
          departments,
          indicators,
        };
      });

      const [executiveResult, ...scopeResults] = await Promise.all([
        executivePromise,
        ...scopePromises,
      ]);

      if (requestId !== requestIdRef.current) {
        return;
      }

      const executive = adaptExecutiveSummaryToView(executiveResult);
      setStrategicIndicatorsCachedValue(
        buildStrategicIndicatorsCacheKey("executive-summary", {
          competence,
          branch: executiveBranch,
          startDate,
          endDate,
        }),
        executive,
      );

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
      if (requestId === requestIdRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [viewMode, branch, competence, startDate, endDate, scopes, query]);

  useEffect(() => {
    void load();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [load]);

  const reload = useCallback(() => {
    void load();
  }, [load]);

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
