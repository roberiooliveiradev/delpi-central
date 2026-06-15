import { getProductionOeeAppointmentById } from "../api/productionApi";
import type { ProductionOeeAppointmentDetailData } from "../types/production";
import { useProductionResource } from "./useProductionResource";

type UseProductionOeeAppointmentDetailOptions = {
  branch?: string;
};

export function useProductionOeeAppointmentDetail(
  appointmentId: string,
  options: UseProductionOeeAppointmentDetailOptions = {}
) {
  const normalizedId = appointmentId.trim();
  const branch = options.branch?.trim() || undefined;

  const { data, loading, error, reload } = useProductionResource<ProductionOeeAppointmentDetailData>(
    (signal) =>
      getProductionOeeAppointmentById(
        normalizedId,
        { branch },
        signal
      ),
    [normalizedId, branch],
    {
      enabled: Boolean(normalizedId),
      cacheKey: `oee-appointment:${normalizedId}:${branch ?? "all"}`,
    }
  );

  return {
    data,
    appointment: data?.appointment ?? null,
    timeAnalysis: data?.time_analysis ?? null,
    routingOperations: data?.routing_operations ?? [],
    structure: data?.structure ?? null,
    relatedRoutes: data?.related_routes ?? null,
    loading,
    error,
    reload,
  };
}
