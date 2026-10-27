import { getDowntimeInsights } from "../api/mesApi";
import type {
  DowntimeAnalyticsQuery,
  DowntimeInsightsResponse,
} from "../types/mes";
import { useDowntimeQuerySnapshot } from "./useDowntimeQuerySnapshot";

/** Análise avançada de paradas (Etapa 6): reincidência, comparação de
 * períodos, criticidade, pendências e eficácia de ações — mesmos filtros
 * e mesmo ciclo de vida de snapshot da consulta analítica. */
export function useDowntimeInsights(query: DowntimeAnalyticsQuery | null) {
  return useDowntimeQuerySnapshot<DowntimeInsightsResponse>(
    query,
    getDowntimeInsights,
    "Falha ao consultar a análise avançada de paradas.",
  );
}
