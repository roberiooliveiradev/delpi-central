import { getProductionOeeAppointmentById } from "../api/productionOeeApi";
import type { ProductionOeeAppointmentDetailData } from "../types/productionOeeDetail";
import { useAsyncResource } from "./useAsyncResource";

type UseProductionOeeAppointmentDetailOptions = {
  branch?: string;
};

export function useProductionOeeAppointmentDetail(
  appointmentId: string,
  options: UseProductionOeeAppointmentDetailOptions = {}
) {
  const normalizedId = appointmentId.trim();
  const branch = options.branch?.trim() || undefined;

  const { data, loading, error, reload } = useAsyncResource<ProductionOeeAppointmentDetailData>(
    (signal) => getProductionOeeAppointmentById(normalizedId, { branch }, signal),
    [normalizedId, branch],
    Boolean(normalizedId)
  );

  return {
    data,
    appointment: data?.appointment ?? null,
    timeAnalysis: data?.time_analysis ?? null,
    routingOperations: data?.routing_operations ?? [],
    structure: data?.structure ?? null,
    loading,
    error,
    reload,
  };
}
