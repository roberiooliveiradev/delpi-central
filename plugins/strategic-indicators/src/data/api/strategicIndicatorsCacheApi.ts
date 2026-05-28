import { clearAllStrategicIndicatorsCache } from "../cache/strategicIndicatorsReadCache";
import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export type StrategicIndicatorsRefreshResponse = {
  status: "accepted" | "already_running";
  message: string;
};

export type StrategicIndicatorsRefreshStatusResponse = {
  running: boolean;
  last_started_at: string | null;
  last_completed_at: string | null;
  last_duration_ms: number | null;
  last_periods_upserted: number | null;
  last_error: string | null;
};

/** Atualização incremental (botão Atualizar): não apaga period_scores. */
export async function refreshStrategicIndicatorsSnapshots(
  options: {
    getAccessToken?: GetToken;
    competence?: string;
    trendsMonths?: number;
  } = {},
): Promise<StrategicIndicatorsRefreshResponse> {
  const response = await fetch(`${BASE_URL}/cache/refresh`, {
    method: "POST",
    headers: buildHeaders(options.getAccessToken),
    body: JSON.stringify({
      competence: options.competence ?? null,
      trends_months: options.trendsMonths ?? null,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `Falha ao iniciar atualização dos dados (${response.status}).`,
    );
  }

  return response.json();
}

export async function fetchStrategicIndicatorsRefreshStatus(
  getAccessToken?: GetToken,
): Promise<StrategicIndicatorsRefreshStatusResponse> {
  const response = await fetch(`${BASE_URL}/cache/refresh/status`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error(
      `Falha ao consultar status da atualização (${response.status}).`,
    );
  }

  return response.json();
}

const REFRESH_POLL_MS = 3000;
const REFRESH_POLL_MAX_MS = 45 * 60 * 1000;

export async function waitForStrategicIndicatorsRefresh(
  getAccessToken?: GetToken,
): Promise<StrategicIndicatorsRefreshStatusResponse> {
  const started = Date.now();

  for (;;) {
    const status = await fetchStrategicIndicatorsRefreshStatus(getAccessToken);
    if (!status.running) {
      return status;
    }
    if (Date.now() - started > REFRESH_POLL_MAX_MS) {
      throw new Error(
        "A atualização dos dados está demorando mais que o esperado. Tente novamente em alguns minutos.",
      );
    }
    await new Promise((resolve) => setTimeout(resolve, REFRESH_POLL_MS));
  }
}

/** @deprecated Preferir refreshStrategicIndicatorsSnapshots (incremental com versões). */
export async function invalidateStrategicIndicatorsCache(
  getAccessToken?: GetToken,
): Promise<void> {
  const response = await fetch(`${BASE_URL}/cache/invalidate`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error(
      `Falha ao invalidar cache do backend (${response.status}).`,
    );
  }

  clearAllStrategicIndicatorsCache();
}
