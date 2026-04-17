import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adaptAlertsToView } from "../../data/adapters/alertsAdapter";
import { adaptDepartmentDetailsToView } from "../../data/adapters/departmentDetailsAdapter";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import { adaptTrendsToView } from "../../data/adapters/trendsAdapter";
import { fetchStrategicIndicatorsAlerts } from "../../data/api/strategicIndicatorsAlertsApi";
import { fetchStrategicIndicatorsDepartmentDetails } from "../../data/api/strategicIndicatorsDepartmentDetailsApi";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import { fetchStrategicIndicatorsExecutiveSummary } from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import { fetchStrategicIndicators } from "../../data/api/strategicIndicatorsApi";
import { fetchStrategicIndicatorsTrends } from "../../data/api/strategicIndicatorsTrendsApi";
import {
  buildPresentationViewData,
  type PresentationViewData,
} from "../../data/types/presentation";
import type { AlertsDashboardViewData } from "../../data/types/alerts";
import type { DepartmentDetailsViewData } from "../../data/types/departmentDetails";
import type { DepartmentOverviewViewItem } from "../../data/types/departments";
import type { ExecutiveDashboardViewData } from "../../data/types/executiveSummary";
import type { IndicatorViewItem } from "../../data/types/indicators";
import type { TrendsDashboardViewData } from "../../data/types/trends";

type UseStrategicIndicatorsPresentationParams = {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

type PresentationWarningSource =
  | "tendencias"
  | "indicadores"
  | "detalhe_departamento";

type PresentationWarningItem = {
  source: PresentationWarningSource;
  message: string;
};

type PresentationDataBundle = {
  executive: ExecutiveDashboardViewData | null;
  alerts: AlertsDashboardViewData | null;
  departments: DepartmentOverviewViewItem[];
  trends: TrendsDashboardViewData | null;
  departmentDetailsById: Record<string, DepartmentDetailsViewData>;
  departmentDetailsRequestedById: Record<string, boolean>;
  indicatorsByDepartmentId: Record<string, IndicatorViewItem[]>;
  selectedDepartmentId: string | null;
};

type SettledResult<T> =
  | { status: "fulfilled"; value: T }
  | { status: "rejected"; reason: unknown };

function getSafeErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function settle<T>(promise: Promise<T>): Promise<SettledResult<T>> {
  return promise.then(
    (value) => ({ status: "fulfilled", value }) as const,
    (reason) => ({ status: "rejected", reason }) as const,
  );
}

function createInitialBundle(): PresentationDataBundle {
  return {
    executive: null,
    alerts: null,
    departments: [],
    trends: null,
    departmentDetailsById: {},
    departmentDetailsRequestedById: {},
    indicatorsByDepartmentId: {},
    selectedDepartmentId: null,
  };
}

function mergeWarnings(
  previous: PresentationWarningItem[],
  next: PresentationWarningItem[],
) {
  const map = new Map<PresentationWarningSource, PresentationWarningItem>();

  [...previous, ...next].forEach((item) => {
    map.set(item.source, item);
  });

  return Array.from(map.values());
}

function groupIndicatorsByDepartmentId(params: {
  response: Awaited<ReturnType<typeof fetchStrategicIndicators>>;
  departmentIds: string[];
}) {
  const { response, departmentIds } = params;

  const groupedRawItems = new Map<string, typeof response.items>();

  for (const item of response.items ?? []) {
    const departmentId = item.department_id;

    if (!departmentId) {
      continue;
    }

    const currentItems = groupedRawItems.get(departmentId) ?? [];
    currentItems.push(item);
    groupedRawItems.set(departmentId, currentItems);
  }

  const groupedIndicators: Record<string, IndicatorViewItem[]> = {};

  for (const departmentId of departmentIds) {
    const rawItems = groupedRawItems.get(departmentId) ?? [];

    groupedIndicators[departmentId] = adaptIndicatorsToView({
      items: rawItems,
      errors: [],
      partial_success: false,
    });
  }

  return groupedIndicators;
}

export function useStrategicIndicatorsPresentation({
  competence,
  branch,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsPresentationParams) {
  const [bundle, setBundle] = useState<PresentationDataBundle>(
    createInitialBundle(),
  );
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<PresentationWarningItem[]>([]);

  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);
  const detailRequestIdRef = useRef(0);
  const detailRequestsInFlightRef = useRef<Record<string, boolean>>({});

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const commonParams = useMemo(
    () => ({
      competence,
      branch,
      startDate,
      endDate,
      getAccessToken: getAccessTokenRef.current,
    }),
    [competence, branch, startDate, endDate],
  );

  const loadDepartmentDetails = useCallback(
    async (departmentId: string, prefetchOnly = false) => {
      if (!departmentId) return;

      if (detailRequestsInFlightRef.current[departmentId]) {
        return;
      }

      detailRequestsInFlightRef.current[departmentId] = true;

      setBundle((current) => ({
        ...current,
        departmentDetailsRequestedById: {
          ...current.departmentDetailsRequestedById,
          [departmentId]: true,
        },
      }));

      const requestId = ++detailRequestIdRef.current;

      try {
        const detailsResult = await settle(
          fetchStrategicIndicatorsDepartmentDetails({
            departmentId,
            competence,
            branch,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
        );

        if (!prefetchOnly && requestId !== detailRequestIdRef.current) {
          return;
        }

        if (detailsResult.status === "fulfilled") {
          const nextDetails = adaptDepartmentDetailsToView(detailsResult.value);

          setBundle((current) => ({
            ...current,
            selectedDepartmentId: prefetchOnly
              ? current.selectedDepartmentId
              : departmentId,
            departmentDetailsById: {
              ...current.departmentDetailsById,
              [departmentId]: nextDetails,
            },
          }));

          return;
        }

        setWarnings((current) =>
          mergeWarnings(current, [
            {
              source: "detalhe_departamento",
              message: getSafeErrorMessage(
                detailsResult.reason,
                "Não foi possível carregar o detalhamento do departamento em foco.",
              ),
            },
          ]),
        );
      } finally {
        detailRequestsInFlightRef.current[departmentId] = false;
      }
    },
    [competence, branch, startDate, endDate],
  );

  const reloadBase = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    if (hasLoadedOnceRef.current) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError(null);
    setWarnings([]);
    detailRequestsInFlightRef.current = {};

    try {
      const [
        executiveResponse,
        alertsResponse,
        departmentsResponse,
        indicatorsResult,
        trendsResult,
      ] = await Promise.all([
        fetchStrategicIndicatorsExecutiveSummary(commonParams),
        fetchStrategicIndicatorsAlerts(commonParams),
        fetchStrategicIndicatorsDepartments(commonParams),
        settle(fetchStrategicIndicators(commonParams)),
        settle(
          fetchStrategicIndicatorsTrends({
            competence,
            branch,
            startDate,
            endDate,
            months,
            getAccessToken: getAccessTokenRef.current,
          }),
        ),
      ]);

      if (requestId !== requestIdRef.current) {
        return;
      }

      const executive = adaptExecutiveSummaryToView(executiveResponse);
      const alerts = adaptAlertsToView(alertsResponse);
      const departments = adaptDepartmentsToView(departmentsResponse);

      const effectiveDepartmentId =
        selectedDepartmentId &&
        departments.some((item) => item.id === selectedDepartmentId)
          ? selectedDepartmentId
          : departments[0]?.id ?? null;

      const departmentIds = departments.map((item) => item.id);
      const indicatorsByDepartmentId =
        indicatorsResult.status === "fulfilled"
          ? groupIndicatorsByDepartmentId({
              response: indicatorsResult.value,
              departmentIds,
            })
          : Object.fromEntries(
              departmentIds.map((departmentId) => [departmentId, []]),
            );

      setBundle((current) => ({
        ...current,
        executive,
        alerts,
        departments,
        trends:
          trendsResult.status === "fulfilled"
            ? adaptTrendsToView(trendsResult.value)
            : null,
        indicatorsByDepartmentId,
        selectedDepartmentId: effectiveDepartmentId,
      }));

      setSelectedDepartmentId(effectiveDepartmentId);
      hasLoadedOnceRef.current = true;

      const nextWarnings: PresentationWarningItem[] = [];

      if (indicatorsResult.status === "rejected") {
        nextWarnings.push({
          source: "indicadores",
          message: getSafeErrorMessage(
            indicatorsResult.reason,
            "Não foi possível carregar os indicadores consolidados da apresentação.",
          ),
        });
      }

      if (trendsResult.status === "rejected") {
        nextWarnings.push({
          source: "tendencias",
          message: getSafeErrorMessage(
            trendsResult.reason,
            "Não foi possível carregar a tendência do período.",
          ),
        });
      }

      if (nextWarnings.length > 0) {
        setWarnings((current) => mergeWarnings(current, nextWarnings));
      }

      if (effectiveDepartmentId) {
        void loadDepartmentDetails(effectiveDepartmentId, false);

        const nextDepartmentId =
          departments.find((item) => item.id !== effectiveDepartmentId)?.id ??
          null;

        if (nextDepartmentId) {
          void loadDepartmentDetails(nextDepartmentId, true);
        }
      }
    } catch (err) {
      if (requestId !== requestIdRef.current) {
        return;
      }

      setError(
        getSafeErrorMessage(
          err,
          "Erro inesperado ao carregar a apresentação executiva.",
        ),
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [
    commonParams,
    competence,
    branch,
    startDate,
    endDate,
    months,
    selectedDepartmentId,
    loadDepartmentDetails,
  ]);

  useEffect(() => {
    setBundle(createInitialBundle());
    setSelectedDepartmentId(null);
    void reloadBase();
  }, [reloadBase]);

  useEffect(() => {
    if (!selectedDepartmentId) {
      return;
    }

    const hasDetails = Boolean(bundle.departmentDetailsById[selectedDepartmentId]);
    const hasRequestedDetails = Boolean(
      bundle.departmentDetailsRequestedById[selectedDepartmentId],
    );

    if (!hasDetails && !hasRequestedDetails) {
      void loadDepartmentDetails(selectedDepartmentId, false);
    }

    const currentIndex = bundle.departments.findIndex(
      (item) => item.id === selectedDepartmentId,
    );

    if (currentIndex >= 0) {
      const nextDepartmentId = bundle.departments[currentIndex + 1]?.id;

      if (
        nextDepartmentId &&
        !bundle.departmentDetailsById[nextDepartmentId] &&
        !bundle.departmentDetailsRequestedById[nextDepartmentId]
      ) {
        void loadDepartmentDetails(nextDepartmentId, true);
      }
    }
  }, [
    selectedDepartmentId,
    bundle.departments,
    bundle.departmentDetailsById,
    bundle.departmentDetailsRequestedById,
    loadDepartmentDetails,
  ]);

  const data = useMemo<PresentationViewData | null>(() => {
    if (!bundle.executive || !bundle.alerts || bundle.departments.length === 0) {
      return null;
    }

    return buildPresentationViewData({
      executiveSummary: bundle.executive,
      executiveAlerts: bundle.alerts.executiveAlerts,
      alerts: bundle.alerts,
      departmentsOverview: bundle.departments,
      departmentDetailsById: bundle.departmentDetailsById,
      indicatorsByDepartmentId: bundle.indicatorsByDepartmentId,
      trends: bundle.trends,
      focusDepartmentId: bundle.selectedDepartmentId,
    });
  }, [bundle]);

  const departmentIds = useMemo(
    () => bundle.departments.map((item) => item.id),
    [bundle.departments],
  );

  const setFocusedDepartmentId = useCallback((departmentId: string | null) => {
    setSelectedDepartmentId(departmentId);
    setBundle((current) => ({
      ...current,
      selectedDepartmentId: departmentId,
    }));
  }, []);

  const reload = useCallback(async () => {
    await reloadBase();
  }, [reloadBase]);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      error,
      warnings,
      departmentIds,
      selectedDepartmentId,
      setFocusedDepartmentId,
      reload,
    }),
    [
      data,
      loading,
      refreshing,
      error,
      warnings,
      departmentIds,
      selectedDepartmentId,
      setFocusedDepartmentId,
      reload,
    ],
  );
}