import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchStrategicIndicatorsPresentation,
  type StrategicIndicatorsPresentationApiResponse,
} from "../../data/api/strategicIndicatorsPresentationApi";
import {
  adaptPresentationPayloadToViewData,
  adaptPresentationWarnings,
  type PresentationWarningItem,
} from "../../data/adapters/presentationPayloadAdapter";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import type { PresentationViewData } from "../../data/types/presentation";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";
import { beginStrategicIndicatorsLoad } from "./strategicIndicatorsLoadState";

type UseStrategicIndicatorsPresentationParams = {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsPresentation({
  competence,
  branch,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
}: UseStrategicIndicatorsPresentationParams) {
  const [payload, setPayload] =
    useState<StrategicIndicatorsPresentationApiResponse | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);
  const [warnings, setWarnings] = useState<PresentationWarningItem[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);
  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  useEffect(() => {
    loadRef.current = async () => {
      const requestId = ++requestIdRef.current;

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      beginStrategicIndicatorsLoad({
        cached: payload,
        hasLoadedOnce: hasLoadedOnceRef.current,
        setValue: setPayload,
        setLoading,
        setRefreshing,
      });

      setError(null);
      setTrendsLoading(true);

      try {
        const overviewPayload = await fetchStrategicIndicatorsPresentation({
          competence,
          branch,
          startDate,
          endDate,
          months,
          include:
            "executive_summary,departments_overview,department_details_by_id,indicators_by_department_id,alerts",
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setPayload(overviewPayload);
        setWarnings(adaptPresentationWarnings(overviewPayload));
        hasLoadedOnceRef.current = true;
        setLoading(false);
        setRefreshing(false);

        const overviewDepartmentIds = overviewPayload.departments_overview.map(
          (department) => department.id,
        );
        setSelectedDepartmentId((current) => {
          if (current && overviewDepartmentIds.includes(current)) {
            return current;
          }
          return overviewDepartmentIds[0] ?? null;
        });

        const trendsPayload = await fetchStrategicIndicatorsPresentation({
          competence,
          branch,
          startDate,
          endDate,
          months,
          include: "trends",
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        const nextPayload: StrategicIndicatorsPresentationApiResponse = {
          ...overviewPayload,
          trends: trendsPayload.trends,
          meta: {
            partial_success:
              overviewPayload.meta.partial_success ||
              trendsPayload.meta.partial_success,
            errors: [
              ...overviewPayload.meta.errors,
              ...trendsPayload.meta.errors,
            ],
          },
        };

        setPayload(nextPayload);
        setWarnings(adaptPresentationWarnings(nextPayload));
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Apresentação executiva",
            route: "/presentation",
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
          }),
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
          setTrendsLoading(false);
        }
      }
    };
  }, [competence, branch, startDate, endDate, months]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [competence, branch, startDate, endDate, months]);

  const data = useMemo<PresentationViewData | null>(() => {
    if (!payload) {
      return null;
    }

    return adaptPresentationPayloadToViewData({
      payload,
      focusDepartmentId: selectedDepartmentId,
    });
  }, [payload, selectedDepartmentId]);

  const departmentIds = useMemo(
    () => payload?.departments_overview.map((item) => item.id) ?? [],
    [payload],
  );

  const setFocusedDepartmentId = useCallback((departmentId: string | null) => {
    setSelectedDepartmentId(departmentId);
  }, []);

  const reload = useCallback(async () => {
    await loadRef.current();
  }, []);

  const retryFailedParts = useCallback(async () => {
    await loadRef.current();
  }, []);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      trendsLoading,
      error,
      warnings,
      departmentIds,
      selectedDepartmentId,
      setFocusedDepartmentId,
      retryFailedParts,
      reload,
    }),
    [
      data,
      loading,
      refreshing,
      trendsLoading,
      error,
      warnings,
      departmentIds,
      selectedDepartmentId,
      setFocusedDepartmentId,
      retryFailedParts,
      reload,
    ],
  );
}