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
};

function getSafeErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export function useStrategicIndicatorsPresentation({
  competence,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsPresentationParams) {
  const [bundle, setBundle] = useState<PresentationDataBundle | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<PresentationWarningItem[]>([]);

  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);
  const selectedDepartmentIdRef = useRef<string | null>(null);
  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  useEffect(() => {
    selectedDepartmentIdRef.current = selectedDepartmentId;
  }, [selectedDepartmentId]);

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

      try {
        const [
          executiveResponse,
          alertsResponse,
          departmentsResponse,
          trendsResult,
        ] = await Promise.all([
          fetchStrategicIndicatorsExecutiveSummary({
            competence,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
          fetchStrategicIndicatorsAlerts({
            competence,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
          fetchStrategicIndicatorsDepartments({
            competence,
            startDate,
            endDate,
            getAccessToken: getAccessTokenRef.current,
          }),
          fetchStrategicIndicatorsTrends({
            competence,
            months,
            getAccessToken: getAccessTokenRef.current,
          }).then(
            (response) => ({ status: "fulfilled", value: response } as const),
            (reason) => ({ status: "rejected", reason } as const),
          ),
        ]);

        if (requestId !== requestIdRef.current) {
          return;
        }

        const executive = adaptExecutiveSummaryToView(executiveResponse);
        const alerts = adaptAlertsToView(alertsResponse);
        const departments = adaptDepartmentsToView(departmentsResponse);

        const nextWarnings: PresentationWarningItem[] = [];
        let trends: TrendsDashboardViewData | null = null;

        if (trendsResult.status === "fulfilled") {
          trends = adaptTrendsToView(trendsResult.value);
        } else {
          nextWarnings.push({
            source: "tendencias",
            message: getSafeErrorMessage(
              trendsResult.reason,
              "Não foi possível carregar a tendência do período.",
            ),
          });
        }

        const currentSelectedDepartmentId = selectedDepartmentIdRef.current;
        const effectiveDepartmentId =
          currentSelectedDepartmentId &&
          departments.some((item) => item.id === currentSelectedDepartmentId)
            ? currentSelectedDepartmentId
            : departments[0]?.id ?? null;

        let departmentDetailsById: Record<string, DepartmentDetailsViewData> = {};
        let indicators: IndicatorViewItem[] = [];

        if (effectiveDepartmentId) {
          const [detailsResult, indicatorsResult] = await Promise.all([
            fetchStrategicIndicatorsDepartmentDetails({
              departmentId: effectiveDepartmentId,
              competence,
              startDate,
              endDate,
              getAccessToken: getAccessTokenRef.current,
            }).then(
              (response) => ({ status: "fulfilled", value: response } as const),
              (reason) => ({ status: "rejected", reason } as const),
            ),
            fetchStrategicIndicators({
              departmentId: effectiveDepartmentId,
              startDate,
              endDate,
              getAccessToken: getAccessTokenRef.current,
            }).then(
              (response) => ({ status: "fulfilled", value: response } as const),
              (reason) => ({ status: "rejected", reason } as const),
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
        });

        selectedDepartmentIdRef.current = effectiveDepartmentId;
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
  }, [competence, startDate, endDate, months]);

  useEffect(() => {
    if (!hasLoadedOnceRef.current) {
      return;
    }

    void loadRef.current();
  }, [selectedDepartmentId]);

  useEffect(() => {
    void loadRef.current();
  }, [competence, startDate, endDate, months]);

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
      focusDepartmentId: selectedDepartmentId,
    });
  }, [bundle, selectedDepartmentId]);

  const departmentIds = useMemo(() => {
    return bundle?.departments.map((item) => item.id) ?? [];
  }, [bundle]);

  const setFocusedDepartmentId = useCallback((departmentId: string | null) => {
    selectedDepartmentIdRef.current = departmentId;
    setSelectedDepartmentId(departmentId);
  }, []);

  const reload = useCallback(() => {
    return loadRef.current();
  }, []);

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