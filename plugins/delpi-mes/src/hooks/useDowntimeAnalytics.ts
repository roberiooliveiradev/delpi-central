import { getDowntimeAnalytics } from "../api/mesApi";
import type {
  DowntimeAnalyticsQuery,
  DowntimeAnalyticsResponse,
} from "../types/mes";
import { useDowntimeQuerySnapshot } from "./useDowntimeQuerySnapshot";

/** Agregações gerenciais de paradas (Etapa 2) — delega o ciclo de vida
 * do snapshot ao mecanismo compartilhado de consultas de paradas. */
export function useDowntimeAnalytics(query: DowntimeAnalyticsQuery | null) {
  return useDowntimeQuerySnapshot<DowntimeAnalyticsResponse>(
    query,
    getDowntimeAnalytics,
    "Falha ao consultar os indicadores de paradas.",
  );
}
