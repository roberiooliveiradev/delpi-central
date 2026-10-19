import { createContext, useContext } from "react";
import type { useWorkCenterActivity } from "./useWorkCenterActivity";

export type CockpitActivityState = ReturnType<typeof useWorkCenterActivity>;

export const CockpitActivityContext =
  createContext<CockpitActivityState | null>(null);

/**
 * Leitura diária MES compartilhada do cockpit (Etapa 4): um único hook —
 * e um único GET por escopo — alimenta o cartão de acesso, os indicadores
 * do cabeçalho e a tela de Atividade do posto.
 */
export function useCockpitActivity(): CockpitActivityState {
  const ctx = useContext(CockpitActivityContext);
  if (!ctx) {
    throw new Error(
      "useCockpitActivity deve ser usado dentro do CockpitActivityProvider.",
    );
  }
  return ctx;
}
