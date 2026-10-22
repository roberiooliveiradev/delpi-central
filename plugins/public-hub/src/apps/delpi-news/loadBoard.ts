import { DELPI_NEWS_DEMO_TOKEN, isDelpiNewsDemoEnabled, type DelpiNewsDemoEnv } from "./demoMode";
import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";
import type { PublicNewsBoard } from "./types";

export { DELPI_NEWS_DEMO_TOKEN };

/**
 * Carrega o board público da Etapa 1 (somente fixture de demonstração).
 *
 * Produção (bundle sem `VITE_DELPI_NEWS_DEMO=1`): sempre `null` → 404 do shell.
 * Futuro: token opaco revogável via `GET /apps/delpi-news-api/public/boards/{token}`.
 */
export async function loadPublicNewsBoard(
  token: string,
  env: DelpiNewsDemoEnv = import.meta.env,
): Promise<PublicNewsBoard | null> {
  if (!isDelpiNewsDemoEnabled(env)) {
    return null;
  }
  if (token !== DELPI_NEWS_DEMO_TOKEN) {
    return null;
  }
  return MOCK_PUBLIC_NEWS_BOARD;
}
