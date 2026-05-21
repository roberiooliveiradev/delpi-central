import {
  parseStrategicIndicatorsError,
  StrategicIndicatorsApiError,
  type StrategicIndicatorsErrorContext,
  type StrategicIndicatorsErrorView,
} from "../errors/strategicIndicatorsError";

type ApiErrorBody = {
  detail?: unknown;
  message?: unknown;
  errors?: Array<{ message?: string; source?: string; department_id?: string }>;
};

function extractDetailMessage(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg?: string }).msg ?? "");
        }
        return "";
      })
      .filter(Boolean);

    return parts.length ? parts.join(" · ") : null;
  }

  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message?: string }).message ?? "");
  }

  return null;
}

async function readApiErrorBody(response: Response): Promise<ApiErrorBody | null> {
  try {
    return (await response.json()) as ApiErrorBody;
  } catch {
    return null;
  }
}

export async function buildStrategicIndicatorsApiError(
  response: Response,
  context: StrategicIndicatorsErrorContext,
): Promise<StrategicIndicatorsApiError> {
  const body = await readApiErrorBody(response);
  const detailMessage = extractDetailMessage(body?.detail);
  const fallbackMessage =
    typeof body?.message === "string" ? body.message : null;

  const measurementHint =
    body?.errors
      ?.map((item) => item.message)
      .filter(Boolean)
      .slice(0, 2)
      .join(" · ") ?? null;

  const rawMessage =
    detailMessage ??
    fallbackMessage ??
    measurementHint ??
    `Falha HTTP ${response.status} ao acessar ${context.route ?? "API"}.`;

  const view = parseStrategicIndicatorsError(rawMessage, {
    ...context,
    httpStatus: response.status,
  });

  return new StrategicIndicatorsApiError(view);
}

export function buildStrategicIndicatorsClientError(
  error: unknown,
  context: StrategicIndicatorsErrorContext,
): StrategicIndicatorsApiError {
  if (error instanceof StrategicIndicatorsApiError) {
    return error;
  }

  const message =
    error instanceof Error ? error.message : "Erro inesperado no módulo.";

  const view: StrategicIndicatorsErrorView = parseStrategicIndicatorsError(
    message,
    context,
  );

  return new StrategicIndicatorsApiError(view);
}
