import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/lmp";
import type { LmpNonconformityStreak } from "../types/lmpNonconformity";

const ENGINEERING_API_BASE = "/apps/engineering-api/v1";

type StreakEnvelope = {
  status?: string;
  data?: LmpNonconformityStreak;
};

/** Dias sem NC — owner NC via adapter governado
 * `GET /v1/lmps/nonconformities/streak` (delegação do Bearer humano).
 * A migração das operações de NC aguarda contrato oficial — este adapter
 * expõe somente o indicador read-only do dashboard. */
export async function fetchLmpNonconformityStreak(
  signal?: AbortSignal,
): Promise<LmpNonconformityStreak | null> {
  const response = await httpGet<ApiSuccessResponse<StreakEnvelope>>(
    `${ENGINEERING_API_BASE}/lmps/nonconformities/streak`,
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao carregar dias sem NC");
  if (data.status !== "available" || !data.data) return null;
  return data.data;
}
