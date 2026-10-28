import { getJson, HomeApiError } from "./httpClient";
import type {
  OverviewEnvelope,
  OverviewFilters,
  OverviewResponse,
} from "../types/overview";

const OVERVIEW_PATH = "/apps/engineering-api/v1/overview";

const INDICATOR_AVAILABILITIES = new Set([
  "available",
  "empty",
  "unavailable",
  "forbidden",
]);

function isValidIndicator(indicator: unknown): boolean {
  if (typeof indicator !== "object" || indicator === null) return false;
  const candidate = indicator as {
    id?: unknown;
    family?: unknown;
    availability?: unknown;
    source?: unknown;
  };
  return (
    typeof candidate.id === "string" &&
    (candidate.family === "lmp" || candidate.family === "transforma") &&
    typeof candidate.availability === "string" &&
    INDICATOR_AVAILABILITIES.has(candidate.availability) &&
    typeof candidate.source === "string"
  );
}

function assertContract(data: OverviewResponse): void {
  if (
    typeof data?.schema_version !== "string" ||
    typeof data?.generated_at !== "string" ||
    typeof data?.status !== "string" ||
    !Array.isArray(data?.indicators) ||
    !data.indicators.every(isValidIndicator)
  ) {
    throw new HomeApiError(
      "contract_error",
      "A resposta da Engineering API não está no formato esperado.",
    );
  }
}

function buildQuery(filters: OverviewFilters): string {
  const params = new URLSearchParams();
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.competence) params.set("competence", filters.competence);
  if (filters.branch) params.set("branch", filters.branch);
  const query = params.toString();
  return query ? `?${query}` : "";
}

/** `GET /apps/engineering-api/v1/overview` — operationId
 * get_engineering_overview, envelope canônico { success, data, meta }. */
export async function getEngineeringOverview(
  filters: OverviewFilters,
  signal?: AbortSignal,
): Promise<OverviewResponse> {
  const envelope = await getJson<OverviewEnvelope>(
    `${OVERVIEW_PATH}${buildQuery(filters)}`,
    signal,
  );
  if (!envelope || envelope.success !== true || !envelope.data) {
    throw new HomeApiError(
      "contract_error",
      "A resposta da Engineering API não está no formato esperado.",
    );
  }
  assertContract(envelope.data);
  return envelope.data;
}
