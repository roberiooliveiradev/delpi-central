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

      const requestId = ++detailRequestIdRef.current;

      const [detailsResult, indicatorsResult] = await Promise.all([
        settle(
          fetchStrategicIndicatorsDepartmentDetails({
            departmentId,
            competence,
            branch,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
        ),
        settle(
          fetchStrategicIndicators({
            departmentId,
            competence,
            branch,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
        ),
      ]);

      if (!prefetchOnly && requestId !== detailRequestIdRef.current) {
        return;
      }

      const nextWarnings: PresentationWarningItem[] = [];
      let nextDetails: DepartmentDetailsViewData | undefined;
      let nextIndicators: IndicatorViewItem[] | undefined;

      if (detailsResult.status === "fulfilled") {
        nextDetails = adaptDepartmentDetailsToView(detailsResult.value);
      } else {
        nextWarnings.push({
          source: "detalhe_departamento",
          message: getSafeErrorMessage(
            detailsResult.reason,
            "Não foi possível carregar o detalhamento do departamento em foco.",
          ),
        });
      }

      if (indicatorsResult.status === "fulfilled") {
        nextIndicators = adaptIndicatorsToView(indicatorsResult.value);
      } else {
        nextWarnings.push({
          source: "indicadores",
          message: getSafeErrorMessage(
            indicatorsResult.reason,
            "Não foi possível carregar os indicadores do departamento em foco.",
          ),
        });
      }

      setBundle((current) => ({
        ...current,
        selectedDepartmentId: prefetchOnly
          ? current.selectedDepartmentId
          : departmentId,
        departmentDetailsById: nextDetails
          ? {
              ...current.departmentDetailsById,
              [departmentId]: nextDetails,
            }
          : current.departmentDetailsById,
        indicatorsByDepartmentId: nextIndicators
          ? {
              ...current.indicatorsByDepartmentId,
              [departmentId]: nextIndicators,
            }
          : current.indicatorsByDepartmentId,
      }));

      if (nextWarnings.length > 0) {
        setWarnings((current) => mergeWarnings(current, nextWarnings));
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

    try {
      const [executiveResponse, alertsResponse, departmentsResponse] =
        await Promise.all([
          fetchStrategicIndicatorsExecutiveSummary(commonParams),
          fetchStrategicIndicatorsAlerts(commonParams),
          fetchStrategicIndicatorsDepartments(commonParams),
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

      setBundle((current) => ({
        ...current,
        executive,
        alerts,
        departments,
        selectedDepartmentId: effectiveDepartmentId,
      }));

      setSelectedDepartmentId(effectiveDepartmentId);
      hasLoadedOnceRef.current = true;

      void (async () => {
        const trendsResult = await settle(
          fetchStrategicIndicatorsTrends({
            competence,
            branch,
            startDate,
            endDate,
            months,
            getAccessToken: getAccessTokenRef.current,
          }),
        );

        if (requestId !== requestIdRef.current) {
          return;
        }

        if (trendsResult.status === "fulfilled") {
          setBundle((current) => ({
            ...current,
            trends: adaptTrendsToView(trendsResult.value),
          }));
        } else {
          setWarnings((current) =>
            mergeWarnings(current, [
              {
                source: "tendencias",
                message: getSafeErrorMessage(
                  trendsResult.reason,
                  "Não foi possível carregar a tendência do período.",
                ),
              },
            ]),
          );
        }
      })();

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
    const hasIndicators = Boolean(bundle.indicatorsByDepartmentId[selectedDepartmentId]);

    if (!hasDetails || !hasIndicators) {
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
        !bundle.indicatorsByDepartmentId[nextDepartmentId]
      ) {
        void loadDepartmentDetails(nextDepartmentId, true);
      }
    }
  }, [
    selectedDepartmentId,
    bundle.departments,
    bundle.departmentDetailsById,
    bundle.indicatorsByDepartmentId,
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