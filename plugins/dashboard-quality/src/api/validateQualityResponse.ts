import type { ApiSuccessResponse } from "../types/api";

export class QualityApiContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "QualityApiContractError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/**
 * Validação leve do envelope `{ success, message, data }` sem dependência externa.
 * Substitui Zod até a Onda 4.3 formalizar schemas por endpoint.
 */
export function parseQualityApiEnvelope<T>(
  body: unknown,
  validateData: (data: unknown) => data is T
): ApiSuccessResponse<T> {
  if (!isRecord(body)) {
    throw new QualityApiContractError(
      "Resposta inválida da API de qualidade (corpo não é objeto JSON)."
    );
  }

  if (typeof body.success !== "boolean") {
    throw new QualityApiContractError(
      "Resposta inválida da API de qualidade (campo success ausente)."
    );
  }

  if (body.success === false) {
    const message =
      typeof body.message === "string"
        ? body.message
        : "Erro na API de qualidade";
    throw new Error(message);
  }

  if (!validateData(body.data)) {
    throw new QualityApiContractError(
      "Resposta inválida da API de qualidade (formato de data inesperado)."
    );
  }

  return {
    success: true,
    message: typeof body.message === "string" ? body.message : "",
    data: body.data,
  };
}

export function isQualityBranchesData(data: unknown): data is {
  branches: string[];
} {
  return (
    isRecord(data) &&
    Array.isArray(data.branches) &&
    data.branches.every((b) => typeof b === "string")
  );
}

function isSeriesPoints(
  data: unknown,
  valueKey: "ppm" | "value"
): boolean {
  if (!isRecord(data) || !Array.isArray(data.points)) {
    return false;
  }

  return data.points.every((p) => {
    if (!isRecord(p) || typeof p.periodo !== "string") {
      return false;
    }
    const metric = p[valueKey];
    return typeof metric === "number" && Number.isFinite(metric);
  });
}

export function isPpmSeriesData(
  data: unknown
): data is import("../types/ppm").PpmSeriesResponse {
  return (
    isRecord(data) &&
    typeof data.type === "string" &&
    typeof data.granularity === "string" &&
    typeof data.truncated === "boolean" &&
    isSeriesPoints(data, "ppm")
  );
}

export function isNonconformitySeriesData(
  data: unknown
): data is import("../types/nonconformity").NonconformitySeriesResponse {
  return (
    isRecord(data) &&
    typeof data.type === "string" &&
    typeof data.granularity === "string" &&
    typeof data.truncated === "boolean" &&
    isSeriesPoints(data, "value")
  );
}
