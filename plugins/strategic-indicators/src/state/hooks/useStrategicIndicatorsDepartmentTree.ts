import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  adaptTreeSnapshotToModel,
  mergeTreeTrendsIntoModel,
} from "../../data/adapters/departmentTreeBundleAdapter";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import {
  pickActiveTreeColumn,
  resolveActiveTreeScopeKey,
  resolveDepartmentTreeScopes,
} from "../../data/departmentTreeScopes";
import {
  fetchDepartmentTreeSnapshot,
  fetchDepartmentTreeTrends,
} from "../../data/api/strategicIndicatorsDepartmentTreeApi";
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
  EMPTY_REQUEST_PROGRESS,
  type RequestProgress,
} from "../utils/loadingProgress";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";
import { StrategicIndicatorsApiError } from "../../data/errors/strategicIndicatorsError";

function isGatewayTimeoutError(error: unknown): boolean {
  if (error instanceof StrategicIndicatorsApiError) {
    const status = error.view.context.httpStatus;
    if (status === 504) return true;
    const raw = (error.view.rawMessage ?? "").toLowerCase();
    return raw.includes("504") || raw.includes("timed out") || raw.includes("timeout");
  }
  if (error instanceof Error) {
    const raw = error.message.toLowerCase();
    return raw.includes("504") || raw.includes("timed out") || raw.includes("timeout");
  }
  return false;
}

async function sleep(ms: number, signal?: AbortSignal) {
  if (signal?.aborted) return;
  await new Promise<void>((resolve) => {
    const id = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(id);
        resolve();
      },
      { once: true },
    );
  });
}

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
  months = 3,
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
    setRequestProgress({ completed: 0, total: 2 });

    const token = getAccessTokenRef.current;
    const branchParam = viewMode === "branch" ? branch : undefined;

    try {
      let snapshot: Awaited<ReturnType<typeof fetchDepartmentTreeSnapshot>> | null =
        null;
      let lastSnapshotError: unknown = null;

      for (let attempt = 0; attempt < 2; attempt++) {
        try {
          snapshot = await fetchDepartmentTreeSnapshot({
            viewMode,
            branch: branchParam,
            competence,
            startDate,
            endDate,
            getAccessToken: token,
            signal: controller.signal,
          });
          lastSnapshotError = null;
          break;
        } catch (snapshotErr) {
          lastSnapshotError = snapshotErr;
          if (!isGatewayTimeoutError(snapshotErr) || controller.signal.aborted) {
            break;
          }
          await sleep(1200, controller.signal);
        }
      }

      if (!snapshot) {
        throw lastSnapshotError ?? new Error("Falha ao carregar snapshot da árvore.");
      }

      if (requestId !== requestIdRef.current) return;

      const snapshotModel = narrowDepartmentTreeModel(
        adaptTreeSnapshotToModel(snapshot),
        viewMode,
        branch,
      );

      for (const scope of snapshot.scopes) {
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

      setModel(snapshotModel);
      setLoading(false);
      setRefreshing(true);
      hasLoadedOnceRef.current = true;
      setRequestProgress({ completed: 1, total: 2 });

      const trends = await fetchDepartmentTreeTrends({
        viewMode,
        branch: branchParam,
        competence,
        startDate,
        endDate,
        months,
        getAccessToken: token,
        signal: controller.signal,
      });

      if (requestId !== requestIdRef.current) return;

      const enrichedModel = narrowDepartmentTreeModel(
        mergeTreeTrendsIntoModel(
          adaptTreeSnapshotToModel(snapshot),
          trends,
        ),
        viewMode,
        branch,
      );

      setModel(enrichedModel);
      setStrategicIndicatorsCachedValue(cacheKey, { model: enrichedModel });
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
        setRequestProgress({ completed: 2, total: 2 });
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
