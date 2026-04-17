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

type PresentationWarningItem = {
  source: "tendencias" | "indicadores" | "detalhe_departamento";
  message: string;
};

type PresentationDataBundle = {
  executive: ExecutiveDashboardViewData;
  alerts: AlertsDashboardViewData;
  departments: DepartmentOverviewViewItem[];
  trends: TrendsDashboardViewData | null;
  departmentDetailsById: Record<string, DepartmentDetailsViewData>;
  indicators: IndicatorViewItem[];
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

export function useStrategicIndicatorsPresentation({
  competence,
  branch,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsPresentationParams) {
  const [bundle, setBundle] = useState<PresentationDataBundle | null>(null);
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

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    loadRef.current = async () => {
      const requestId = ++requestIdRef.current;

      if (hasLoadedOnceRef.current) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);
      setWarnings([]);

      const commonParams = {
        competence,
        branch,
        startDate,
        endDate,
        getAccessToken: getAccessTokenRef.current,
      };

      try {
        const [executiveResponse, alertsResponse, departmentsResponse, trendsResult] =
          await Promise.all([
            fetchStrategicIndicatorsExecutiveSummary(commonParams),
            fetchStrategicIndicatorsAlerts(commonParams),
            fetchStrategicIndicatorsDepartments(commonParams),
            settle(
              fetchStrategicIndicatorsTrends({
                ...commonParams,
                months,
              }),
            ),
          ]);

        if (requestId !== requestIdRef.current) {
          return;
        }

        const executive = adaptExecutiveSummaryToView(executiveResponse);
        const alerts = adaptAlertsToView(alertsResponse);
        const departments = adaptDepartmentsToView(departmentsResponse);

        const nextWarnings: PresentationWarningItem[] = [];

        const trends =
          trendsResult.status === "fulfilled"
            ? adaptTrendsToView(trendsResult.value)
            : (() => {
                nextWarnings.push({
                  source: "tendencias",
                  message: getSafeErrorMessage(
                    trendsResult.reason,
                    "Não foi possível carregar a tendência do período.",
                  ),
                });
                return null;
              })();

        const effectiveDepartmentId =
          selectedDepartmentId &&
          departments.some((item) => item.id === selectedDepartmentId)
            ? selectedDepartmentId
            : departments[0]?.id ?? null;

        let departmentDetailsById: Record<string, DepartmentDetailsViewData> = {};
        let indicators: IndicatorViewItem[] = [];

        if (effectiveDepartmentId) {
          const [detailsResult, indicatorsResult] = await Promise.all([
            settle(
              fetchStrategicIndicatorsDepartmentDetails({
                departmentId: effectiveDepartmentId,
                ...commonParams,
              }),
            ),
            settle(
              fetchStrategicIndicators({
                departmentId: effectiveDepartmentId,
                ...commonParams,
              }),
            ),
          ]);

          if (requestId !== requestIdRef.current) {
            return;
          }

          if (detailsResult.status === "fulfilled") {
            departmentDetailsById = {
              [effectiveDepartmentId]: adaptDepartmentDetailsToView(
                detailsResult.value,
              ),
            };
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
            indicators = adaptIndicatorsToView(indicatorsResult.value);
          } else {
            nextWarnings.push({
              source: "indicadores",
              message: getSafeErrorMessage(
                indicatorsResult.reason,
                "Não foi possível carregar os indicadores do departamento em foco.",
              ),
            });
          }
        }

        setBundle({
          executive,
          alerts,
          departments,
          trends,
          departmentDetailsById,
          indicators,
          selectedDepartmentId: effectiveDepartmentId,
        });
        setSelectedDepartmentId(effectiveDepartmentId);
        setWarnings(nextWarnings);
        hasLoadedOnceRef.current = true;
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
    };
  }, [competence, branch, startDate, endDate, months, selectedDepartmentId]);

  useEffect(() => {
    void loadRef.current();
  }, [competence, branch, startDate, endDate, months]);

  const data = useMemo<PresentationViewData | null>(() => {
    if (!bundle) {
      return null;
    }

    return buildPresentationViewData({
      executiveSummary: bundle.executive,
      executiveAlerts: bundle.alerts.executiveAlerts,
      alerts: bundle.alerts,
      departmentsOverview: bundle.departments,
      departmentDetailsById: bundle.departmentDetailsById,
      indicators: bundle.indicators,
      trends: bundle.trends,
      focusDepartmentId: bundle.selectedDepartmentId,
    });
  }, [bundle]);

  const departmentIds = useMemo(() => {
    return bundle?.departments.map((item) => item.id) ?? [];
  }, [bundle]);

  const setFocusedDepartmentId = useCallback((departmentId: string | null) => {
    setSelectedDepartmentId(departmentId);
  }, []);

  const reload = useCallback(() => loadRef.current(), []);

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