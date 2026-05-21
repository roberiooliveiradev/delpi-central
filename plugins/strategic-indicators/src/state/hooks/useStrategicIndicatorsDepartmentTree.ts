import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentTreeBundleToModel } from "../../data/adapters/departmentTreeBundleAdapter";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import {
  pickActiveTreeColumn,
  resolveActiveTreeScopeKey,
  resolveDepartmentTreeScopes,
} from "../../data/departmentTreeScopes";
import { fetchStrategicIndicatorsDepartmentTree } from "../../data/api/strategicIndicatorsDepartmentTreeApi";
import {
  writeDepartmentsReadCache,
  writeIndicatorsReadCache,
} from "../../data/builders/departmentTreeCacheWrites";
import { tryBuildDepartmentTreeFromReadCache } from "../../data/builders/departmentTreeReadCache";
import type { DepartmentTreeModel } from "../../data/types/departmentTree";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import type { StrategicIndicatorsViewMode } from "../../ui/shared/strategicIndicatorsFilters";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";

type UseStrategicIndicatorsDepartmentTreeParams = {
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

type DepartmentTreeCache = {
  model: DepartmentTreeModel;
};

function narrowDepartmentTreeModel(
  model: DepartmentTreeModel,
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): DepartmentTreeModel {
  const activeScopeKey = resolveActiveTreeScopeKey(viewMode, branch);
  const activeColumn = pickActiveTreeColumn(model.columns, activeScopeKey);

  if (!activeColumn || model.columns.length <= 1) {
    return model;
  }

  return {
    ...model,
    columns: [activeColumn],
  };
}

export function useStrategicIndicatorsDepartmentTree({
  viewMode,
  branch,
  competence,
  startDate,
  endDate,
  months = 6,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentTreeParams) {
  const [model, setModel] = useState<DepartmentTreeModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

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
      months,
    });
    const cachedTree =
      getStrategicIndicatorsCachedValue<DepartmentTreeCache>(cacheKey);
    const hydratedFromReads = tryBuildDepartmentTreeFromReadCache({
      viewMode,
      branch,
      scopes,
      query,
    });

    const cachedModel = cachedTree?.model ?? hydratedFromReads;
    const scopedCachedModel = cachedModel
      ? narrowDepartmentTreeModel(cachedModel, viewMode, branch)
      : null;

    beginStrategicIndicatorsLoad({
      cached: scopedCachedModel,
      hasLoadedOnce: hasLoadedOnceRef.current,
      setValue: (value) => setModel(value),
      setLoading,
      setRefreshing,
    });

    setError(null);
    beginSingleRequestProgress(setRequestProgress);

    try {
      const token = getAccessTokenRef.current;
      const bundle = await fetchStrategicIndicatorsDepartmentTree({
        viewMode,
        branch: viewMode === "branch" ? branch : undefined,
        competence,
        startDate,
        endDate,
        months,
        getAccessToken: token,
        signal: controller.signal,
      });

      if (requestId !== requestIdRef.current) {
        return;
      }

      const nextModel = narrowDepartmentTreeModel(
        adaptDepartmentTreeBundleToModel(bundle),
        viewMode,
        branch,
      );

      for (const scope of bundle.scopes) {
        writeDepartmentsReadCache(
          query,
          scope.branch ?? undefined,
          adaptDepartmentsToView(scope.departments),
        );
        writeIndicatorsReadCache(
          query,
          scope.branch ?? undefined,
          adaptIndicatorsToView(scope.indicators),
        );
      }

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
          route: "/departments/tree",
          method: "GET",
          competence: competence ?? null,
          branch: branch ?? null,
        }),
      );
    } finally {
      if (requestId === requestIdRef.current) {
        finishSingleRequestProgress(setRequestProgress, controller.signal.aborted);
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [viewMode, branch, competence, startDate, endDate, months, scopes, query]);

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
      requestProgress,
      error,
      reload,
    }),
    [model, loading, refreshing, requestProgress, error, reload],
  );
}
