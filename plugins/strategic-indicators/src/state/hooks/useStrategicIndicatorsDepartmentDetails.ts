import { useEffect, useMemo, useRef, useState } from "react";
import { adaptDepartmentDetailsToView } from "../../data/adapters/departmentDetailsAdapter";
import { fetchStrategicIndicatorsDepartmentDetails } from "../../data/api/strategicIndicatorsDepartmentDetailsApi";
import type { DepartmentDetailsViewData } from "../../data/types/departmentDetails";
import type { StrategicIndicatorsErrorView } from "../../data/errors/strategicIndicatorsError";
import { captureStrategicIndicatorsError } from "./strategicIndicatorsCaptureError";

type UseStrategicIndicatorsDepartmentDetailsParams = {
  departmentId: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartmentDetails({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentDetailsParams) {
  const [data, setData] = useState<DepartmentDetailsViewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<StrategicIndicatorsErrorView | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);
  const getAccessTokenRef = useRef(getAccessToken);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const loadRef = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    loadRef.current = async () => {
      if (!departmentId) {
        setData(null);
        setLoading(false);
        setRefreshing(false);
        setError(
          captureStrategicIndicatorsError("Departamento inválido.", {
            surface: "Detalhe do departamento",
            route: "/departments/:id",
            departmentId: departmentId ?? null,
          }),
        );
        return;
      }

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
        const response = await fetchStrategicIndicatorsDepartmentDetails({
          departmentId,
          branch,
          competence,
          startDate,
          endDate,
          getAccessToken: getAccessTokenRef.current,
          signal: controller.signal,
        });

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setData(adaptDepartmentDetailsToView(response));
        hasLoadedOnceRef.current = true;
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        setError(
          captureStrategicIndicatorsError(err, {
            surface: "Detalhe do departamento",
            route: `/departments/${departmentId}`,
            method: "GET",
            competence: competence ?? null,
            branch: branch ?? null,
            departmentId,
          }),
        );
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };
  }, [departmentId, branch, competence, startDate, endDate]);

  useEffect(() => {
    void loadRef.current();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [departmentId, branch, competence, startDate, endDate]);

  return useMemo(
    () => ({
      data,
      loading,
      refreshing,
      error,
      reload: () => loadRef.current(),
    }),
    [data, loading, refreshing, error],
  );
}