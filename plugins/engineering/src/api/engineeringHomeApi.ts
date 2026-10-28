import { getJson, HomeApiError } from "./httpClient";
import type { HomeEnvelope, HomeResponse, HomeSections } from "../types/home";

const HOME_PATH = "/apps/engineering-api/v1/home";
const SECTION_KEYS = [
  "attention",
  "tasks",
  "lmps",
  "requests",
  "activity",
  "collaboration",
] as const;

function isValidSection(section: unknown): boolean {
  if (typeof section !== "object" || section === null) return false;
  const candidate = section as { status?: unknown; items?: unknown };
  return (
    typeof candidate.status === "string" &&
    (candidate.items === undefined || Array.isArray(candidate.items))
  );
}

function assertContract(data: HomeResponse): void {
  const sections = (data as { sections?: HomeSections }).sections;
  if (
    typeof data?.schema_version !== "string" ||
    typeof data?.status !== "string" ||
    !sections ||
    !SECTION_KEYS.every((key) => isValidSection(sections[key]))
  ) {
    throw new HomeApiError(
      "contract_error",
      "A resposta da Engineering API não está no formato esperado.",
    );
  }
}

/** `GET /apps/engineering-api/v1/home` — operationId get_engineering_home,
 * envelope canônico { success, message, data, meta }. */
export async function getEngineeringHome(
  signal?: AbortSignal,
): Promise<HomeResponse> {
  const envelope = await getJson<HomeEnvelope>(HOME_PATH, signal);
  if (!envelope || envelope.success !== true || !envelope.data) {
    throw new HomeApiError(
      "contract_error",
      "A resposta da Engineering API não está no formato esperado.",
    );
  }
  assertContract(envelope.data);
  return envelope.data;
}
