import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet } from "./httpClient";

export type ForecastDeclarationData = {
  cycleYear: number;
  cycleMonth: number;
  portfolioId: string;
  declaredValue: number;
  updatedBy: string;
  updatedAt: string | null;
  nature: "declared_fct";
  empty: boolean;
};

export async function getCurrentForecast(
  signal?: AbortSignal,
  options?: { cycleYear?: number; cycleMonth?: number; portfolioId?: string },
): Promise<ForecastDeclarationData> {
  const params = new URLSearchParams();
  if (options?.cycleYear) params.set("cycle_year", String(options.cycleYear));
  if (options?.cycleMonth) params.set("cycle_month", String(options.cycleMonth));
  if (options?.portfolioId) params.set("portfolio_id", options.portfolioId);
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<ForecastDeclarationData>>(
    `${commercialApiUrl("/forecast/current")}${qs ? `?${qs}` : ""}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar previsão declarada.");
}
