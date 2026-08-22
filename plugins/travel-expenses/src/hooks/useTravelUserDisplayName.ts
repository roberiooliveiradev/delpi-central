import { useMemo } from "react";

import { getAccessToken } from "../api/httpClient";
import { getDisplayNameFromToken } from "../utils/jwt";

export function useTravelUserDisplayName(fallback = "colaborador") {
  return useMemo(() => getDisplayNameFromToken(getAccessToken()) ?? fallback, [fallback]);
}
