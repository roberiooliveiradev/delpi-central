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
import type { PresentationViewData } from "../../data/types/presentation";

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
  const [error, setError] = useState<string | null>(null);
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

      if (hasLoadedOnceRef.current) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const nextPayload = await fetchStrategicIndicatorsPresentation({
          competence,
          branch,
          startDate,
          endDate,
          months,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setPayload(nextPayload);
        setWarnings(adaptPresentationWarnings(nextPayload));

        const nextDepartmentIds = nextPayload.departments_overview.map(
          (department) => department.id,
        );

        setSelectedDepartmentId((current) => {
          if (current && nextDepartmentIds.includes(current)) {
            return current;
          }

          return nextDepartmentIds[0] ?? null;
        });

        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar a apresentação executiva.",
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
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